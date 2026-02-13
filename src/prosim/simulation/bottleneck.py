"""Bottleneck detection using utilization-based scoring.

Identifies nodes that are the primary sources of friction (time),
energy drain (cost), and entropy (errors) in the workflow.
"""

from __future__ import annotations

from prosim.simulation.results import BottleneckInfo, NodeMetrics, SimulationResults


def compute_bottleneck_scores(node_metrics: list[NodeMetrics], avg_total_time: float) -> None:
    """Compute bottleneck scores for all node metrics (mutates in place).

    Simplified inline scoring used by both simulation engines:
    score = 0.4 * time_contribution_pct + 0.3 * utilization + 0.3 * queue_time_pct
    """
    total_time_contrib = sum(nm.total_time_contribution for nm in node_metrics)
    for nm in node_metrics:
        time_pct = nm.total_time_contribution / max(total_time_contrib, 1e-10)
        nm.bottleneck_score = (
            0.4 * time_pct
            + 0.3 * nm.utilization
            + 0.3 * (nm.queue_time / max(avg_total_time, 1e-10))
        )


def detect_bottlenecks(
    results: SimulationResults,
    top_n: int = 5,
) -> list[BottleneckInfo]:
    """Detect bottleneck nodes from simulation results.

    Scoring formula:
    score = 0.35 * time_contribution_pct
          + 0.25 * utilization
          + 0.20 * queue_time_pct
          + 0.10 * error_rate
          + 0.10 * cost_contribution_pct

    Returns the top N bottleneck nodes ranked by score.
    """
    if not results.node_metrics:
        return []

    total_time_contrib = sum(nm.total_time_contribution for nm in results.node_metrics)
    total_cost = sum(nm.total_cost for nm in results.node_metrics)
    max_queue = max((nm.queue_time for nm in results.node_metrics), default=1.0)

    bottlenecks = []
    for nm in results.node_metrics:
        if nm.transactions_processed == 0:
            continue

        time_pct = nm.total_time_contribution / max(total_time_contrib, 1e-10)
        cost_pct = nm.total_cost / max(total_cost, 1e-10)
        queue_pct = nm.queue_time / max(max_queue, 1e-10)
        error_rate = nm.transactions_errored / max(nm.transactions_processed, 1)

        score = (
            0.35 * time_pct
            + 0.25 * nm.utilization
            + 0.20 * queue_pct
            + 0.10 * error_rate
            + 0.10 * cost_pct
        )

        # Determine primary reason
        components = {
            "High time contribution": time_pct,
            "High utilization": nm.utilization,
            "High queue delay": queue_pct,
            "High error rate": error_rate,
            "High cost": cost_pct,
        }
        reason = max(components, key=components.get)  # type: ignore[arg-type]

        bottlenecks.append(
            BottleneckInfo(
                node_id=nm.node_id,
                node_name=nm.node_name,
                score=round(score, 4),
                reason=reason,
                utilization=nm.utilization,
                avg_queue_time=nm.queue_time,
                time_contribution_pct=round(time_pct * 100, 2),
            )
        )

    bottlenecks.sort(key=lambda b: b.score, reverse=True)
    return bottlenecks[:top_n]
