"""Tests for FastAPI routes."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from prosim.api.server import app
from prosim.graph.serialization import graph_to_json

client = TestClient(app)


def _workflow_json(wf):
    return graph_to_json(wf)


def test_workflow_parse(linear_workflow):
    resp = client.post("/api/workflow/parse", json={"data": _workflow_json(linear_workflow)})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Linear Invoice"
    assert len(body["nodes"]) == 4


def test_workflow_parse_invalid():
    resp = client.post("/api/workflow/parse", json={"data": {"bad": "data"}})
    assert resp.status_code == 422


def test_simulate_deterministic(linear_workflow):
    resp = client.post("/api/simulate", json={
        "workflow": _workflow_json(linear_workflow),
        "mode": "deterministic",
        "num_transactions": 1000,
        "volume_per_hour": 100.0,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_transactions"] == 1000
    assert body["avg_total_time"] > 0
    assert body["avg_total_cost"] > 0
    assert len(body["bottlenecks"]) > 0


def test_simulate_monte_carlo(linear_workflow):
    resp = client.post("/api/simulate", json={
        "workflow": _workflow_json(linear_workflow),
        "mode": "monte_carlo",
        "num_transactions": 500,
        "volume_per_hour": 100.0,
        "seed": 42,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["p50_total_time"] > 0
    assert body["p95_total_time"] >= body["p50_total_time"]


def test_sensitivity(linear_workflow):
    resp = client.post("/api/sensitivity", json={
        "workflow": _workflow_json(linear_workflow),
        "volume_per_hour": 100.0,
        "num_transactions": 1000,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entries"]) > 0


def test_intervene(linear_workflow):
    # First get baseline results
    sim_resp = client.post("/api/simulate", json={
        "workflow": _workflow_json(linear_workflow),
        "mode": "deterministic",
        "num_transactions": 1000,
    })
    baseline = sim_resp.json()

    resp = client.post("/api/intervene", json={
        "workflow": _workflow_json(linear_workflow),
        "interventions": [{"node_id": "process", "time_reduction_pct": 30.0}],
        "baseline_results": baseline,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["time_saved_pct"] > 0


def test_leverage(linear_workflow):
    # First get sensitivity
    sens_resp = client.post("/api/sensitivity", json={
        "workflow": _workflow_json(linear_workflow),
    })
    sensitivity = sens_resp.json()

    resp = client.post("/api/leverage", json={
        "workflow": _workflow_json(linear_workflow),
        "sensitivity": sensitivity,
        "top_n": 3,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    assert "node_id" in body[0]


def test_export_mermaid(linear_workflow):
    resp = client.post("/api/export/mermaid", json={
        "workflow": _workflow_json(linear_workflow),
        "show_metrics": False,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "flowchart LR" in body["mermaid"]


def test_export_mermaid_with_results(linear_workflow):
    sim_resp = client.post("/api/simulate", json={
        "workflow": _workflow_json(linear_workflow),
        "mode": "deterministic",
        "num_transactions": 1000,
    })
    results = sim_resp.json()

    resp = client.post("/api/export/mermaid", json={
        "workflow": _workflow_json(linear_workflow),
        "results": results,
        "show_metrics": True,
    })
    assert resp.status_code == 200
    assert "flowchart LR" in resp.json()["mermaid"]


def test_history_endpoint():
    """GET /api/history returns stub with items and limit."""
    resp = client.get("/api/history")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["items"] == []
    assert body["limit"] == 30


def test_history_endpoint_with_limit():
    """GET /api/history?limit=10 accepts limit param."""
    resp = client.get("/api/history?limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 10


def test_workflow_generate_success(linear_workflow):
    """POST /api/workflow/generate returns 200 with valid mocked output."""
    raw_valid = {
        "name": "Generated",
        "description": "Test",
        "nodes": [
            {"id": "start", "name": "Start", "node_type": "start"},
            {"id": "step", "name": "Step", "node_type": "api"},
            {"id": "end", "name": "End", "node_type": "end"},
        ],
        "edges": [
            {"source": "start", "target": "step"},
            {"source": "step", "target": "end"},
        ],
    }

    with patch("prosim.parser.client.generate_workflow_raw", return_value=raw_valid):
        resp = client.post("/api/workflow/generate", json={"description": "test process"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Generated"
    assert len(body["nodes"]) == 3
    assert len(body["edges"]) == 2


def test_workflow_generate_invalid_output_returns_500():
    """POST /api/workflow/generate returns 500 when Claude returns invalid structure."""
    raw_invalid = {
        "name": "Bad",
        "nodes": [{"id": "a", "name": "A", "node_type": "api"}],  # no start/end, no edges
        "edges": [],
    }

    with patch("prosim.parser.client.generate_workflow_raw", return_value=raw_invalid):
        resp = client.post("/api/workflow/generate", json={"description": "test"})
    assert resp.status_code == 500
    assert "invalid" in resp.json()["detail"].lower()


def test_workflow_generate_missing_api_key():
    """POST /api/workflow/generate returns 500 when ANTHROPIC_API_KEY is missing."""
    with patch("prosim.parser.client.generate_workflow_raw") as mock:
        mock.side_effect = EnvironmentError("ANTHROPIC_API_KEY environment variable is required")
        resp = client.post("/api/workflow/generate", json={"description": "test"})
    assert resp.status_code == 500
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]
