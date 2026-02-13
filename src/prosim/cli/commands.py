"""CLI command implementations for generate, simulate, intervene, export, and dashboard."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from prosim.export.json_export import export_full, save_export
from prosim.export.mermaid import generate_mermaid
from prosim.export.reports import (
    format_comparison_report,
    format_leverage_report,
    format_simulation_report,
)
from prosim.graph.serialization import load_graph, save_graph
from prosim.intervention.engine import apply_interventions
from prosim.intervention.leverage import rank_leverage
from prosim.intervention.models import Intervention
from prosim.simulation.bottleneck import detect_bottlenecks
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.montecarlo import run_monte_carlo
from prosim.simulation.results import SimulationConfig, SimulationMode
from prosim.simulation.sensitivity import run_sensitivity_analysis

console = Console()


@click.command()
@click.argument("description")
@click.option("--output", "-o", default="workflow.json", help="Output file path")
@click.option("--model", "-m", default=None, help="Claude model to use")
def generate_cmd(description: str, output: str, model: str | None) -> None:
    """Generate a workflow graph from a natural language description.

    DESCRIPTION is the process to model (e.g., "invoice processing system").
    """
    from prosim.parser.client import generate_workflow_raw
    from prosim.parser.postprocess import postprocess_raw_workflow

    console.print(f"[bold blue]Generating workflow for:[/] {description}")

    try:
        raw = generate_workflow_raw(description, model=model)
        workflow = postprocess_raw_workflow(raw)
        save_graph(workflow, output)
        console.print(f"[bold green]Workflow saved to {output}[/]")
        console.print(f"  Nodes: {len(workflow.nodes)}")
        console.print(f"  Edges: {len(workflow.edges)}")

        # Show Mermaid preview
        mermaid = generate_mermaid(workflow)
        console.print("\n[bold]Mermaid Diagram:[/]")
        console.print(f"```mermaid\n{mermaid}\n```")

    except EnvironmentError as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Generation failed:[/] {e}")
        sys.exit(1)


@click.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--mode", "-m", type=click.Choice(["deterministic", "monte_carlo"]), default="deterministic")
@click.option("--transactions", "-n", type=int, default=10000, help="Number of transactions")
@click.option("--seed", type=int, default=42, help="Random seed")
@click.option("--volume", type=float, default=100.0, help="Transactions per hour")
@click.option("--sensitivity/--no-sensitivity", default=False, help="Run sensitivity analysis")
@click.option("--output", "-o", default=None, help="Save results to JSON file")
def simulate_cmd(
    workflow_file: str,
    mode: str,
    transactions: int,
    seed: int,
    volume: float,
    sensitivity: bool,
    output: str | None,
) -> None:
    """Run simulation on a workflow graph.

    WORKFLOW_FILE is the path to a workflow JSON file.
    """
    workflow = load_graph(workflow_file)
    config = SimulationConfig(
        mode=SimulationMode(mode),
        num_transactions=transactions,
        seed=seed,
        volume_per_hour=volume,
    )

    console.print(f"[bold blue]Simulating {workflow.name}[/] ({mode}, {transactions:,} transactions)")

    if mode == "deterministic":
        results = run_deterministic(workflow, config)
    else:
        results = run_monte_carlo(workflow, config)

    # Detect bottlenecks
    results.bottlenecks = detect_bottlenecks(results)

    # Run sensitivity analysis if requested
    if sensitivity:
        console.print("[dim]Running sensitivity analysis...[/]")
        results.sensitivity = run_sensitivity_analysis(workflow, config)

    # Display report
    report = format_simulation_report(results)
    console.print(report)

    # Show leverage rankings if sensitivity was run
    if results.sensitivity:
        rankings = rank_leverage(workflow, results.sensitivity)
        leverage_report = format_leverage_report(rankings)
        console.print(leverage_report)

    # Save results if output specified
    if output:
        data = export_full(workflow, results)
        save_export(data, output)
        console.print(f"[bold green]Results saved to {output}[/]")


@click.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--node", "-n", required=True, help="Target node ID")
@click.option("--time-reduction", type=float, default=0.0, help="Time reduction %")
@click.option("--cost-reduction", type=float, default=0.0, help="Cost reduction %")
@click.option("--error-reduction", type=float, default=0.0, help="Error reduction %")
@click.option("--capacity-increase", type=float, default=0.0, help="Capacity increase %")
@click.option("--add-workers", type=int, default=0, help="Additional parallel workers")
@click.option("--queue-reduction", type=float, default=0.0, help="Queue delay reduction %")
@click.option("--impl-cost", type=float, default=0.0, help="Implementation cost ($)")
@click.option("--volume", type=float, default=100.0, help="Transactions per hour")
@click.option("--output", "-o", default=None, help="Save comparison to JSON file")
def intervene_cmd(
    workflow_file: str,
    node: str,
    time_reduction: float,
    cost_reduction: float,
    error_reduction: float,
    capacity_increase: float,
    add_workers: int,
    queue_reduction: float,
    impl_cost: float,
    volume: float,
    output: str | None,
) -> None:
    """Apply an intervention to a workflow node and show impact.

    WORKFLOW_FILE is the path to a workflow JSON file.
    """
    workflow = load_graph(workflow_file)

    # Verify node exists
    target = workflow.get_node(node)
    if not target:
        console.print(f"[bold red]Node '{node}' not found.[/] Available nodes:")
        for n in workflow.nodes:
            console.print(f"  - {n.id}: {n.name}")
        sys.exit(1)

    intervention = Intervention(
        node_id=node,
        time_reduction_pct=time_reduction,
        cost_reduction_pct=cost_reduction,
        error_reduction_pct=error_reduction,
        capacity_increase_pct=capacity_increase,
        parallelization_increase=add_workers,
        queue_reduction_pct=queue_reduction,
        implementation_cost=impl_cost,
    )

    config = SimulationConfig(volume_per_hour=volume)
    baseline = run_deterministic(workflow, config)

    console.print(f"[bold blue]Applying intervention to:[/] {target.name}")
    comparison = apply_interventions(workflow, [intervention], baseline, config)

    report = format_comparison_report(comparison)
    console.print(report)

    if output:
        data = export_full(workflow, comparison=comparison)
        save_export(data, output)
        console.print(f"[bold green]Comparison saved to {output}[/]")


@click.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", type=click.Choice(["mermaid", "json"]), default="mermaid")
@click.option("--output", "-o", default=None, help="Output file (stdout if not specified)")
def export_cmd(workflow_file: str, fmt: str, output: str | None) -> None:
    """Export a workflow graph as Mermaid diagram or JSON.

    WORKFLOW_FILE is the path to a workflow JSON file.
    """
    workflow = load_graph(workflow_file)

    if fmt == "mermaid":
        result = generate_mermaid(workflow)
    else:
        result = json.dumps(export_full(workflow), indent=2, default=str)

    if output:
        Path(output).write_text(result)
        console.print(f"[bold green]Exported to {output}[/]")
    else:
        console.print(result)


@click.command()
@click.option("--port", "-p", type=int, default=8501, help="Streamlit port")
def dashboard_cmd(port: int) -> None:
    """Launch the Streamlit web dashboard."""
    app_path = Path(__file__).parent.parent / "dashboard" / "app.py"
    console.print(f"[bold blue]Launching ProSim Dashboard on port {port}...[/]")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)],
    )
