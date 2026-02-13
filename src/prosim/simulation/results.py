"""Pydantic models for simulation configuration and results."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SimulationMode(str, Enum):
    """Simulation execution mode."""

    DETERMINISTIC = "deterministic"
    MONTE_CARLO = "monte_carlo"


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""

    mode: SimulationMode = Field(default=SimulationMode.DETERMINISTIC)
    num_transactions: int = Field(default=10000, ge=1, description="Number of transactions to simulate")
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")
    batch_size: int = Field(default=10000, ge=100, description="Batch size for Monte Carlo processing")
    volume_per_hour: float = Field(default=100.0, ge=0, description="Input transaction volume per hour")


class NodeMetrics(BaseModel):
    """Per-node simulation metrics."""

    node_id: str
    node_name: str

    # Time metrics
    avg_time: float = Field(default=0.0, description="Average execution time including queue")
    p50_time: float = Field(default=0.0, description="Median execution time")
    p95_time: float = Field(default=0.0, description="95th percentile execution time")
    p99_time: float = Field(default=0.0, description="99th percentile execution time")
    total_time_contribution: float = Field(default=0.0, description="Total time contribution to path")

    # Cost metrics
    avg_cost: float = Field(default=0.0, description="Average cost per transaction at this node")
    total_cost: float = Field(default=0.0, description="Total cost across all transactions")

    # Volume metrics
    transactions_processed: int = Field(default=0, description="Number of transactions processed")
    transactions_errored: int = Field(default=0, description="Number of transactions that errored")
    transactions_dropped: int = Field(default=0, description="Number of transactions dropped")
    transactions_retried: int = Field(default=0, description="Number of retries triggered")

    # Utilization
    utilization: float = Field(default=0.0, ge=0, le=1, description="Node utilization ratio")
    queue_time: float = Field(default=0.0, description="Average queue wait time")

    # Bottleneck score (higher = worse)
    bottleneck_score: float = Field(default=0.0, description="Composite bottleneck score")


class BottleneckInfo(BaseModel):
    """Information about a detected bottleneck."""

    node_id: str
    node_name: str
    score: float = Field(description="Bottleneck severity score (0-1)")
    reason: str = Field(description="Primary reason for bottleneck classification")
    utilization: float = Field(default=0.0)
    avg_queue_time: float = Field(default=0.0)
    time_contribution_pct: float = Field(default=0.0)


class SensitivityEntry(BaseModel):
    """Sensitivity of a system metric to a parameter change."""

    node_id: str
    parameter: str
    baseline_value: float
    perturbed_value: float
    metric_name: str
    baseline_metric: float
    perturbed_metric: float
    absolute_impact: float
    relative_impact_pct: float


class SensitivityReport(BaseModel):
    """Complete sensitivity analysis report."""

    entries: list[SensitivityEntry] = Field(default_factory=list)
    perturbation_pct: float = Field(default=10.0, description="Perturbation percentage used")


class SimulationResults(BaseModel):
    """Complete results from a simulation run."""

    config: SimulationConfig
    workflow_name: str

    # Aggregate metrics
    total_transactions: int = Field(default=0)
    completed_transactions: int = Field(default=0)
    failed_transactions: int = Field(default=0)
    dropped_transactions: int = Field(default=0)

    # Time metrics
    avg_total_time: float = Field(default=0.0, description="Average end-to-end time per transaction")
    p50_total_time: float = Field(default=0.0)
    p95_total_time: float = Field(default=0.0)
    p99_total_time: float = Field(default=0.0)
    min_total_time: float = Field(default=0.0)
    max_total_time: float = Field(default=0.0)

    # Cost metrics
    avg_total_cost: float = Field(default=0.0, description="Average end-to-end cost per transaction")
    total_cost: float = Field(default=0.0, description="Total cost across all transactions")

    # Throughput
    throughput_per_hour: float = Field(default=0.0, description="Effective throughput in transactions/hour")
    max_throughput_per_hour: float = Field(default=0.0, description="Maximum possible throughput")

    # Per-node metrics
    node_metrics: list[NodeMetrics] = Field(default_factory=list)

    # Bottlenecks
    bottlenecks: list[BottleneckInfo] = Field(default_factory=list)

    # Sensitivity (populated if sensitivity analysis was run)
    sensitivity: Optional[SensitivityReport] = None

    def get_node_metrics(self, node_id: str) -> Optional[NodeMetrics]:
        """Get metrics for a specific node."""
        for nm in self.node_metrics:
            if nm.node_id == node_id:
                return nm
        return None
