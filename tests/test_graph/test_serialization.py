"""Tests for graph serialization."""

import json
import tempfile
from pathlib import Path

from prosim.graph.models import Edge, Node, NodeType, WorkflowGraph
from prosim.graph.serialization import graph_from_json, graph_to_json, load_graph, save_graph


def _make_workflow() -> WorkflowGraph:
    return WorkflowGraph(
        name="Test Workflow",
        description="A test workflow",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START),
            Node(id="process", name="Process", node_type=NodeType.HUMAN),
            Node(id="end", name="End", node_type=NodeType.END),
        ],
        edges=[
            Edge(source="start", target="process"),
            Edge(source="process", target="end"),
        ],
    )


def test_graph_to_json():
    wf = _make_workflow()
    data = graph_to_json(wf)
    assert data["name"] == "Test Workflow"
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2


def test_graph_from_json():
    wf = _make_workflow()
    data = graph_to_json(wf)
    restored = graph_from_json(data)
    assert restored.name == wf.name
    assert len(restored.nodes) == len(wf.nodes)
    assert len(restored.edges) == len(wf.edges)


def test_roundtrip():
    wf = _make_workflow()
    data = graph_to_json(wf)
    restored = graph_from_json(data)
    data2 = graph_to_json(restored)
    assert data == data2


def test_save_load():
    wf = _make_workflow()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        save_graph(wf, path)
        assert path.exists()

        loaded = load_graph(path)
        assert loaded.name == wf.name
        assert len(loaded.nodes) == len(wf.nodes)


def test_save_creates_directories():
    wf = _make_workflow()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "sub" / "dir" / "test.json"
        save_graph(wf, path)
        assert path.exists()
