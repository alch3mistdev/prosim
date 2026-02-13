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


def postprocess_raw_workflow(raw: dict) -> WorkflowGraph:
    """Convert raw Claude API output into a validated WorkflowGraph.

    Handles:
    - Mapping raw node dicts to Node models with NodeParams
    - Mapping raw edge dicts to Edge models
    - Applying defaults for missing parameters
    - Normalizing decision probabilities
    - Validating graph structure
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

    edges = []
    for raw_edge in raw.get("edges", []):
        edge = Edge(
            source=raw_edge["source"],
            target=raw_edge["target"],
            edge_type=EdgeType(raw_edge.get("edge_type", "normal")),
            probability=raw_edge.get("probability", 1.0),
            condition=raw_edge.get("condition", ""),
        )
        edges.append(edge)

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
        # Log issues but don't fail — best-effort generation
        for issue in issues:
            print(f"[ProSim Warning] {issue}")

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
