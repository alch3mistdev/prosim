"""JSON serialization and deserialization for workflow graphs."""

from __future__ import annotations

import json
from pathlib import Path

from prosim.graph.models import WorkflowGraph


def graph_to_json(workflow: WorkflowGraph) -> dict:
    """Serialize a WorkflowGraph to a JSON-compatible dict."""
    return workflow.model_dump(mode="json")


def graph_from_json(data: dict) -> WorkflowGraph:
    """Deserialize a WorkflowGraph from a JSON-compatible dict."""
    return WorkflowGraph.model_validate(data)


def save_graph(workflow: WorkflowGraph, path: str | Path) -> None:
    """Save a WorkflowGraph to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(graph_to_json(workflow), f, indent=2)


def load_graph(path: str | Path) -> WorkflowGraph:
    """Load a WorkflowGraph from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return graph_from_json(data)
