/* TypeScript types mirroring ProSim Pydantic models. */

export type NodeType =
  | "start"
  | "end"
  | "human"
  | "api"
  | "async"
  | "batch"
  | "decision"
  | "parallel_gateway"
  | "wait";

export type EdgeType = "normal" | "conditional" | "default" | "loop";

export interface NodeParams {
  exec_time_mean: number;
  exec_time_variance: number;
  cost_per_transaction: number;
  error_rate: number;
  drop_off_rate: number;
  sla_breach_probability: number;
  conversion_rate: number;
  parallelization_factor: number;
  queue_delay_mean: number;
  queue_delay_variance: number;
  capacity_per_hour: number | null;
  max_retries: number;
  retry_delay: number;
  volume_multiplier: number;
}

export interface WorkflowNode {
  id: string;
  name: string;
  node_type: NodeType;
  description: string;
  params: NodeParams;
}

export interface WorkflowEdge {
  source: string;
  target: string;
  edge_type: EdgeType;
  probability: number;
  condition: string;
}

export interface WorkflowGraph {
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface NodeMetrics {
  node_id: string;
  node_name: string;
  avg_time: number;
  p50_time: number;
  p95_time: number;
  p99_time: number;
  total_time_contribution: number;
  avg_cost: number;
  total_cost: number;
  transactions_processed: number;
  transactions_errored: number;
  transactions_dropped: number;
  transactions_retried: number;
  utilization: number;
  queue_time: number;
  bottleneck_score: number;
}

export interface BottleneckInfo {
  node_id: string;
  node_name: string;
  score: number;
  reason: string;
  utilization: number;
  avg_queue_time: number;
  time_contribution_pct: number;
}

export interface SimulationResults {
  config: {
    mode: string;
    num_transactions: number;
    seed: number | null;
    volume_per_hour: number;
  };
  workflow_name: string;
  total_transactions: number;
  completed_transactions: number;
  failed_transactions: number;
  dropped_transactions: number;
  avg_total_time: number;
  p50_total_time: number;
  p95_total_time: number;
  p99_total_time: number;
  min_total_time: number;
  max_total_time: number;
  avg_total_cost: number;
  total_cost: number;
  throughput_per_hour: number;
  max_throughput_per_hour: number;
  node_metrics: NodeMetrics[];
  bottlenecks: BottleneckInfo[];
}

export interface MetricDelta {
  metric_name: string;
  baseline_value: number;
  optimized_value: number;
  absolute_change: number;
  relative_change_pct: number;
}

export interface InterventionComparison {
  interventions_applied: Intervention[];
  deltas: MetricDelta[];
  time_saved_pct: number;
  cost_saved_pct: number;
  throughput_increase_pct: number;
  error_reduction_pct: number;
  total_implementation_cost: number;
  annual_cost_savings: number;
  roi_ratio: number | null;
  payback_months: number | null;
}

export interface Intervention {
  node_id: string;
  time_reduction_pct: number;
  cost_reduction_pct: number;
  error_reduction_pct: number;
  capacity_increase_pct: number;
  parallelization_increase: number;
  queue_reduction_pct: number;
  implementation_cost: number;
}

export interface SensitivityEntry {
  node_id: string;
  parameter: string;
  baseline_value: number;
  perturbed_value: number;
  metric_name: string;
  baseline_metric: number;
  perturbed_metric: number;
  absolute_impact: number;
  relative_impact_pct: number;
}

export interface SensitivityReport {
  entries: SensitivityEntry[];
  perturbation_pct: number;
}

export interface LeverageRanking {
  node_id: string;
  node_name: string;
  parameter: string;
  leverage_score: number;
  time_impact_pct: number;
  cost_impact_pct: number;
  recommendation: string;
}
