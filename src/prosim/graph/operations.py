"""Graph construction, validation, and operations using NetworkX."""

from __future__ import annotations

import networkx as nx

from prosim.graph.models import EdgeType, NodeType, WorkflowGraph


def build_nx_graph(workflow: WorkflowGraph) -> nx.DiGraph:
    """Build a NetworkX DiGraph from a WorkflowGraph model.

    Transfers all node parameters and edge attributes to the NetworkX graph
    for use in simulation algorithms.
    """
    G = nx.DiGraph()

    for node in workflow.nodes:
        G.add_node(
            node.id,
            name=node.name,
            node_type=node.node_type,
            description=node.description,
            params=node.params,
        )

    for edge in workflow.edges:
        G.add_edge(
            edge.source,
            edge.target,
            edge_type=edge.edge_type,
            probability=edge.probability,
            condition=edge.condition,
        )

    return G


def validate_graph(workflow: WorkflowGraph) -> list[str]:
    """Validate a workflow graph and return a list of issues.

    Checks:
    - At least one start and one end node
    - All edge endpoints reference existing nodes
    - No orphaned nodes (except start/end)
    - Decision node branch probabilities sum to ~1.0
    - No self-loops on non-loop edges
    - Graph is weakly connected
    """
    issues: list[str] = []
    node_ids = workflow.node_ids

    # Check start/end nodes
    start_nodes = workflow.get_start_nodes()
    end_nodes = workflow.get_end_nodes()
    if not start_nodes:
        issues.append("Graph has no start node")
    if not end_nodes:
        issues.append("Graph has no end node")

    # Check edge endpoint validity
    for edge in workflow.edges:
        if edge.source not in node_ids:
            issues.append(f"Edge source '{edge.source}' not found in nodes")
        if edge.target not in node_ids:
            issues.append(f"Edge target '{edge.target}' not found in nodes")

    # Check for orphaned nodes
    connected = set()
    for edge in workflow.edges:
        connected.add(edge.source)
        connected.add(edge.target)
    for node in workflow.nodes:
        if node.id not in connected and node.node_type not in (NodeType.START, NodeType.END):
            # Start/end with no edges are caught by other checks
            if len(workflow.nodes) > 1:
                issues.append(f"Node '{node.id}' is orphaned (no edges)")

    # Check decision probability normalization
    for node in workflow.get_decision_nodes():
        outgoing = workflow.get_outgoing_edges(node.id)
        if outgoing:
            total_prob = sum(e.probability for e in outgoing)
            if abs(total_prob - 1.0) > 0.01:
                issues.append(
                    f"Decision node '{node.id}' outgoing probabilities sum to {total_prob:.3f}, expected 1.0"
                )

    # Check self-loops
    for edge in workflow.edges:
        if edge.source == edge.target and edge.edge_type != EdgeType.LOOP:
            issues.append(f"Self-loop on '{edge.source}' without LOOP edge type")

    # Check weak connectivity
    G = build_nx_graph(workflow)
    if len(workflow.nodes) > 1 and not nx.is_weakly_connected(G):
        issues.append("Graph is not weakly connected")

    return issues


def normalize_decision_probabilities(workflow: WorkflowGraph) -> WorkflowGraph:
    """Normalize outgoing edge probabilities for all decision nodes to sum to 1.0.

    Modifies edges in-place and returns the workflow for chaining.
    """
    for node in workflow.get_decision_nodes():
        outgoing = workflow.get_outgoing_edges(node.id)
        if not outgoing:
            continue

        total = sum(e.probability for e in outgoing)
        if total <= 0:
            # Equal distribution
            equal_prob = 1.0 / len(outgoing)
            for edge in outgoing:
                edge.probability = equal_prob
        elif abs(total - 1.0) > 0.001:
            for edge in outgoing:
                edge.probability = edge.probability / total

    return workflow


def topological_execution_order(workflow: WorkflowGraph) -> list[str]:
    """Get topological execution order for graph traversal.

    For DAGs, returns a valid topological sort. For graphs with cycles,
    breaks cycles at loop edges and returns approximate order.
    """
    G = build_nx_graph(workflow)

    # Remove loop edges to break cycles for topological sort
    loop_edges = [
        (e.source, e.target)
        for e in workflow.edges
        if e.edge_type == EdgeType.LOOP
    ]
    G_acyclic = G.copy()
    G_acyclic.remove_edges_from(loop_edges)

    # If still cyclic after removing loop edges, break remaining cycles
    while not nx.is_directed_acyclic_graph(G_acyclic):
        try:
            cycle = nx.find_cycle(G_acyclic)
            # Remove the last edge in the cycle (heuristic: most likely a back-edge)
            G_acyclic.remove_edge(*cycle[-1][:2])
        except nx.NetworkXNoCycle:
            break

    return list(nx.topological_sort(G_acyclic))


def get_all_paths(workflow: WorkflowGraph) -> list[list[str]]:
    """Get all simple paths from start to end nodes."""
    G = build_nx_graph(workflow)
    paths = []
    for start in workflow.get_start_nodes():
        for end in workflow.get_end_nodes():
            for path in nx.all_simple_paths(G, start.id, end.id):
                paths.append(path)
    return paths
