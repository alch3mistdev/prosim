"""Marginal leverage ranking — identify nodes with highest improvement potential."""

from __future__ import annotations

from prosim.graph.models import WorkflowGraph
from prosim.intervention.models import LeverageRanking
from prosim.simulation.results import SensitivityReport


def rank_leverage(
    workflow: WorkflowGraph,
    sensitivity: SensitivityReport,
    top_n: int = 10,
) -> list[LeverageRanking]:
    """Rank nodes by their marginal improvement leverage.

    Uses sensitivity analysis results to identify which (node, parameter)
    combinations yield the highest system-level improvement per unit change.

    Leverage score = normalized absolute impact across both time and cost metrics.
    """
    # Collect per-(node, param) impacts
    impact_map: dict[tuple[str, str], dict[str, float]] = {}

    for entry in sensitivity.entries:
        key = (entry.node_id, entry.parameter)
        if key not in impact_map:
            impact_map[key] = {"time_impact": 0.0, "cost_impact": 0.0}

        if entry.metric_name == "avg_total_time":
            impact_map[key]["time_impact"] = abs(entry.relative_impact_pct)
        elif entry.metric_name == "avg_total_cost":
            impact_map[key]["cost_impact"] = abs(entry.relative_impact_pct)

    # Compute composite leverage score
    # Weight time impact slightly higher than cost (time is usually the binding constraint)
    rankings: list[LeverageRanking] = []
    max_score = 0.0

    for (node_id, param), impacts in impact_map.items():
        score = 0.6 * impacts["time_impact"] + 0.4 * impacts["cost_impact"]
        max_score = max(max_score, score)

        node = workflow.get_node(node_id)
        node_name = node.name if node else node_id

        recommendation = _build_recommendation(param, impacts)

        rankings.append(
            LeverageRanking(
                node_id=node_id,
                node_name=node_name,
                parameter=param,
                leverage_score=score,
                time_impact_pct=round(impacts["time_impact"], 2),
                cost_impact_pct=round(impacts["cost_impact"], 2),
                recommendation=recommendation,
            )
        )

    # Normalize scores to [0, 1]
    if max_score > 0:
        for r in rankings:
            r.leverage_score = round(r.leverage_score / max_score, 4)

    rankings.sort(key=lambda r: r.leverage_score, reverse=True)
    return rankings[:top_n]


def _build_recommendation(param: str, impacts: dict[str, float]) -> str:
    """Generate a human-readable recommendation for a leverage point."""
    param_actions = {
        "exec_time_mean": "Reduce execution time",
        "cost_per_transaction": "Reduce per-transaction cost",
        "error_rate": "Reduce error rate",
        "queue_delay_mean": "Reduce queue delay",
        "parallelization_factor": "Add parallel workers",
    }

    action = param_actions.get(param, f"Optimize {param}")
    parts = [action]

    if impacts["time_impact"] > impacts["cost_impact"]:
        parts.append(f"(primary impact: {impacts['time_impact']:.1f}% on total time)")
    else:
        parts.append(f"(primary impact: {impacts['cost_impact']:.1f}% on total cost)")

    return " ".join(parts)
