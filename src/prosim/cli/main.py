"""CLI entry point — Click command group with shared options."""

from __future__ import annotations

import click

from prosim.cli.commands import dashboard_cmd, export_cmd, generate_cmd, intervene_cmd, simulate_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="prosim")
def cli() -> None:
    """ProSim - Workflow Simulation Engine with Process Mining Capabilities.

    Generate, simulate, optimize, and visualize business process workflows.
    """


cli.add_command(generate_cmd, name="generate")
cli.add_command(simulate_cmd, name="simulate")
cli.add_command(intervene_cmd, name="intervene")
cli.add_command(export_cmd, name="export")
cli.add_command(dashboard_cmd, name="dashboard")


if __name__ == "__main__":
    cli()
