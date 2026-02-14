"use client";

import { Badge } from "@/components/ui/badge";
import type { ScenarioState } from "@/lib/types";

interface DecisionSummaryStripProps {
  baseline: ScenarioState;
  proposal: ScenarioState;
  volumePerHour: number;
  numTransactions: number;
}

function statusVariant(status: ScenarioState["status"]): "default" | "success" | "warning" | "error" | "muted" {
  if (status === "ready") return "success";
  if (status === "simulating") return "warning";
  if (status === "error") return "error";
  return "muted";
}

function formatUpdatedAt(value: string | null): string {
  if (!value) return "Not run";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "Not run";
  return dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function DecisionSummaryStrip({
  baseline,
  proposal,
  volumePerHour,
  numTransactions,
}: DecisionSummaryStripProps) {
  return (
    <div className="rounded-xl border border-border bg-surface/60 px-4 py-3 backdrop-blur-sm">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <div className="min-w-[220px] flex-1">
          <p className="text-xs uppercase tracking-wide text-text-muted">Workflow</p>
          <p className="font-medium text-text">{baseline.workflow?.name ?? "No workflow loaded"}</p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-text-muted">Assumptions</p>
          <p className="font-mono text-text">{volumePerHour.toLocaleString()} vol/hr | {numTransactions.toLocaleString()} txns</p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={statusVariant(baseline.status)}>Baseline {baseline.status}</Badge>
          <Badge variant={statusVariant(proposal.status)}>Proposal {proposal.status}</Badge>
        </div>

        <div className="text-xs text-text-dim">
          Baseline run: {formatUpdatedAt(baseline.updatedAt)} | Proposal run: {formatUpdatedAt(proposal.updatedAt)}
        </div>
      </div>
    </div>
  );
}
