"""REST API routes — thin wrappers over ProSim engine functions."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prosim.export.mermaid import generate_mermaid
from prosim.graph.models import WorkflowGraph
from prosim.graph.serialization import graph_from_json, graph_to_json
from prosim.intervention.engine import apply_interventions
from prosim.intervention.leverage import rank_leverage
from prosim.intervention.models import Intervention, InterventionComparison, LeverageRanking
from prosim.simulation.bottleneck import detect_bottlenecks
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.montecarlo import run_monte_carlo
from prosim.simulation.results import SimulationConfig, SimulationMode, SimulationResults
from prosim.simulation.sensitivity import SensitivityReport, run_sensitivity_analysis

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    description: str
    model: str | None = None


class ParseRequest(BaseModel):
    data: dict[str, Any]


class SimulateRequest(BaseModel):
    workflow: dict[str, Any]
    mode: str = "deterministic"
    num_transactions: int = Field(default=10_000, ge=100, le=1_000_000)
    volume_per_hour: float = Field(default=100.0, ge=0.1, le=100_000)
    seed: int | None = 42


class SensitivityRequest(BaseModel):
    workflow: dict[str, Any]
    volume_per_hour: float = Field(default=100.0, ge=0.1, le=100_000)
    num_transactions: int = Field(default=10_000, ge=100, le=1_000_000)
    perturbation_pct: float = Field(default=10.0, ge=0.1, le=100.0)


class InterveneRequest(BaseModel):
    workflow: dict[str, Any]
    interventions: list[dict[str, Any]]
    baseline_results: dict[str, Any]
    volume_per_hour: float = Field(default=100.0, ge=0.1, le=100_000)
    num_transactions: int = Field(default=10_000, ge=100, le=1_000_000)


class LeverageRequest(BaseModel):
    workflow: dict[str, Any]
    sensitivity: dict[str, Any]
    top_n: int = Field(default=10, ge=1, le=100)


class MermaidRequest(BaseModel):
    workflow: dict[str, Any]
    results: dict[str, Any] | None = None
    show_metrics: bool = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/workflow/generate")
def workflow_generate(req: GenerateRequest) -> dict[str, Any]:
    """Generate a workflow from a natural-language description via Claude API."""
    try:
        from prosim.parser.client import generate_workflow_raw
        from prosim.parser.postprocess import postprocess_raw_workflow

        raw = generate_workflow_raw(req.description, model=req.model)
        wf = postprocess_raw_workflow(raw)
        return graph_to_json(wf)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Anthropic API errors, postprocess KeyError/ValueError, etc.
        detail = str(exc) or "Workflow generation failed"
        if isinstance(exc, (KeyError, ValueError, TypeError)):
            detail = f"Workflow generation produced invalid output: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc


@router.post("/workflow/parse")
def workflow_parse(req: ParseRequest) -> dict[str, Any]:
    """Validate and normalise an uploaded workflow JSON."""
    try:
        wf = graph_from_json(req.data)
        return graph_to_json(wf)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/simulate")
def simulate(req: SimulateRequest) -> dict[str, Any]:
    """Run deterministic or Monte Carlo simulation."""
    wf = graph_from_json(req.workflow)
    config = SimulationConfig(
        mode=SimulationMode(req.mode),
        num_transactions=req.num_transactions,
        volume_per_hour=req.volume_per_hour,
        seed=req.seed,
    )

    if config.mode == SimulationMode.MONTE_CARLO:
        results = run_monte_carlo(wf, config)
    else:
        results = run_deterministic(wf, config)

    results.bottlenecks = detect_bottlenecks(results)
    return results.model_dump(mode="json")


@router.post("/sensitivity")
def sensitivity(req: SensitivityRequest) -> dict[str, Any]:
    """Run sensitivity analysis."""
    wf = graph_from_json(req.workflow)
    config = SimulationConfig(
        num_transactions=req.num_transactions,
        volume_per_hour=req.volume_per_hour,
    )
    report = run_sensitivity_analysis(wf, config, perturbation_pct=req.perturbation_pct)
    return report.model_dump(mode="json")


@router.post("/intervene")
def intervene(req: InterveneRequest) -> dict[str, Any]:
    """Apply interventions and return before/after comparison."""
    wf = graph_from_json(req.workflow)
    interventions = [Intervention(**i) for i in req.interventions]
    baseline = SimulationResults(**req.baseline_results)
    config = SimulationConfig(
        volume_per_hour=req.volume_per_hour,
        num_transactions=req.num_transactions,
    )
    comparison = apply_interventions(wf, interventions, baseline, config)
    return comparison.model_dump(mode="json")


@router.post("/leverage")
def leverage(req: LeverageRequest) -> list[dict[str, Any]]:
    """Rank nodes by improvement leverage."""
    wf = graph_from_json(req.workflow)
    report = SensitivityReport(**req.sensitivity)
    rankings = rank_leverage(wf, report, top_n=req.top_n)
    return [r.model_dump(mode="json") for r in rankings]


@router.post("/export/mermaid")
def export_mermaid(req: MermaidRequest) -> dict[str, str]:
    """Generate Mermaid diagram code."""
    wf = graph_from_json(req.workflow)
    results = SimulationResults(**req.results) if req.results else None
    code = generate_mermaid(wf, results=results, show_metrics=req.show_metrics)
    return {"mermaid": code}
