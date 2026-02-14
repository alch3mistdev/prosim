"use client";

import { Clock, DollarSign, Gauge, CheckCircle, AlertTriangle, ArrowRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { InterventionComparison, SimulationResults } from "@/lib/types";
import {
  formatCost,
  formatPct,
  formatRelativeDelta,
  formatThroughputPerHour,
  formatTime,
} from "@/lib/utils";

interface MetricsCardsProps {
  results?: SimulationResults | null;
  baselineResults?: SimulationResults | null;
  proposalResults?: SimulationResults | null;
  comparison?: InterventionComparison | null;
  onOptimizeBottleneck?: (nodeId: string) => void;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  sub,
  delta,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub?: string;
  delta?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-background/70 p-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-text-muted">
        <span className="rounded-md bg-accent/10 p-1.5">
          <Icon className="h-3.5 w-3.5 text-accent-bright" />
        </span>
        <span>{label}</span>
      </div>
      <p className="mt-2 font-mono text-2xl font-bold text-text">{value}</p>
      <div className="mt-1 flex items-center justify-between">
        {sub ? <p className="text-xs text-text-dim">{sub}</p> : <span />}
        {delta ? <Badge variant="default">{delta}</Badge> : null}
      </div>
    </div>
  );
}

export function MetricsCards({
  results,
  baselineResults,
  proposalResults,
  comparison,
  onOptimizeBottleneck,
}: MetricsCardsProps) {
  const baseline = baselineResults ?? results ?? null;

  if (!baseline) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle>KPI Storyboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-52 items-center justify-center text-sm text-text-dim">
            Baseline simulation metrics will appear here.
          </div>
        </CardContent>
      </Card>
    );
  }

  const completionPct =
    (baseline.completed_transactions / Math.max(baseline.total_transactions, 1)) * 100;

  const proposedTime = comparison
    ? baseline.avg_total_time * (1 - comparison.time_saved_pct / 100)
    : proposalResults?.avg_total_time ?? null;
  const proposedCost = comparison
    ? baseline.avg_total_cost * (1 - comparison.cost_saved_pct / 100)
    : proposalResults?.avg_total_cost ?? null;
  const proposedThroughput = comparison
    ? baseline.throughput_per_hour * (1 + comparison.throughput_increase_pct / 100)
    : proposalResults?.throughput_per_hour ?? null;

  const topBottleneck = baseline.bottlenecks[0];

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle>KPI Storyboard</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <MetricCard
            icon={Clock}
            label="Avg Time"
            value={formatTime(baseline.avg_total_time)}
            sub={`P95: ${formatTime(baseline.p95_total_time)}`}
            delta={
              proposedTime !== null
                ? formatRelativeDelta(proposedTime, baseline.avg_total_time)
                : undefined
            }
          />
          <MetricCard
            icon={DollarSign}
            label="Avg Cost"
            value={formatCost(baseline.avg_total_cost)}
            sub={`Total: ${formatCost(baseline.total_cost)}`}
            delta={
              proposedCost !== null
                ? formatRelativeDelta(proposedCost, baseline.avg_total_cost)
                : undefined
            }
          />
          <MetricCard
            icon={Gauge}
            label="Throughput"
            value={formatThroughputPerHour(baseline.throughput_per_hour)}
            sub={`Max: ${formatThroughputPerHour(baseline.max_throughput_per_hour)}`}
            delta={
              proposedThroughput !== null
                ? formatRelativeDelta(proposedThroughput, baseline.throughput_per_hour)
                : undefined
            }
          />
          <MetricCard
            icon={CheckCircle}
            label="Completion"
            value={`${completionPct.toFixed(1)}%`}
            sub={`${baseline.completed_transactions.toLocaleString()} / ${baseline.total_transactions.toLocaleString()}`}
            delta={comparison ? formatPct(comparison.error_reduction_pct) : undefined}
          />
        </div>

        {comparison && (
          <div className="rounded-lg border border-success/25 bg-success/10 px-3 py-2 text-sm text-success">
            Proposal impact: {formatPct(comparison.time_saved_pct)} faster, {formatPct(comparison.cost_saved_pct)} lower cost, {formatPct(comparison.throughput_increase_pct)} higher throughput.
          </div>
        )}

        {baseline.bottlenecks.length > 0 && (
          <div className="space-y-2 pt-1">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-text-muted">
              <AlertTriangle className="h-3 w-3" />
              Priority Bottlenecks
            </div>
            {baseline.bottlenecks.slice(0, 3).map((bn, idx) => (
              <div
                key={bn.node_id}
                className="flex items-center justify-between gap-2 rounded-lg border border-border bg-background px-3 py-2"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text">{bn.node_name}</p>
                  <p className="text-xs text-text-dim">{bn.reason}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={idx === 0 ? "warning" : "muted"}>{bn.time_contribution_pct.toFixed(0)}%</Badge>
                  {idx === 0 && onOptimizeBottleneck ? (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => onOptimizeBottleneck(bn.node_id)}
                    >
                      Optimize
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  ) : null}
                </div>
              </div>
            ))}
            {topBottleneck ? (
              <p className="text-xs text-text-dim">
                Recommended first action: target <span className="font-medium text-text">{topBottleneck.node_name}</span> to unlock the largest cycle-time reduction.
              </p>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
