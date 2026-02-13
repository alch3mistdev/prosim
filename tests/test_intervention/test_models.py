"""Tests for intervention models."""

from prosim.intervention.models import Intervention, InterventionComparison, LeverageRanking, MetricDelta


def test_intervention_defaults():
    i = Intervention(node_id="test")
    assert i.time_reduction_pct == 0.0
    assert i.cost_reduction_pct == 0.0
    assert i.error_reduction_pct == 0.0
    assert i.parallelization_increase == 0
    assert i.implementation_cost == 0.0


def test_intervention_with_values():
    i = Intervention(
        node_id="validate",
        time_reduction_pct=30.0,
        cost_reduction_pct=20.0,
        implementation_cost=10000.0,
    )
    assert i.time_reduction_pct == 30.0
    assert i.cost_reduction_pct == 20.0
    assert i.implementation_cost == 10000.0


def test_metric_delta():
    d = MetricDelta(
        metric_name="Total Time",
        baseline_value=100.0,
        optimized_value=80.0,
        absolute_change=-20.0,
        relative_change_pct=-20.0,
    )
    assert d.absolute_change == -20.0
    assert d.relative_change_pct == -20.0


def test_intervention_comparison():
    comp = InterventionComparison(
        time_saved_pct=25.0,
        cost_saved_pct=15.0,
        total_implementation_cost=50000,
        annual_cost_savings=200000,
        roi_ratio=4.0,
        payback_months=3.0,
    )
    assert comp.roi_ratio == 4.0
    assert comp.payback_months == 3.0


def test_leverage_ranking():
    r = LeverageRanking(
        node_id="process",
        node_name="Process Payment",
        parameter="exec_time_mean",
        leverage_score=0.85,
        time_impact_pct=12.5,
        cost_impact_pct=3.2,
        recommendation="Reduce execution time",
    )
    assert r.leverage_score == 0.85
