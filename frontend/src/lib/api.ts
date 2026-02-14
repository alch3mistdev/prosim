/* Typed API client for ProSim FastAPI backend. */

import type {
  InterventionComparison,
  LeverageRanking,
  SensitivityReport,
  SimulationResults,
  WorkflowGraph,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function post<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (typeof json.detail === "string") detail = json.detail;
    } catch {
      /* use raw text */
    }
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

/** Generate a workflow from a natural-language description via Claude API. */
export async function generateWorkflow(
  description: string,
  opts?: { max_nodes?: number },
  signal?: AbortSignal,
): Promise<WorkflowGraph> {
  return post<WorkflowGraph>(
    "/workflow/generate",
    { description, max_nodes: opts?.max_nodes ?? undefined },
    signal,
  );
}

/** Validate and normalise an uploaded workflow JSON. */
export async function parseWorkflow(
  data: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<WorkflowGraph> {
  return post<WorkflowGraph>("/workflow/parse", { data }, signal);
}

/** Run deterministic or Monte Carlo simulation. */
export async function simulate(
  workflow: WorkflowGraph,
  opts: {
    mode?: "deterministic" | "monte_carlo";
    num_transactions?: number;
    volume_per_hour?: number;
    seed?: number;
  } = {},
  signal?: AbortSignal,
): Promise<SimulationResults> {
  return post<SimulationResults>(
    "/simulate",
    {
      workflow,
      mode: opts.mode ?? "deterministic",
      num_transactions: opts.num_transactions ?? 10_000,
      volume_per_hour: opts.volume_per_hour ?? 100,
      seed: opts.seed ?? 42,
    },
    signal,
  );
}

/** Run sensitivity analysis. */
export async function runSensitivity(
  workflow: WorkflowGraph,
  opts: {
    volume_per_hour?: number;
    num_transactions?: number;
    perturbation_pct?: number;
  } = {},
  signal?: AbortSignal,
): Promise<SensitivityReport> {
  return post<SensitivityReport>(
    "/sensitivity",
    {
      workflow,
      volume_per_hour: opts.volume_per_hour ?? 100,
      num_transactions: opts.num_transactions ?? 10_000,
      perturbation_pct: opts.perturbation_pct ?? 10,
    },
    signal,
  );
}

/** Apply interventions and return before/after comparison. */
export async function intervene(
  workflow: WorkflowGraph,
  interventions: { node_id: string; [key: string]: unknown }[],
  baselineResults: SimulationResults,
  opts: { volume_per_hour?: number; num_transactions?: number } = {},
  signal?: AbortSignal,
): Promise<InterventionComparison> {
  return post<InterventionComparison>(
    "/intervene",
    {
      workflow,
      interventions,
      baseline_results: baselineResults,
      volume_per_hour: opts.volume_per_hour ?? 100,
      num_transactions: opts.num_transactions ?? 10_000,
    },
    signal,
  );
}

/** Rank nodes by improvement leverage. */
export async function rankLeverage(
  workflow: WorkflowGraph,
  sensitivity: SensitivityReport,
  topN = 10,
): Promise<LeverageRanking[]> {
  return post<LeverageRanking[]>("/leverage", {
    workflow,
    sensitivity,
    top_n: topN,
  });
}

/** Generate Mermaid diagram code. */
export async function exportMermaid(
  workflow: WorkflowGraph,
  results?: SimulationResults,
  showMetrics = true,
  signal?: AbortSignal,
): Promise<string> {
  const resp = await post<{ mermaid: string }>(
    "/export/mermaid",
    {
      workflow,
      results: results ?? null,
      show_metrics: showMetrics,
    },
    signal,
  );
  return resp.mermaid;
}
