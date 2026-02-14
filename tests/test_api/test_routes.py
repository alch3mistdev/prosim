"""Tests for FastAPI routes."""

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
