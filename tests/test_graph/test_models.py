"""Tests for graph data models."""

import pytest
from pydantic import ValidationError

from prosim.graph.models import (
    Edge,
    EdgeType,
    Node,
    NodeParams,
    NodeType,
    WorkflowGraph,
)


def test_node_params_defaults():
    p = NodeParams()
    assert p.exec_time_mean == 1.0
    assert p.exec_time_variance == 0.1
    assert p.error_rate == 0.0
    assert p.parallelization_factor == 1
    assert p.capacity_per_hour is None


def test_node_params_validation():
    with pytest.raises(ValidationError):
        NodeParams(error_rate=1.5)
    with pytest.raises(ValidationError):
        NodeParams(exec_time_mean=-1.0)


def test_node_creation():
    n = Node(id="step_1", name="Step 1", node_type=NodeType.HUMAN)
    assert n.id == "step_1"
    assert n.node_type == NodeType.HUMAN
    assert n.params.exec_time_mean == 1.0


def test_node_id_validation():
    with pytest.raises(ValidationError):
        Node(id="", name="Empty", node_type=NodeType.API)
    with pytest.raises(ValidationError):
        Node(id="   ", name="Whitespace", node_type=NodeType.API)


def test_edge_creation():
    e = Edge(source="a", target="b")
    assert e.edge_type == EdgeType.NORMAL
    assert e.probability == 1.0


def test_edge_probability_validation():
    with pytest.raises(ValidationError):
        Edge(source="a", target="b", probability=1.5)
    with pytest.raises(ValidationError):
        Edge(source="a", target="b", probability=-0.1)


def test_workflow_graph_basic():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="start", target="end"),
        ],
    )
    assert wf.name == "Test"
    assert len(wf.nodes) == 2
    assert len(wf.edges) == 1


def test_workflow_get_node():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="s", name="Start", node_type=NodeType.START),
        ],
        edges=[],
    )
    assert wf.get_node("s") is not None
    assert wf.get_node("nonexistent") is None


def test_workflow_get_start_end_nodes():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="s", name="Start", node_type=NodeType.START),
            Node(id="m", name="Middle", node_type=NodeType.HUMAN),
            Node(id="e", name="End", node_type=NodeType.END),
        ],
        edges=[],
    )
    assert len(wf.get_start_nodes()) == 1
    assert len(wf.get_end_nodes()) == 1
    assert wf.get_start_nodes()[0].id == "s"


def test_workflow_get_outgoing_edges():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="a", name="A", node_type=NodeType.START),
            Node(id="b", name="B", node_type=NodeType.HUMAN),
            Node(id="c", name="C", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="a", target="b"),
            Edge(source="a", target="c"),
            Edge(source="b", target="c"),
        ],
    )
    assert len(wf.get_outgoing_edges("a")) == 2
    assert len(wf.get_outgoing_edges("b")) == 1
    assert len(wf.get_outgoing_edges("c")) == 0


def test_workflow_node_ids():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="a", name="A", node_type=NodeType.START),
            Node(id="b", name="B", node_type=NodeType.END),
        ],
        edges=[],
    )
    assert wf.node_ids == {"a", "b"}


def test_workflow_decision_nodes():
    wf = WorkflowGraph(
        name="Test",
        nodes=[
            Node(id="d", name="Decision", node_type=NodeType.DECISION),
            Node(id="h", name="Human", node_type=NodeType.HUMAN),
        ],
        edges=[],
    )
    assert len(wf.get_decision_nodes()) == 1
    assert wf.get_decision_nodes()[0].id == "d"
