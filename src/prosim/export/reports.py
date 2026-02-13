"""Generate baseline vs. optimized summary reports with Rich table formatting."""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prosim.intervention.models import InterventionComparison, LeverageRanking
from prosim.simulation.results import SimulationResults


def format_simulation_report(results: SimulationResults) -> str:
    """Format simulation results as a Rich-rendered string."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=100)

    # Summary panel
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Metric", style="bold cyan")
    summary.add_column("Value", style="white")

    summary.add_row("Workflow", results.workflow_name)
    summary.add_row("Mode", results.config.mode.value)
    summary.add_row("Transactions", f"{results.total_transactions:,}")
    summary.add_row("Completed", f"{results.completed_transactions:,}")
    summary.add_row("Failed", f"{results.failed_transactions:,}")
    summary.add_row("Dropped", f"{results.dropped_transactions:,}")

    console.print(Panel(summary, title="Simulation Summary", border_style="blue"))

    # Time metrics
    time_table = Table(title="Time Metrics", show_lines=True)
    time_table.add_column("Metric", style="bold")
    time_table.add_column("Value", justify="right")

    time_table.add_row("Avg Total Time", f"{results.avg_total_time:.2f}s")
    time_table.add_row("P50 Time", f"{results.p50_total_time:.2f}s")
    time_table.add_row("P95 Time", f"{results.p95_total_time:.2f}s")
    time_table.add_row("P99 Time", f"{results.p99_total_time:.2f}s")
    time_table.add_row("Throughput", f"{results.throughput_per_hour:.1f} tx/hr")

    console.print(time_table)

    # Cost metrics
    cost_table = Table(title="Cost Metrics", show_lines=True)
    cost_table.add_column("Metric", style="bold")
    cost_table.add_column("Value", justify="right")

    cost_table.add_row("Avg Cost/Transaction", f"${results.avg_total_cost:.4f}")
    cost_table.add_row("Total Cost", f"${results.total_cost:.2f}")

    console.print(cost_table)

    # Per-node metrics
    if results.node_metrics:
        node_table = Table(title="Node Metrics", show_lines=True)
        node_table.add_column("Node", style="bold")
        node_table.add_column("Avg Time", justify="right")
        node_table.add_column("Avg Cost", justify="right")
        node_table.add_column("Processed", justify="right")
        node_table.add_column("Errors", justify="right")
        node_table.add_column("Utilization", justify="right")
        node_table.add_column("Bottleneck", justify="right")

        sorted_metrics = sorted(results.node_metrics, key=lambda m: m.bottleneck_score, reverse=True)
        for nm in sorted_metrics:
            if nm.transactions_processed == 0:
                continue
            bottleneck_style = "bold red" if nm.bottleneck_score > 0.3 else ""
            node_table.add_row(
                nm.node_name,
                f"{nm.avg_time:.2f}s",
                f"${nm.avg_cost:.4f}",
                f"{nm.transactions_processed:,}",
                f"{nm.transactions_errored:,}",
                f"{nm.utilization:.1%}",
                f"[{bottleneck_style}]{nm.bottleneck_score:.3f}[/{bottleneck_style}]" if bottleneck_style else f"{nm.bottleneck_score:.3f}",
            )

        console.print(node_table)

    # Bottlenecks
    if results.bottlenecks:
        bn_table = Table(title="Bottlenecks (Top)", show_lines=True)
        bn_table.add_column("Node", style="bold red")
        bn_table.add_column("Score", justify="right")
        bn_table.add_column("Reason")
        bn_table.add_column("Time %", justify="right")

        for bn in results.bottlenecks[:5]:
            bn_table.add_row(
                bn.node_name,
                f"{bn.score:.4f}",
                bn.reason,
                f"{bn.time_contribution_pct:.1f}%",
            )

        console.print(bn_table)

    return buf.getvalue()


def format_comparison_report(comparison: InterventionComparison) -> str:
    """Format intervention comparison as a Rich-rendered string."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=100)

    # Delta table
    delta_table = Table(title="Baseline vs. Optimized", show_lines=True)
    delta_table.add_column("Metric", style="bold")
    delta_table.add_column("Baseline", justify="right")
    delta_table.add_column("Optimized", justify="right")
    delta_table.add_column("Change", justify="right")
    delta_table.add_column("Change %", justify="right")

    for d in comparison.deltas:
        change_style = "green" if d.relative_change_pct < 0 else "red"
        if "Throughput" in d.metric_name or "Completed" in d.metric_name:
            change_style = "green" if d.relative_change_pct > 0 else "red"

        delta_table.add_row(
            d.metric_name,
            f"{d.baseline_value:.4f}",
            f"{d.optimized_value:.4f}",
            f"{d.absolute_change:+.4f}",
            f"[{change_style}]{d.relative_change_pct:+.2f}%[/]",
        )

    console.print(delta_table)

    # ROI summary
    roi_table = Table(show_header=False, box=None, padding=(0, 2))
    roi_table.add_column("Metric", style="bold cyan")
    roi_table.add_column("Value", style="white")

    roi_table.add_row("Time Saved", f"{comparison.time_saved_pct:.1f}%")
    roi_table.add_row("Cost Saved", f"{comparison.cost_saved_pct:.1f}%")
    roi_table.add_row("Throughput Increase", f"{comparison.throughput_increase_pct:.1f}%")
    roi_table.add_row("Implementation Cost", f"${comparison.total_implementation_cost:,.2f}")
    roi_table.add_row("Annual Savings", f"${comparison.annual_cost_savings:,.2f}")
    if comparison.roi_ratio is not None:
        roi_table.add_row("ROI Ratio", f"{comparison.roi_ratio:.1f}x")
    if comparison.payback_months is not None:
        roi_table.add_row("Payback Period", f"{comparison.payback_months:.1f} months")

    console.print(Panel(roi_table, title="ROI Summary", border_style="green"))

    return buf.getvalue()


def format_leverage_report(rankings: list[LeverageRanking]) -> str:
    """Format leverage rankings as a Rich-rendered string."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=100)

    table = Table(title="Highest Marginal Leverage Nodes", show_lines=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Node", style="bold")
    table.add_column("Parameter")
    table.add_column("Score", justify="right")
    table.add_column("Time Impact", justify="right")
    table.add_column("Cost Impact", justify="right")
    table.add_column("Recommendation")

    for i, r in enumerate(rankings, 1):
        style = "bold yellow" if i == 1 else ""
        rank_str = f"[{style}]{i}[/{style}]" if style else str(i)
        name_str = f"[{style}]{r.node_name}[/{style}]" if style else r.node_name
        table.add_row(
            rank_str,
            name_str,
            r.parameter,
            f"{r.leverage_score:.4f}",
            f"{r.time_impact_pct:.1f}%",
            f"{r.cost_impact_pct:.1f}%",
            r.recommendation,
        )

    console.print(table)
    return buf.getvalue()
