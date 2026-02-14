"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from prosim.cli.main import cli
from prosim.graph.models import Edge, Node, NodeParams, NodeType, WorkflowGraph
from prosim.graph.serialization import save_graph


def _create_test_workflow(tmpdir: str) -> str:
    """Create a test workflow file and return its path."""
    wf = WorkflowGraph(
        name="Test CLI Workflow",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START, params=NodeParams(exec_time_mean=0.0)),
            Node(
                id="process",
                name="Process",
                node_type=NodeType.API,
                params=NodeParams(exec_time_mean=5.0, cost_per_transaction=0.05),
            ),
            Node(id="end", name="End", node_type=NodeType.END, params=NodeParams(exec_time_mean=0.0)),
        ],
        edges=[
            Edge(source="start", target="process"),
            Edge(source="process", target="end"),
        ],
    )
    path = Path(tmpdir) / "workflow.json"
    save_graph(wf, path)
    return str(path)


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_simulate_deterministic():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(cli, ["simulate", wf_path, "--mode", "deterministic", "-n", "100"])
        assert result.exit_code == 0


def test_simulate_monte_carlo():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(cli, ["simulate", wf_path, "--mode", "monte_carlo", "-n", "500", "--seed", "42"])
        assert result.exit_code == 0


def test_simulate_with_output():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        out_path = str(Path(tmpdir) / "results.json")
        result = runner.invoke(cli, ["simulate", wf_path, "-n", "100", "-o", out_path])
        assert result.exit_code == 0
        assert Path(out_path).exists()

        with open(out_path) as f:
            data = json.load(f)
        assert "workflow" in data
        assert "simulation_results" in data


def test_intervene():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(
            cli,
            ["intervene", wf_path, "--node", "process", "--time-reduction", "50"],
        )
        assert result.exit_code == 0


def test_intervene_invalid_node():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(
            cli,
            ["intervene", wf_path, "--node", "nonexistent", "--time-reduction", "50"],
        )
        assert result.exit_code != 0


def test_export_mermaid():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(cli, ["export", wf_path, "-f", "mermaid"])
        assert result.exit_code == 0
        assert "flowchart LR" in result.output


def test_export_json():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        result = runner.invoke(cli, ["export", wf_path, "-f", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "workflow" in data


def test_export_to_file():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        wf_path = _create_test_workflow(tmpdir)
        out_path = str(Path(tmpdir) / "diagram.mmd")
        result = runner.invoke(cli, ["export", wf_path, "-f", "mermaid", "-o", out_path])
        assert result.exit_code == 0
        assert Path(out_path).exists()
