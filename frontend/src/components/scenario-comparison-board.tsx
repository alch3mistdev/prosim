"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { InterventionComparison } from "@/lib/types";
import { formatCost, formatPct } from "@/lib/utils";

interface ScenarioComparisonBoardProps {
  comparison: InterventionComparison | null;
  proposalStatus: "idle" | "simulating" | "ready" | "error";
  proposalError?: string | null;
}

export function ScenarioComparisonBoard({
  comparison,
  proposalStatus,
  proposalError,
}: ScenarioComparisonBoardProps) {
  return (
    <Card className="relative z-10 min-w-0">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Baseline vs Proposal</CardTitle>
          <Badge variant={proposalStatus === "ready" ? "default" : "muted"}>
            {proposalStatus === "ready" ? "Compared" : proposalStatus}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {proposalError ? (
          <div className="rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
            {proposalError}
          </div>
        ) : null}

        {!comparison ? (
          <div className="rounded-lg border border-border bg-background/60 px-3 py-8 text-center text-sm text-text-dim">
            Build a proposal and click <span className="font-medium text-text">Compare Proposal</span> to generate executive-ready deltas.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-2">
              <DeltaTile label="Time saved" value={formatPct(comparison.time_saved_pct)} good />
              <DeltaTile label="Cost saved" value={formatPct(comparison.cost_saved_pct)} good />
              <DeltaTile label="Throughput" value={formatPct(comparison.throughput_increase_pct)} good />
              <DeltaTile label="Error reduction" value={formatPct(comparison.error_reduction_pct)} good />
            </div>

            <div className="rounded-lg border border-success/20 bg-success/10 px-3 py-2 text-sm text-success">
              Annual value unlocked: <span className="font-semibold">{formatCost(comparison.annual_cost_savings)}</span>
            </div>

            <div className="rounded-lg border border-border bg-background/50 px-3 py-2 text-sm text-text-dim">
              Stakeholder readout: this proposal is expected to improve cycle time by <span className="font-medium text-text">{formatPct(comparison.time_saved_pct)}</span>, reduce unit cost by <span className="font-medium text-text">{formatPct(comparison.cost_saved_pct)}</span>, and increase flow capacity by <span className="font-medium text-text">{formatPct(comparison.throughput_increase_pct)}</span>.
            </div>

            {(comparison.roi_ratio !== null || comparison.payback_months !== null) ? (
              <p className="text-xs text-text-dim">
                {comparison.roi_ratio !== null ? `ROI ${comparison.roi_ratio.toFixed(2)}x` : "ROI n/a"}
                {comparison.payback_months !== null
                  ? ` | Payback ${comparison.payback_months.toFixed(1)} months`
                  : ""}
              </p>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DeltaTile({
  label,
  value,
  good,
}: {
  label: string;
  value: string;
  good?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-background px-3 py-2">
      <p className="text-xs uppercase tracking-wide text-text-muted">{label}</p>
      <p className={`mt-1 font-mono text-lg font-bold ${good ? "text-success" : "text-text"}`}>{value}</p>
    </div>
  );
}
