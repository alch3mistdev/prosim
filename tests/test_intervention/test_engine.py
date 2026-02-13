"""Tests for intervention engine."""

from prosim.intervention.engine import apply_interventions
from prosim.intervention.models import Intervention
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig


def test_time_reduction(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    intervention = Intervention(
        node_id="process",
        time_reduction_pct=50.0,
    )

    comparison = apply_interventions(linear_workflow, [intervention], baseline, config)

    assert comparison.time_saved_pct > 0
    # The time delta should show reduction
    time_delta = next((d for d in comparison.deltas if "Time" in d.metric_name), None)
    assert time_delta is not None
    assert time_delta.optimized_value < time_delta.baseline_value


def test_cost_reduction(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    intervention = Intervention(
        node_id="process",
        cost_reduction_pct=30.0,
    )

    comparison = apply_interventions(linear_workflow, [intervention], baseline, config)

    assert comparison.cost_saved_pct > 0
    cost_delta = next((d for d in comparison.deltas if "Cost" in d.metric_name), None)
    assert cost_delta is not None
    assert cost_delta.optimized_value <= cost_delta.baseline_value


def test_parallelization_increase(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    intervention = Intervention(
        node_id="process",
        parallelization_increase=2,
    )

    comparison = apply_interventions(linear_workflow, [intervention], baseline, config)
    assert comparison.time_saved_pct > 0


def test_roi_calculation(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    intervention = Intervention(
        node_id="process",
        cost_reduction_pct=50.0,
        implementation_cost=10000.0,
    )

    comparison = apply_interventions(linear_workflow, [intervention], baseline, config)
    assert comparison.total_implementation_cost == 10000.0
    if comparison.annual_cost_savings > 0:
        assert comparison.roi_ratio is not None
        assert comparison.roi_ratio > 0


def test_multiple_interventions(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    interventions = [
        Intervention(node_id="validate", time_reduction_pct=20.0),
        Intervention(node_id="process", time_reduction_pct=30.0, cost_reduction_pct=20.0),
    ]

    comparison = apply_interventions(linear_workflow, interventions, baseline, config)
    assert len(comparison.interventions_applied) == 2
    assert comparison.time_saved_pct > 0


def test_no_intervention(linear_workflow):
    """Applying no interventions should result in zero deltas."""
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    baseline = run_deterministic(linear_workflow, config)

    comparison = apply_interventions(linear_workflow, [], baseline, config)
    for delta in comparison.deltas:
        assert abs(delta.absolute_change) < 0.001
