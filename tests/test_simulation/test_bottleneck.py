"""Tests for bottleneck detection."""

from prosim.simulation.bottleneck import detect_bottlenecks
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig


def test_detect_bottlenecks_linear(linear_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    results = run_deterministic(linear_workflow, config)
    bottlenecks = detect_bottlenecks(results)

    assert len(bottlenecks) > 0
    # Process node (5s + 3s queue) should score higher than validate (2s)
    assert bottlenecks[0].node_id in ("process", "validate")


def test_detect_bottlenecks_branching(branching_workflow):
    config = SimulationConfig(num_transactions=1000, volume_per_hour=100)
    results = run_deterministic(branching_workflow, config)
    bottlenecks = detect_bottlenecks(results, top_n=3)

    assert len(bottlenecks) <= 3
    # Review node (300s) should be the top bottleneck
    assert bottlenecks[0].node_id == "review"
    assert bottlenecks[0].score > 0


def test_detect_bottlenecks_empty():
    from prosim.simulation.results import SimulationConfig, SimulationResults

    results = SimulationResults(
        config=SimulationConfig(),
        workflow_name="Empty",
    )
    bottlenecks = detect_bottlenecks(results)
    assert len(bottlenecks) == 0


def test_bottleneck_has_reason(branching_workflow):
    config = SimulationConfig(num_transactions=1000)
    results = run_deterministic(branching_workflow, config)
    bottlenecks = detect_bottlenecks(results)

    for bn in bottlenecks:
        assert bn.reason != ""
        assert bn.score >= 0
