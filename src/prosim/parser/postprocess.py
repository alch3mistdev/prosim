"""Post-process and validate raw Claude output into a WorkflowGraph."""

from __future__ import annotations

import networkx as nx

from prosim.graph.models import (
    Edge,
    EdgeType,
    Node,
    NodeParams,
    NodeType,
    WorkflowGraph,
)
from prosim.graph.operations import build_nx_graph, normalize_decision_probabilities, validate_graph


def _normalize_id_for_match(s: str) -> str:
    """Normalize ID for fuzzy matching (lowercase, hyphens/underscores)."""
    return s.strip().lower().replace("-", "_")


def _find_matching_node_id(candidate: str, node_ids: set[str]) -> str | None:
    """Find a node ID that matches candidate, with fuzzy matching for common mismatches."""
    if candidate in node_ids:
        return candidate
    norm_candidate = _normalize_id_for_match(candidate)
    for nid in node_ids:
        if _normalize_id_for_match(nid) == norm_candidate:
            return nid
    return None


def _infer_linear_chain(
    start_nodes: list[Node],
    end_nodes: list[Node],
    process_nodes: list[Node],
) -> list[Edge]:
    """Infer a linear chain: start -> process_1 -> ... -> process_n -> end."""
    edges = []
    prev = start_nodes[0].id
    for node in process_nodes:
        edges.append(
            Edge(source=prev, target=node.id, edge_type=EdgeType.NORMAL, probability=1.0)
        )
        prev = node.id
    edges.append(
        Edge(source=prev, target=end_nodes[0].id, edge_type=EdgeType.NORMAL, probability=1.0)
    )
    return edges


def _repair_edges(nodes: list[Node], raw_edges: list[dict]) -> list[Edge]:
    """Repair edges: fix invalid source/target references, infer linear chain if empty."""
    node_ids = {n.id for n in nodes}
    start_nodes = [n for n in nodes if n.node_type == NodeType.START]
    end_nodes = [n for n in nodes if n.node_type == NodeType.END]
    process_nodes = [
        n for n in nodes
        if n.node_type not in (NodeType.START, NodeType.END)
    ]

    # If edges empty but we have start/end and process nodes, infer linear chain
    if not raw_edges and start_nodes and end_nodes:
        return _infer_linear_chain(start_nodes, end_nodes, process_nodes)

    # Repair edges with invalid source/target
    repaired = []
    for raw_edge in raw_edges:
        src = raw_edge.get("source", "")
        tgt = raw_edge.get("target", "")
        if not src or not tgt:
            continue
        fixed_src = _find_matching_node_id(src, node_ids) or src
        fixed_tgt = _find_matching_node_id(tgt, node_ids) or tgt
        if fixed_src in node_ids and fixed_tgt in node_ids:
            repaired.append(
                Edge(
                    source=fixed_src,
                    target=fixed_tgt,
                    edge_type=EdgeType(raw_edge.get("edge_type", "normal")),
                    probability=raw_edge.get("probability", 1.0),
                    condition=raw_edge.get("condition", ""),
                )
            )

    # Fallback: if repair yielded no valid edges, infer linear chain
    if not repaired and start_nodes and end_nodes:
        return _infer_linear_chain(start_nodes, end_nodes, process_nodes)

    return repaired


