"""Sensitivity analysis — compute marginal impact of parameter changes on system metrics.

Uses perturbation method: for each (node, parameter) pair, apply a small
percentage change and measure the impact on total time and total cost.
"""

from __future__ import annotations

import copy

from prosim.graph.models import WorkflowGraph
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.results import (
    SensitivityEntry,
    SensitivityReport,
    SimulationConfig,
    SimulationMode,
)

# Parameters to analyze sensitivity for
SENSITIVITY_PARAMS = [
    "exec_time_mean",
    "cost_per_transaction",
    "error_rate",
    "queue_delay_mean",
    "parallelization_factor",
]

# System metrics to measure impact on
SYSTEM_METRICS = ["avg_total_time", "avg_total_cost"]


def run_sensitivity_analysis(
    workflow: WorkflowGraph,
    config: SimulationConfig | None = None,
    perturbation_pct: float = 10.0,
) -> SensitivityReport:
    """Run sensitivity analysis by perturbing each node parameter.

    For each (node, parameter) combination:
    1. Create a copy of the workflow
    2. Increase the parameter by perturbation_pct%
    3. Run deterministic simulation
    4. Measure change in system metrics
    """
    if config is None:
        config = SimulationConfig(mode=SimulationMode.DETERMINISTIC)

    # Run baseline
    baseline_results = run_deterministic(workflow, config)
    baseline_metrics = {
        "avg_total_time": baseline_results.avg_total_time,
        "avg_total_cost": baseline_results.avg_total_cost,
    }

    entries: list[SensitivityEntry] = []

    for node in workflow.nodes:
        for param_name in SENSITIVITY_PARAMS:
            baseline_value = getattr(node.params, param_name)

            # Skip if baseline is zero (can't compute relative change meaningfully)
            if param_name == "parallelization_factor":
                # For parallelization, increase by 1 (discrete)
                perturbed_value = baseline_value + 1
            elif baseline_value == 0:
                continue
            else:
                perturbed_value = baseline_value * (1 + perturbation_pct / 100.0)

            # Create perturbed workflow
            perturbed_wf = _perturb_workflow(workflow, node.id, param_name, perturbed_value)
            perturbed_results = run_deterministic(perturbed_wf, config)

            for metric_name in SYSTEM_METRICS:
                perturbed_metric = getattr(perturbed_results, metric_name)
                baseline_metric = baseline_metrics[metric_name]

                absolute_impact = perturbed_metric - baseline_metric
                relative_impact = (absolute_impact / max(abs(baseline_metric), 1e-10)) * 100

                entries.append(
                    SensitivityEntry(
                        node_id=node.id,
                        parameter=param_name,
                        baseline_value=baseline_value,
                        perturbed_value=perturbed_value,
                        metric_name=metric_name,
                        baseline_metric=baseline_metric,
                        perturbed_metric=perturbed_metric,
                        absolute_impact=round(absolute_impact, 6),
                        relative_impact_pct=round(relative_impact, 4),
                    )
                )

    return SensitivityReport(entries=entries, perturbation_pct=perturbation_pct)


def _perturb_workflow(
    workflow: WorkflowGraph,
    node_id: str,
    param_name: str,
    new_value: float,
) -> WorkflowGraph:
    """Create a copy of the workflow with one parameter changed."""
    wf = copy.deepcopy(workflow)
    node = wf.get_node(node_id)
    if node:
        setattr(node.params, param_name, new_value)
    return wf
