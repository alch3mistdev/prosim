"""Structured JSON export for graphs, simulation results, and comparisons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prosim.graph.models import WorkflowGraph
from prosim.graph.serialization import graph_to_json
from prosim.intervention.models import InterventionComparison
from prosim.simulation.results import SimulationResults


def export_full(
    workflow: WorkflowGraph,
    results: SimulationResults | None = None,
    comparison: InterventionComparison | None = None,
) -> dict[str, Any]:
    """Export complete JSON package with graph, results, and comparison."""
    output: dict[str, Any] = {
        "workflow": graph_to_json(workflow),
    }

    if results:
        output["simulation_results"] = results.model_dump(mode="json")

    if comparison:
        output["intervention_comparison"] = comparison.model_dump(mode="json")

    return output


def save_export(
    data: dict[str, Any],
    path: str | Path,
) -> None:
    """Save JSON export to a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
