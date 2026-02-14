"""Tests for postprocess_raw_workflow: empty edges, orphaned nodes, repair, strict mode."""

import pytest

from prosim.graph.models import NodeType, WorkflowGraph
from prosim.graph.operations import validate_graph
from prosim.parser.postprocess import postprocess_raw_workflow


def _raw_linear_nodes():
    """Minimal valid raw nodes: start, process, end."""
    return [
        {"id": "start", "name": "Start", "node_type": "start"},
        {"id": "validate", "name": "Validate", "node_type": "api"},
        {"id": "end", "name": "End", "node_type": "end"},
    ]


def test_postprocess_valid_workflow():
    """Valid output passes through unchanged."""
    raw = {
        "name": "Test",
        "description": "A test",
        "nodes": _raw_linear_nodes(),
        "edges": [
            {"source": "start", "target": "validate"},
            {"source": "validate", "target": "end"},
        ],
    }
    wf = postprocess_raw_workflow(raw)
    assert isinstance(wf, WorkflowGraph)
    assert wf.name == "Test"
    assert len(wf.nodes) == 3
    assert len(wf.edges) == 2
    issues = validate_graph(wf)
    assert len(issues) == 0


def test_postprocess_empty_edges_infers_linear_chain():
    """Raw output with nodes but empty edges infers linear chain."""
    raw = {
        "name": "Inferred",
        "description": "",
        "nodes": _raw_linear_nodes(),
        "edges": [],
    }
    wf = postprocess_raw_workflow(raw)
    assert len(wf.edges) == 2  # start->validate, validate->end
    assert wf.edges[0].source == "start" and wf.edges[0].target == "validate"
    assert wf.edges[1].source == "validate" and wf.edges[1].target == "end"
    issues = validate_graph(wf)
    assert len(issues) == 0


def test_postprocess_orphaned_nodes_repaired_by_empty_edges():
    """Orphaned nodes (no edges) get repaired when edges are empty via linear inference."""
    raw = {
        "name": "Orphaned",
        "description": "",
        "nodes": _raw_linear_nodes(),
        "edges": [],
    }
    wf = postprocess_raw_workflow(raw)
    # Linear chain inference connects all nodes
    assert len(wf.edges) >= 1
    issues = validate_graph(wf)
    assert not any("orphaned" in i.lower() for i in issues)


def test_postprocess_edge_repair_fuzzy_match():
    """Edges with mismatched IDs (hyphen vs underscore) get repaired."""
    raw = {
        "name": "Repair",
        "description": "",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {"id": "invoice_capture", "name": "Capture", "node_type": "api"},
            {"id": "end", "name": "End", "node_type": "end"},
        ],
        "edges": [
            {"source": "start", "target": "invoice-capture"},  # hyphen vs underscore
            {"source": "invoice-capture", "target": "end"},
        ],
    }
    wf = postprocess_raw_workflow(raw)
    assert len(wf.edges) == 2
    assert wf.edges[0].source == "start" and wf.edges[0].target == "invoice_capture"
    assert wf.edges[1].source == "invoice_capture" and wf.edges[1].target == "end"
    issues = validate_graph(wf)
    assert len(issues) == 0


def test_postprocess_all_invalid_edges_fallback_to_linear():
    """When all edges have invalid refs, fall back to linear chain."""
    raw = {
        "name": "Fallback",
        "description": "",
        "nodes": _raw_linear_nodes(),
        "edges": [
            {"source": "nonexistent_a", "target": "nonexistent_b"},
        ],
    }
    wf = postprocess_raw_workflow(raw)
    # Repair yields 0 valid edges, then fallback to linear chain
    assert len(wf.edges) == 2
    issues = validate_graph(wf)
    assert len(issues) == 0


def test_postprocess_strict_raises_on_orphaned():
    """Strict mode raises when graph has orphaned nodes that cannot be repaired."""
    # No start/end - repair can't infer linear chain
    raw = {
        "name": "Bad",
        "description": "",
        "nodes": [
            {"id": "a", "name": "A", "node_type": "api"},
            {"id": "b", "name": "B", "node_type": "api"},
        ],
        "edges": [],  # empty, no start/end to infer from
    }
    with pytest.raises(ValueError) as exc_info:
        postprocess_raw_workflow(raw, strict=True)
    assert "invalid graph" in str(exc_info.value).lower() or "orphaned" in str(exc_info.value).lower()


def test_postprocess_strict_passes_when_valid():
    """Strict mode passes when graph is valid."""
    raw = {
        "name": "OK",
        "description": "",
        "nodes": _raw_linear_nodes(),
        "edges": [
            {"source": "start", "target": "validate"},
            {"source": "validate", "target": "end"},
        ],
    }
    wf = postprocess_raw_workflow(raw, strict=True)
    assert wf is not None
    assert len(validate_graph(wf)) == 0


def test_postprocess_strict_raises_on_no_start():
    """Strict mode raises when there is no start node."""
    raw = {
        "name": "NoStart",
        "description": "",
        "nodes": [
            {"id": "only", "name": "Only", "node_type": "end"},
        ],
        "edges": [],
    }
    with pytest.raises(ValueError):
        postprocess_raw_workflow(raw, strict=True)


def test_postprocess_connectivity_repair_start_end_split():
    """When start and end are in different components, connect them."""
    raw = {
        "name": "Split",
        "description": "",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {"id": "a", "name": "A", "node_type": "api"},
            {"id": "orphan", "name": "Orphan", "node_type": "api"},
            {"id": "end", "name": "End", "node_type": "end"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            # a and orphan disconnected; end isolated
        ],
    }
    wf = postprocess_raw_workflow(raw, strict=True)
    issues = validate_graph(wf)
    assert not any("not weakly connected" in i.lower() for i in issues)


def test_postprocess_connectivity_repair():
    """Disconnected components get connected to main flow."""
    raw = {
        "name": "Disconnected",
        "description": "",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {"id": "a", "name": "A", "node_type": "api"},
            {"id": "end", "name": "End", "node_type": "end"},
            {"id": "orphan", "name": "Orphan", "node_type": "api"},
        ],
        "edges": [
            {"source": "start", "target": "a"},
            {"source": "a", "target": "end"},
            # orphan has no edges - disconnected component
        ],
    }
    wf = postprocess_raw_workflow(raw, strict=True)
    assert len(wf.edges) >= 3  # original 2 + repair adds a -> orphan, orphan -> end
    issues = validate_graph(wf)
    assert not any("not weakly connected" in i.lower() for i in issues)


def test_postprocess_non_strict_logs_warnings():
    """Non-strict mode logs warnings but returns workflow."""
    raw = {
        "name": "Warn",
        "description": "",
        "nodes": [
            {"id": "a", "name": "A", "node_type": "api"},
            {"id": "b", "name": "B", "node_type": "api"},
        ],
        "edges": [],
    }
    # No start/end - repair can't infer. Strict would raise; non-strict returns with issues
    wf = postprocess_raw_workflow(raw, strict=False)
    assert wf is not None
    assert len(wf.edges) == 0  # no repair possible
    issues = validate_graph(wf)
    assert any("no start" in i.lower() or "orphaned" in i.lower() for i in issues)
