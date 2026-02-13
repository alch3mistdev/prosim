"""Pydantic models for intervention specifications and comparison results."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Intervention(BaseModel):
    """A single intervention applied to a workflow node.

    Each field represents a percentage modification:
    - Negative values = reduction (improvement)
    - Positive values = increase
    """

    node_id: str = Field(description="Target node ID")
    time_reduction_pct: float = Field(default=0.0, description="% reduction in execution time (0-100)")
    cost_reduction_pct: float = Field(default=0.0, description="% reduction in cost (0-100)")
    error_reduction_pct: float = Field(default=0.0, description="% reduction in error rate (0-100)")
    capacity_increase_pct: float = Field(default=0.0, description="% increase in capacity (0+)")
    parallelization_increase: int = Field(default=0, ge=0, description="Additional parallel workers")
    queue_reduction_pct: float = Field(default=0.0, description="% reduction in queue delay (0-100)")

    # Optional: estimated cost of implementing this intervention
    implementation_cost: float = Field(default=0.0, ge=0, description="One-time cost to implement this intervention")


class MetricDelta(BaseModel):
    """Change in a single metric from baseline to optimized."""

    metric_name: str
    baseline_value: float
    optimized_value: float
    absolute_change: float
    relative_change_pct: float


class InterventionComparison(BaseModel):
    """Before/after comparison of workflow metrics after interventions."""

    interventions_applied: list[Intervention] = Field(default_factory=list)
    deltas: list[MetricDelta] = Field(default_factory=list)

    # Summary metrics
    time_saved_pct: float = Field(default=0.0)
    cost_saved_pct: float = Field(default=0.0)
    throughput_increase_pct: float = Field(default=0.0)
    error_reduction_pct: float = Field(default=0.0)

    # ROI
    total_implementation_cost: float = Field(default=0.0)
    annual_cost_savings: float = Field(default=0.0)
    roi_ratio: Optional[float] = Field(default=None, description="ROI = annual_savings / implementation_cost")
    payback_months: Optional[float] = Field(default=None, description="Months to break even")


class LeverageRanking(BaseModel):
    """A node ranked by its marginal improvement leverage."""

    node_id: str
    node_name: str
    parameter: str
    leverage_score: float = Field(description="Normalized leverage score (0-1)")
    time_impact_pct: float = Field(default=0.0, description="% impact on total time")
    cost_impact_pct: float = Field(default=0.0, description="% impact on total cost")
    recommendation: str = Field(default="", description="Human-readable recommendation")
