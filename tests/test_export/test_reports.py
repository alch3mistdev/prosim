"""Tests for report generation."""

from prosim.export.reports import format_comparison_report, format_leverage_report, format_simulation_report
from prosim.intervention.engine import apply_interventions
from prosim.intervention.leverage import rank_leverage
from prosim.intervention.models import Intervention
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig
from prosim.simulation.sensitivity import run_sensitivity_analysis


def test_simulation_report(linear_workflow):
    config = SimulationConfig(num_transactions=1000)
    results = run_deterministic(linear_workflow, config)
    report = format_simulation_report(results)

    assert isinstance(report, str)
    assert len(report) > 0
    assert "Linear Invoice" in report
    assert "1,000" in report


def test_comparison_report(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    intervention = Intervention(node_id="process", time_reduction_pct=50.0, implementation_cost=5000.0)
    comparison = apply_interventions(linear_workflow, [intervention], baseline, config)

    report = format_comparison_report(comparison)
    assert isinstance(report, str)
    assert len(report) > 0


def test_leverage_report(linear_workflow):
    report = run_sensitivity_analysis(linear_workflow)
    rankings = rank_leverage(linear_workflow, report)
    output = format_leverage_report(rankings)

    assert isinstance(output, str)
    assert len(output) > 0