def _repair_connectivity(workflow: WorkflowGraph) -> WorkflowGraph:
    """Connect disjoint components so the graph becomes weakly connected.

    When Claude returns multiple disconnected subgraphs, connect orphan components
    to the main flow (the one containing start and end) by inserting them
    linearly before the end node.
    """
    G = build_nx_graph(workflow)
    if nx.is_weakly_connected(G):
        return workflow

    components = list(nx.weakly_connected_components(G))
    start_ids = {n.id for n in workflow.get_start_nodes()}
    end_ids = {n.id for n in workflow.get_end_nodes()}

    # Find main component (has start and end) and orphans
    main_component = None
    orphan_components = []
    start_component = None
    end_component = None
    for comp in components:
        has_start = bool(start_ids & comp)
        has_end = bool(end_ids & comp)
        if has_start and has_end:
            main_component = comp
        elif has_start:
            start_component = comp
        elif has_end:
            end_component = comp
        else:
            orphan_components.append(comp)

    # If start and end are in different components, connect them via orphans
    if not main_component and start_component and end_component:
        # Chain: start_comp -> orphans -> end_comp
        start_node = next(iter(start_ids & start_component))
        end_node = next(iter(end_ids & end_component))
        start_G = G.subgraph(start_component)
        end_G = G.subgraph(end_component)
        start_exits = [n for n in start_component if start_G.out_degree(n) == 0]
        start_last = start_exits[0] if start_exits else next(iter(start_component))
        end_entries = [n for n in end_component if end_G.in_degree(n) == 0]
        end_first = end_entries[0] if end_entries else next(iter(end_component))
        new_edges = list(workflow.edges)
        # Connect start_component's exit to first orphan or end_component
        if orphan_components:
            prev = start_last
            for i, o in enumerate(orphan_components):
                o_G = G.subgraph(o)
                o_first = next((n for n in o if o_G.in_degree(n) == 0), next(iter(o)))
                o_last = next((n for n in o if o_G.out_degree(n) == 0), next(iter(o)))
                new_edges.append(Edge(source=prev, target=o_first, edge_type=EdgeType.NORMAL, probability=1.0))
                prev = o_last
            new_edges.append(Edge(source=prev, target=end_first, edge_type=EdgeType.NORMAL, probability=1.0))
        else:
            new_edges.append(Edge(source=start_last, target=end_first, edge_type=EdgeType.NORMAL, probability=1.0))
        return WorkflowGraph(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=new_edges,
        )

    if not main_component or not orphan_components:
        return workflow

    # Get nodes that feed into end in the main component
    end_node = next(iter(end_ids & main_component), None)
    if not end_node:
        return workflow

    nodes_into_end = [e.source for e in workflow.edges if e.target == end_node]
    # Prefer a non-start node; otherwise use start
    bridge_from = next(
        (n for n in nodes_into_end if n in main_component and n not in start_ids),
        next(iter(start_ids & main_component), None),
    )
    if not bridge_from:
        return workflow

    # Remove the edge bridge_from -> end_node; we'll replace it with a chain through orphans
    new_edges = [
        e for e in workflow.edges
        if not (e.source == bridge_from and e.target == end_node)
    ]

    # Chain orphans: bridge_from -> o1_first -> ... -> o1_last -> o2_first -> ... -> o2_last -> end
    for i, orphan in enumerate(orphan_components):
        orphan_G = G.subgraph(orphan)
        in_degree = orphan_G.in_degree()
        out_degree = orphan_G.out_degree()
        entries = [n for n in orphan if in_degree[n] == 0]
        exits = [n for n in orphan if out_degree[n] == 0]
        first_node = entries[0] if entries else next(iter(orphan))
        last_node = exits[0] if exits else next(iter(orphan))

        new_edges.append(Edge(source=bridge_from, target=first_node, edge_type=EdgeType.NORMAL, probability=1.0))
        if i == len(orphan_components) - 1:
            new_edges.append(Edge(source=last_node, target=end_node, edge_type=EdgeType.NORMAL, probability=1.0))
        else:
            next_orphan = orphan_components[i + 1]
            next_G = G.subgraph(next_orphan)
            next_entries = [n for n in next_orphan if next_G.in_degree(n) == 0]
            next_first = next_entries[0] if next_entries else next(iter(next_orphan))
            new_edges.append(Edge(source=last_node, target=next_first, edge_type=EdgeType.NORMAL, probability=1.0))
        bridge_from = last_node

    return WorkflowGraph(
        name=workflow.name,
        description=workflow.description,
        nodes=workflow.nodes,
        edges=new_edges,
    )


def postprocess_raw_workflow(raw: dict, strict: bool = False) -> WorkflowGraph:
    """Convert raw Claude API output into a validated WorkflowGraph.

    Handles:
    - Mapping raw node dicts to Node models with NodeParams
    - Mapping raw edge dicts to Edge models (with repair for invalid refs)
    - Inferring linear chain when edges are empty
    - Applying defaults for missing parameters
    - Normalizing decision probabilities
    - Validating graph structure

    Args:
        raw: Raw dict from Claude API tool_use output.
        strict: If True, raise ValueError on critical validation issues.
    """
    nodes = []
    for raw_node in raw.get("nodes", []):
        params = NodeParams(
            exec_time_mean=raw_node.get("exec_time_mean", _default_time(raw_node.get("node_type", "api"))),
            exec_time_variance=raw_node.get("exec_time_variance", 0.1),
            cost_per_transaction=raw_node.get("cost_per_transaction", 0.0),
            error_rate=raw_node.get("error_rate", 0.0),
            drop_off_rate=raw_node.get("drop_off_rate", 0.0),
            queue_delay_mean=raw_node.get("queue_delay_mean", 0.0),
            capacity_per_hour=raw_node.get("capacity_per_hour"),
            max_retries=raw_node.get("max_retries", 0),
            retry_delay=raw_node.get("retry_delay", 0.0),
            parallelization_factor=raw_node.get("parallelization_factor", 1),
        )

        node = Node(
            id=raw_node["id"],
            name=raw_node["name"],
            node_type=NodeType(raw_node["node_type"]),
            description=raw_node.get("description", ""),
            params=params,
        )
        nodes.append(node)

    raw_edges = raw.get("edges", [])
    edges = _repair_edges(nodes, raw_edges)

    workflow = WorkflowGraph(
        name=raw.get("name", "Unnamed Workflow"),
        description=raw.get("description", ""),
        nodes=nodes,
        edges=edges,
    )

    # Normalize decision probabilities
    workflow = normalize_decision_probabilities(workflow)

    # Repair disconnected components
    workflow = _repair_connectivity(workflow)

    # Validate
    issues = validate_graph(workflow)
    if issues:
        for issue in issues:
            print(f"[ProSim Warning] {issue}")
        if strict:
            critical = [
                i for i in issues
                if "no start node" in i.lower()
                or "no end node" in i.lower()
                or "orphaned" in i.lower()
                or "not weakly connected" in i.lower()
            ]
            if critical:
                raise ValueError(
                    "Workflow generation produced invalid graph: " + "; ".join(critical)
                )

    return workflow


def _default_time(node_type: str) -> float:
    """Return sensible default execution time for a node type."""
    defaults = {
        "start": 0.0,
        "end": 0.0,
        "human": 300.0,
        "api": 1.0,
        "async": 5.0,
        "batch": 60.0,
        "decision": 0.1,
        "parallel_gateway": 0.0,
        "wait": 30.0,
    }
    return defaults.get(node_type, 1.0)
