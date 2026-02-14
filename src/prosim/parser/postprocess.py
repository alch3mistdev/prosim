"""Post-process and validate raw Claude output into a WorkflowGraph."""

from __future__ import annotations

from prosim.graph.models import (
    Edge,
    EdgeType,
    Node,
    NodeParams,
    NodeType,
    WorkflowGraph,
)
from prosim.graph.operations import normalize_decision_probabilities, validate_graph


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
