"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ProposalControls, SelectedNodeContext } from "@/lib/types";
import { formatCost, formatTime } from "@/lib/utils";

interface NodeInsightPanelProps {
  context: SelectedNodeContext;
  onApplyPreset: (patch: Partial<ProposalControls>) => void;
}

export function NodeInsightPanel({ context, onApplyPreset }: NodeInsightPanelProps) {
  if (!context.node) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Node Insight</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-text-dim">
          Select a node in the graph or table to inspect metrics and intervention options.
        </CardContent>
      </Card>
    );
  }

  const { node, metrics, bottleneck, recommendations } = context;

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex min-w-0 items-center justify-between gap-2">
          <CardTitle className="truncate">{node.name}</CardTitle>
          <Badge variant={bottleneck ? "warning" : "muted"}>{node.node_type}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <Stat label="Avg time" value={formatTime(metrics.avg_time)} />
            <Stat label="Avg cost" value={formatCost(metrics.avg_cost)} />
            <Stat label="Utilization" value={`${(metrics.utilization * 100).toFixed(0)}%`} />
            <Stat label="Queue" value={formatTime(metrics.queue_time)} />
          </div>
        ) : (
          <p className="text-sm text-text-dim">No simulation metrics yet for this node.</p>
        )}

        {bottleneck ? (
          <div className="rounded-lg border border-warning/25 bg-warning/10 px-3 py-2 text-xs text-warning">
            Bottleneck: {bottleneck.reason} ({bottleneck.time_contribution_pct.toFixed(1)}% time contribution)
          </div>
        ) : null}

        {recommendations.length > 0 ? (
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wide text-text-muted">Recommendations</p>
            {recommendations.map((rec) => (
              <p key={rec} className="rounded-md border border-border bg-background/60 px-2.5 py-1.5 text-xs text-text-dim">
                {rec}
              </p>
            ))}
          </div>
        ) : null}

        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-text-muted">Quick actions</p>
          <div className="grid gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                onApplyPreset({
                  targetId: node.id,
                  timeReductionPct: 20,
                  costReductionPct: 10,
                  errorReductionPct: 5,
                })
              }
            >
              Apply 20/10/5 optimization
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                onApplyPreset({
                  targetId: node.id,
                  timeReductionPct: 35,
                  costReductionPct: 5,
                  errorReductionPct: 15,
                })
              }
            >
              Apply throughput boost
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background/60 px-2.5 py-2">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="font-mono text-sm font-bold text-text">{value}</p>
    </div>
  );
}
