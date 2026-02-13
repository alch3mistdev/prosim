"""Tests for sensitivity analysis."""

from prosim.simulation.results import SimulationConfig
from prosim.simulation.sensitivity import run_sensitivity_analysis


def test_sensitivity_linear(linear_workflow):
    config = SimulationConfig(num_transactions=1000)
    report = run_sensitivity_analysis(linear_workflow, config)

    assert len(report.entries) > 0
    assert report.perturbation_pct == 10.0

    # Check that entries have valid structure
    for entry in report.entries:
        assert entry.node_id != ""
        assert entry.parameter != ""
        assert entry.metric_name in ("avg_total_time", "avg_total_cost")


def test_sensitivity_branching(branching_workflow):
    config = SimulationConfig(num_transactions=1000)
    report = run_sensitivity_analysis(branching_workflow, config, perturbation_pct=20.0)

    assert len(report.entries) > 0
    assert report.perturbation_pct == 20.0


def test_sensitivity_exec_time_impact(linear_workflow):
    """Increasing exec_time_mean should increase avg_total_time."""
    report = run_sensitivity_analysis(linear_workflow)

    time_entries = [
        e for e in report.entries
        if e.parameter == "exec_time_mean" and e.metric_name == "avg_total_time"
    ]
    assert len(time_entries) > 0

    # Perturbing exec_time_mean upward should increase total time
    for entry in time_entries:
        if entry.baseline_value > 0:
            assert entry.absolute_impact >= 0


def test_sensitivity_cost_impact(linear_workflow):
    """Increasing cost_per_transaction should increase avg_total_cost."""
    report = run_sensitivity_analysis(linear_workflow)

    cost_entries = [
        e for e in report.entries
        if e.parameter == "cost_per_transaction" and e.metric_name == "avg_total_cost"
    ]
    assert len(cost_entries) > 0

    for entry in cost_entries:
        if entry.baseline_value > 0:
            assert entry.absolute_impact >= 0
