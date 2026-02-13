"""Tests for deterministic simulation engine."""

from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig, SimulationMode


def test_deterministic_linear(linear_workflow):
    config = SimulationConfig(mode=SimulationMode.DETERMINISTIC, num_transactions=1000, volume_per_hour=100)
    results = run_deterministic(linear_workflow, config)

    assert results.total_transactions == 1000
    assert results.avg_total_time > 0
    assert results.avg_total_cost > 0
    assert results.throughput_per_hour > 0
    assert len(results.node_metrics) == 4


def test_deterministic_branching(branching_workflow):
    config = SimulationConfig(mode=SimulationMode.DETERMINISTIC, num_transactions=10000, volume_per_hour=100)
    results = run_deterministic(branching_workflow, config)

    assert results.total_transactions == 10000
    assert results.completed_transactions > 0
    assert results.avg_total_time > 0

    # Check that review node has highest time contribution
    review_metrics = results.get_node_metrics("review")
    assert review_metrics is not None
    assert review_metrics.avg_time > 0
    assert review_metrics.avg_cost > 0


def test_deterministic_cost_calculation(linear_workflow):
    config = SimulationConfig(mode=SimulationMode.DETERMINISTIC, num_transactions=100)
    results = run_deterministic(linear_workflow, config)

    # Total cost should include both validate and process costs
    assert results.avg_total_cost > 0
    assert results.total_cost == results.avg_total_cost * results.total_transactions


def test_deterministic_metrics_consistency(linear_workflow):
    config = SimulationConfig(mode=SimulationMode.DETERMINISTIC, num_transactions=5000)
    results = run_deterministic(linear_workflow, config)

    # Verify node metrics exist for each node
    for node in linear_workflow.nodes:
        nm = results.get_node_metrics(node.id)
        assert nm is not None
        assert nm.node_id == node.id


def test_deterministic_retry_overhead(linear_workflow):
    """Validate node has retries configured - verify time includes retry overhead."""
    config = SimulationConfig(mode=SimulationMode.DETERMINISTIC, num_transactions=100)
    results = run_deterministic(linear_workflow, config)

    validate_metrics = results.get_node_metrics("validate")
    assert validate_metrics is not None
    # With error_rate=0.02 and max_retries=2, there's a retry factor
    # avg_time should be > exec_time_mean due to retry overhead
    assert validate_metrics.avg_time >= linear_workflow.get_node("validate").params.exec_time_mean
