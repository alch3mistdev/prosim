"use client";

import { Clock, DollarSign, Gauge, CheckCircle, AlertTriangle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SimulationResults } from "@/lib/types";
import { formatTime, formatCost } from "@/lib/utils";

interface MetricsCardsProps {
  results: SimulationResults | null;
}

function MetricCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-background border border-border">
      <div className="p-2 rounded-md bg-accent/10">
        <Icon className="h-4 w-4 text-accent-bright" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-text-muted uppercase tracking-wide">{label}</p>
        <p className="text-xl font-bold text-text mt-0.5 font-mono">{value}</p>
        {sub && <p className="text-xs text-text-dim mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export function MetricsCards({ results }: MetricsCardsProps) {
  if (!results) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <CardTitle>Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48 text-text-dim text-sm">
            Simulation results will appear here automatically
          </div>
        </CardContent>
      </Card>
    );
  }

  const completionPct =
    (results.completed_transactions / Math.max(results.total_transactions, 1)) * 100;

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle>Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            icon={Clock}
            label="Avg Time"
            value={formatTime(results.avg_total_time)}
            sub={`P95: ${formatTime(results.p95_total_time)}`}
          />
          <MetricCard
            icon={DollarSign}
            label="Avg Cost"
            value={formatCost(results.avg_total_cost)}
            sub={`Total: ${formatCost(results.total_cost)}`}
          />
          <MetricCard
            icon={Gauge}
            label="Throughput"
            value={`${results.throughput_per_hour.toLocaleString("en-US", { maximumFractionDigits: 0 })}/hr`}
          />
          <MetricCard
            icon={CheckCircle}
            label="Completion"
            value={`${completionPct.toFixed(1)}%`}
            sub={`${results.completed_transactions.toLocaleString()} / ${results.total_transactions.toLocaleString()}`}
          />
        </div>

        {results.bottlenecks.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-2 text-xs text-text-muted uppercase tracking-wide">
              <AlertTriangle className="h-3 w-3" />
              Top Bottlenecks
            </div>
            {results.bottlenecks.slice(0, 3).map((bn) => (
              <div
                key={bn.node_id}
                className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-background border border-border"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text truncate">{bn.node_name}</p>
                  <p className="text-xs text-text-dim">{bn.reason}</p>
                </div>
                <Badge variant="warning">{bn.time_contribution_pct.toFixed(0)}%</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
