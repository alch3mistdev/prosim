"""Tests for graph operations."""

import networkx as nx
import pytest

from prosim.graph.models import (
    Edge,
    EdgeType,
    Node,
    NodeParams,
    NodeType,
    WorkflowGraph,
)
from prosim.graph.operations import (
    build_nx_graph,
    get_all_paths,
    normalize_decision_probabilities,
    topological_execution_order,
    validate_graph,
)


def _make_linear_workflow() -> WorkflowGraph:
    """Create a simple linear workflow: start -> process -> end."""
    return WorkflowGraph(
        name="Linear",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="process", name="Process", node_type=NodeType.HUMAN, params=NodeParams(exec_time_mean=10.0)),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="start", target="process"),
            Edge(source="process", target="end"),
        ],
    )


def _make_branching_workflow() -> WorkflowGraph:
    """Create a workflow with a decision node."""
    return WorkflowGraph(
        name="Branching",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="decide", name="Approve?", node_type=NodeType.DECISION),
            Node(id="approve", name="Approved", node_type=NodeType.HUMAN),
            Node(id="reject", name="Rejected", node_type=NodeType.HUMAN),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="start", target="decide"),
            Edge(source="decide", target="approve", probability=0.7, edge_type=EdgeType.CONDITIONAL, condition="Yes"),
            Edge(source="decide", target="reject", probability=0.3, edge_type=EdgeType.CONDITIONAL, condition="No"),
            Edge(source="approve", target="end"),
            Edge(source="reject", target="end"),
        ],
    )


def test_build_nx_graph():
    wf = _make_linear_workflow()
    G = build_nx_graph(wf)
    assert isinstance(G, nx.DiGraph)
    assert len(G.nodes) == 3
    assert len(G.edges) == 2
    assert G.nodes["process"]["params"].exec_time_mean == 10.0


def test_validate_graph_valid():
    wf = _make_linear_workflow()
    issues = validate_graph(wf)
    assert len(issues) == 0


def test_validate_graph_no_start():
    wf = WorkflowGraph(
        name="No Start",
        nodes=[
            Node(id="a", name="A", node_type=NodeType.HUMAN),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[Edge(source="a", target="end")],
    )
    issues = validate_graph(wf)
    assert any("no start" in i.lower() for i in issues)


def test_validate_graph_no_end():
    wf = WorkflowGraph(
        name="No End",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="a", name="A", node_type=NodeType.HUMAN),
        ],
        edges=[Edge(source="start", target="a")],
    )
    issues = validate_graph(wf)
    assert any("no end" in i.lower() for i in issues)


def test_validate_graph_bad_edge():
    wf = WorkflowGraph(
        name="Bad Edge",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[Edge(source="start", target="nonexistent")],
    )
    issues = validate_graph(wf)
    assert any("nonexistent" in i for i in issues)


def test_validate_decision_probabilities():
    wf = WorkflowGraph(
        name="Bad Probs",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="d", name="Decide", node_type=NodeType.DECISION),
            Node(id="a", name="A", node_type=NodeType.HUMAN),
            Node(id="b", name="B", node_type=NodeType.HUMAN),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="start", target="d"),
            Edge(source="d", target="a", probability=0.5),
            Edge(source="d", target="b", probability=0.3),
            Edge(source="a", target="end"),
            Edge(source="b", target="end"),
        ],
    )
    issues = validate_graph(wf)
    assert any("probabilities sum" in i for i in issues)


def test_normalize_decision_probabilities():
    wf = WorkflowGraph(
        name="Normalize",
        nodes=[
            Node(id="d", name="Decide", node_type=NodeType.DECISION),
            Node(id="a", name="A", node_type=NodeType.HUMAN),
            Node(id="b", name="B", node_type=NodeType.HUMAN),
        ],
        edges=[
            Edge(source="d", target="a", probability=0.4),
            Edge(source="d", target="b", probability=0.4),
        ],
    )
    # Probabilities sum to 0.8, should be normalized to 1.0
    wf = normalize_decision_probabilities(wf)

    edges = wf.get_outgoing_edges("d")
    total = sum(e.probability for e in edges)
    assert abs(total - 1.0) < 0.001
    assert abs(edges[0].probability - 0.5) < 0.001
    assert abs(edges[1].probability - 0.5) < 0.001


def test_topological_order():
    wf = _make_linear_workflow()
    order = topological_execution_order(wf)
    assert order.index("start") < order.index("process")
    assert order.index("process") < order.index("end")


def test_topological_order_branching():
    wf = _make_branching_workflow()
    order = topological_execution_order(wf)
    assert order.index("start") < order.index("decide")
    assert order.index("decide") < order.index("approve")
    assert order.index("decide") < order.index("reject")


def test_get_all_paths():
    wf = _make_branching_workflow()
    paths = get_all_paths(wf)
    assert len(paths) == 2
    path_sets = [set(p) for p in paths]
    assert {"start", "decide", "approve", "end"} in path_sets
    assert {"start", "decide", "reject", "end"} in path_sets
