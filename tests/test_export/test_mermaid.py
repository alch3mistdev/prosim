"""Tests for Mermaid diagram generation."""

from prosim.export.mermaid import generate_mermaid
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig


def test_mermaid_basic(linear_workflow):
    mermaid = generate_mermaid(linear_workflow)
    assert mermaid.startswith("graph LR")
    assert "Start" in mermaid
    assert "End" in mermaid
    assert "Validate Invoice" in mermaid
    assert "-->" in mermaid


def test_mermaid_decision_nodes(branching_workflow):
    mermaid = generate_mermaid(branching_workflow)
    assert "Approved" in mermaid or "70%" in mermaid
    assert "{" in mermaid  # Diamond shape for decision


def test_mermaid_with_metrics(linear_workflow):
    config = SimulationConfig(num_transactions=100)
    results = run_deterministic(linear_workflow, config)
    mermaid = generate_mermaid(linear_workflow, results=results, show_metrics=True)

    # Should contain time/cost annotations
    assert "s |" in mermaid or "s\\n" in mermaid


def test_mermaid_without_metrics(linear_workflow):
    mermaid = generate_mermaid(linear_workflow, show_metrics=False)
    # Should not contain metric annotations
    assert "$" not in mermaid


def test_mermaid_styles(linear_workflow):
    mermaid = generate_mermaid(linear_workflow)
    assert "style" in mermaid
    assert "fill:" in mermaid


def test_mermaid_renders_valid_syntax(branching_workflow):
    mermaid = generate_mermaid(branching_workflow)
    lines = mermaid.strip().split("\n")
    assert lines[0].strip() == "graph LR"
    # Basic syntax check: no unclosed brackets
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("style"):
            # Should either be a node definition or edge definition
            assert "-->" in stripped or "[" in stripped or "{" in stripped or "(" in stripped or stripped == ""
