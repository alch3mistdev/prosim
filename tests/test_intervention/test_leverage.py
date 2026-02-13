"""Tests for leverage ranking."""

from prosim.intervention.leverage import rank_leverage
from prosim.simulation.results import SimulationConfig
from prosim.simulation.sensitivity import run_sensitivity_analysis


def test_rank_leverage_linear(linear_workflow):
    report = run_sensitivity_analysis(linear_workflow)
    rankings = rank_leverage(linear_workflow, report)

    assert len(rankings) > 0
    # Scores should be normalized to [0, 1]
    assert rankings[0].leverage_score <= 1.0
    assert rankings[0].leverage_score >= 0.0


def test_rank_leverage_top_n(linear_workflow):
    report = run_sensitivity_analysis(linear_workflow)
    rankings = rank_leverage(linear_workflow, report, top_n=3)
    assert len(rankings) <= 3


def test_rank_leverage_has_recommendations(linear_workflow):
    report = run_sensitivity_analysis(linear_workflow)
    rankings = rank_leverage(linear_workflow, report)

    for r in rankings:
        assert r.recommendation != ""
        assert r.node_name != ""
        assert r.parameter != ""


def test_rank_leverage_sorted_descending(linear_workflow):
    report = run_sensitivity_analysis(linear_workflow)
    rankings = rank_leverage(linear_workflow, report)

    for i in range(len(rankings) - 1):
        assert rankings[i].leverage_score >= rankings[i + 1].leverage_score
