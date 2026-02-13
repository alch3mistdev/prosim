"""Intervention engine — apply modifications to graph, re-simulate, compute deltas."""

from __future__ import annotations

import copy

from prosim.graph.models import WorkflowGraph
from prosim.intervention.models import (
    Intervention,
    InterventionComparison,
    MetricDelta,
)
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import SimulationConfig, SimulationResults


def apply_interventions(
    workflow: WorkflowGraph,
    interventions: list[Intervention],
    baseline_results: SimulationResults,
    config: SimulationConfig | None = None,
) -> InterventionComparison:
    """Apply a set of interventions and compute before/after comparison.

    1. Deep-copy the workflow
    2. Apply each intervention's parameter modifications
    3. Re-run simulation
    4. Compute deltas and ROI
    """
    if config is None:
        config = baseline_results.config

    # Apply interventions to a copy
    optimized_wf = copy.deepcopy(workflow)
    for intervention in interventions:
        _apply_single(optimized_wf, intervention)

    # Re-simulate
    optimized_results = run_deterministic(optimized_wf, config)

    # Compute deltas
    deltas = _compute_deltas(baseline_results, optimized_results)

    # Compute summary
    time_saved = _pct_change(baseline_results.avg_total_time, optimized_results.avg_total_time)
    cost_saved = _pct_change(baseline_results.avg_total_cost, optimized_results.avg_total_cost)
    throughput_inc = _pct_change(
        baseline_results.throughput_per_hour,
        optimized_results.throughput_per_hour,
        invert=True,
    )
    error_red = _pct_change(baseline_results.failed_transactions, optimized_results.failed_transactions)

    # ROI calculation
    total_impl_cost = sum(i.implementation_cost for i in interventions)
    hours_per_year = 8760
    annual_cost_savings = (
        (baseline_results.avg_total_cost - optimized_results.avg_total_cost)
        * config.volume_per_hour
        * hours_per_year
    )

    roi = annual_cost_savings / total_impl_cost if total_impl_cost > 0 else None
    payback = (total_impl_cost / (annual_cost_savings / 12)) if annual_cost_savings > 0 else None

    return InterventionComparison(
        interventions_applied=interventions,
        deltas=deltas,
        time_saved_pct=round(time_saved, 2),
        cost_saved_pct=round(cost_saved, 2),
        throughput_increase_pct=round(throughput_inc, 2),
        error_reduction_pct=round(error_red, 2),
        total_implementation_cost=total_impl_cost,
        annual_cost_savings=round(annual_cost_savings, 2),
        roi_ratio=round(roi, 2) if roi is not None else None,
        payback_months=round(payback, 1) if payback is not None else None,
    )


def _apply_single(workflow: WorkflowGraph, intervention: Intervention) -> None:
    """Apply a single intervention to a workflow graph (mutates in place)."""
    node = workflow.get_node(intervention.node_id)
    if not node:
        return

    p = node.params

    if intervention.time_reduction_pct > 0:
        factor = max(0.0, 1.0 - min(intervention.time_reduction_pct, 100.0) / 100.0)
        p.exec_time_mean *= factor
        p.exec_time_variance *= factor * factor

    if intervention.cost_reduction_pct > 0:
        factor = max(0.0, 1.0 - min(intervention.cost_reduction_pct, 100.0) / 100.0)
        p.cost_per_transaction *= factor

    if intervention.error_reduction_pct > 0:
        factor = max(0.0, 1.0 - min(intervention.error_reduction_pct, 100.0) / 100.0)
        p.error_rate *= factor

    if intervention.capacity_increase_pct > 0:
        if p.capacity_per_hour is not None:
            p.capacity_per_hour *= (1.0 + intervention.capacity_increase_pct / 100.0)

    if intervention.parallelization_increase > 0:
        p.parallelization_factor += intervention.parallelization_increase

    if intervention.queue_reduction_pct > 0:
        factor = max(0.0, 1.0 - min(intervention.queue_reduction_pct, 100.0) / 100.0)
        p.queue_delay_mean *= factor
        p.queue_delay_variance *= factor * factor


def _compute_deltas(
    baseline: SimulationResults,
    optimized: SimulationResults,
) -> list[MetricDelta]:
    """Compute metric deltas between baseline and optimized results."""
    metrics = [
        ("avg_total_time", "Average Total Time (s)"),
        ("avg_total_cost", "Average Total Cost"),
        ("throughput_per_hour", "Throughput (tx/hr)"),
        ("completed_transactions", "Completed Transactions"),
        ("failed_transactions", "Failed Transactions"),
        ("dropped_transactions", "Dropped Transactions"),
    ]

    deltas = []
    for attr, name in metrics:
        bv = getattr(baseline, attr)
        ov = getattr(optimized, attr)
        abs_change = ov - bv
        rel_change = (abs_change / max(abs(bv), 1e-10)) * 100

        deltas.append(
            MetricDelta(
                metric_name=name,
                baseline_value=round(bv, 4),
                optimized_value=round(ov, 4),
                absolute_change=round(abs_change, 4),
                relative_change_pct=round(rel_change, 2),
            )
        )

    return deltas


def _pct_change(old: float, new: float, invert: bool = False) -> float:
    """Compute percentage change. If invert, positive means improvement."""
    if abs(old) < 1e-10:
        return 0.0
    change = ((old - new) / abs(old)) * 100
    return change if not invert else -change
