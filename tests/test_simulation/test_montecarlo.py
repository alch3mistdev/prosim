"""Tests for Monte Carlo simulation engine."""

from prosim.simulation.montecarlo import run_monte_carlo
from prosim.simulation.results import SimulationConfig, SimulationMode


def test_monte_carlo_linear(linear_workflow):
    config = SimulationConfig(
        mode=SimulationMode.MONTE_CARLO,
        num_transactions=1000,
        seed=42,
        volume_per_hour=100,
    )
    results = run_monte_carlo(linear_workflow, config)

    assert results.total_transactions == 1000
    assert results.completed_transactions > 0
    assert results.avg_total_time > 0
    assert results.avg_total_cost > 0


def test_monte_carlo_branching(branching_workflow):
    config = SimulationConfig(
        mode=SimulationMode.MONTE_CARLO,
        num_transactions=5000,
        seed=42,
    )
    results = run_monte_carlo(branching_workflow, config)

    assert results.total_transactions == 5000
    assert results.completed_transactions > 0

    # Both approve and reject nodes should have been visited
    approve_nm = results.get_node_metrics("approve")
    reject_nm = results.get_node_metrics("reject")
    assert approve_nm is not None and approve_nm.transactions_processed > 0
    assert reject_nm is not None and reject_nm.transactions_processed > 0


def test_monte_carlo_reproducible(linear_workflow):
    config = SimulationConfig(
        mode=SimulationMode.MONTE_CARLO,
        num_transactions=500,
        seed=123,
    )
    r1 = run_monte_carlo(linear_workflow, config)
    r2 = run_monte_carlo(linear_workflow, config)

    assert r1.avg_total_time == r2.avg_total_time
    assert r1.avg_total_cost == r2.avg_total_cost
    assert r1.completed_transactions == r2.completed_transactions


def test_monte_carlo_different_seeds(linear_workflow):
    config1 = SimulationConfig(mode=SimulationMode.MONTE_CARLO, num_transactions=1000, seed=1)
    config2 = SimulationConfig(mode=SimulationMode.MONTE_CARLO, num_transactions=1000, seed=999)

    r1 = run_monte_carlo(linear_workflow, config1)
    r2 = run_monte_carlo(linear_workflow, config2)

    # Different seeds should produce different (but similar) results
    # They won't be exactly equal
    assert r1.avg_total_time != r2.avg_total_time or r1.completed_transactions != r2.completed_transactions


def test_monte_carlo_percentiles(linear_workflow):
    config = SimulationConfig(
        mode=SimulationMode.MONTE_CARLO,
        num_transactions=10000,
        seed=42,
    )
    results = run_monte_carlo(linear_workflow, config)

    assert results.p50_total_time > 0
    assert results.p95_total_time >= results.p50_total_time
    assert results.p99_total_time >= results.p95_total_time
    assert results.min_total_time <= results.p50_total_time
    assert results.max_total_time >= results.p99_total_time
