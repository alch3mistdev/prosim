"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { InlineHelp } from "@/components/inline-help";
import { HelpTip } from "@/components/help-tip";
import { Loader2, Sparkles, RotateCcw } from "lucide-react";
import type {
  InterventionComparison,
  ProposalControls,
  SimulationResults,
  WorkflowGraph,
} from "@/lib/types";
import { formatCost } from "@/lib/utils";

interface WhatIfPanelProps {
  workflow: WorkflowGraph;
  baselineResults: SimulationResults;
  proposalControls: ProposalControls;
  comparison: InterventionComparison | null;
  loading?: boolean;
  error?: string | null;
  onTargetChange: (nodeId: string) => void;
  onControlsChange: (patch: Partial<ProposalControls>) => void;
  onApply: () => void;
  onReset: () => void;
  onRunFullSimulation?: () => void;
  focusSignal?: number;
  notice?: string | null;
  onClearNotice?: () => void;
}

const QUICK_PRESETS: Array<{
  label: string;
  hint: string;
  values: Partial<ProposalControls>;
}> = [
  {
    label: "Lean automation",
    hint: "Speed + cost focus",
    values: { timeReductionPct: 20, costReductionPct: 15, errorReductionPct: 5 },
  },
  {
    label: "Quality hardening",
    hint: "Reduce errors",
    values: { timeReductionPct: 10, costReductionPct: 5, errorReductionPct: 35 },
  },
  {
    label: "Throughput lift",
    hint: "Aggressive cycle-time cut",
    values: { timeReductionPct: 35, costReductionPct: 10, errorReductionPct: 10 },
  },
];

export function WhatIfPanel({
  workflow,
  baselineResults,
  proposalControls,
  comparison,
  loading,
  error,
  onTargetChange,
  onControlsChange,
  onApply,
  onReset,
  onRunFullSimulation,
  focusSignal,
  notice,
  onClearNotice,
}: WhatIfPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [flash, setFlash] = useState(false);

  const actionableNodes = workflow.nodes.filter(
    (n) => n.node_type !== "start" && n.node_type !== "end",
  );

  const hasChange =
    proposalControls.timeReductionPct > 0 ||
    proposalControls.costReductionPct > 0 ||
    proposalControls.errorReductionPct > 0;

  if (actionableNodes.length === 0) return null;

  const targetMetrics = baselineResults.node_metrics.find(
    (metric) => metric.node_id === proposalControls.targetId,
  );

  useEffect(() => {
    if (!focusSignal) return;
    setFlash(true);
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    const timer = setTimeout(() => setFlash(false), 1200);
    return () => clearTimeout(timer);
  }, [focusSignal]);

  return (
    <div ref={panelRef} className="scroll-mt-28">
      <Card className={`relative z-0 transition-shadow ${flash ? "ring-2 ring-accent/70 shadow-[0_0_0_1px_rgba(59,130,246,0.55)]" : ""}`}>
        <CardHeader className="pb-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Proposal Builder</CardTitle>
            <Badge variant={comparison ? "default" : "muted"}>
              {comparison ? "Proposal configured" : "Awaiting proposal"}
            </Badge>
          </div>
          <InlineHelp title="Proposal Builder Help">
            Choose a target node, apply reduction sliders, then click Compare Proposal.
            This estimates macro impact against baseline. Use Run full proposal sim if you
            want deterministic simulation on the modified proposal workflow.
          </InlineHelp>
        </CardHeader>
        <CardContent className="space-y-4">
          {notice ? (
            <div className="flex items-center justify-between gap-3 rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent-bright">
              <span className="min-w-0 flex-1">{notice}</span>
              {onClearNotice ? (
                <Button variant="ghost" size="sm" onClick={onClearNotice}>
                  Dismiss
                </Button>
              ) : null}
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div className="min-w-0 space-y-3 rounded-lg border border-border bg-background/60 p-3">
              <label className="block text-xs uppercase tracking-wide text-text-muted">
                Target node
              </label>
              <Select value={proposalControls.targetId} onValueChange={onTargetChange}>
                <SelectTrigger className="min-w-0">
                  <SelectValue placeholder="Select a node" />
                </SelectTrigger>
                <SelectContent
                  side="bottom"
                  align="start"
                  sideOffset={6}
                  avoidCollisions={false}
                >
                  {actionableNodes.map((n) => (
                    <SelectItem key={n.id} value={n.id}>
                      {n.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-text-muted">Quick presets</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {QUICK_PRESETS.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      className="rounded-md border border-border bg-surface/50 px-2.5 py-2 text-left transition-colors hover:border-accent/40 hover:bg-accent/10"
                      onClick={() => onControlsChange(preset.values)}
                    >
                      <p className="truncate text-sm font-medium text-text">{preset.label}</p>
                      <p className="text-xs text-text-dim">{preset.hint}</p>
                    </button>
                  ))}
                </div>
              </div>

              {targetMetrics ? (
                <div className="rounded-md border border-border bg-surface/40 p-2.5 text-xs text-text-dim">
                  Baseline node profile: {targetMetrics.avg_time.toFixed(1)}s avg time, {formatCost(targetMetrics.avg_cost)} avg cost, {(targetMetrics.utilization * 100).toFixed(0)}% utilization.
                </div>
              ) : null}
            </div>

            <div className="min-w-0 space-y-4 rounded-lg border border-border bg-background/60 p-3">
              <SliderRow
                label="Time reduction"
                helpText="Percent reduction applied to processing and queue time at the selected node."
                value={proposalControls.timeReductionPct}
                onChange={(value) => onControlsChange({ timeReductionPct: value })}
              />
              <SliderRow
                label="Cost reduction"
                helpText="Percent reduction applied to per-transaction node cost."
                value={proposalControls.costReductionPct}
                onChange={(value) => onControlsChange({ costReductionPct: value })}
              />
              <SliderRow
                label="Error reduction"
                helpText="Percent reduction applied to node-level error probability."
                value={proposalControls.errorReductionPct}
                onChange={(value) => onControlsChange({ errorReductionPct: value })}
              />
              <SliderRow
                label="Implementation cost"
                helpText="Estimated one-time investment used for ROI and payback calculations."
                value={proposalControls.implementationCost}
                onChange={(value) => onControlsChange({ implementationCost: value })}
                max={500_000}
                step={5_000}
                asCurrency
              />

              <div className="flex flex-wrap gap-2">
                <Button onClick={onApply} disabled={loading || !hasChange || !proposalControls.targetId}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  Compare Proposal
                </Button>
                <Button variant="secondary" onClick={onReset}>
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </Button>
                {onRunFullSimulation ? (
                  <Button variant="secondary" onClick={onRunFullSimulation} disabled={loading || !hasChange}>
                    Run full proposal sim
                  </Button>
                ) : null}
              </div>

              {error ? (
                <div className="rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
                  {error}
                </div>
              ) : null}
            </div>
          </div>

          {comparison ? (
            <p className="text-xs text-text-dim">
              Proposal configured. Review full KPI deltas in the <span className="font-medium text-text">Baseline vs Proposal</span> panel.
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function SliderRow({
  label,
  helpText,
  value,
  onChange,
  min = 0,
  max = 80,
  step = 5,
  asCurrency = false,
}: {
  label: string;
  helpText?: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  asCurrency?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="inline-flex items-center gap-1 text-text-muted">
          <span>{label}</span>
          {helpText ? <HelpTip text={helpText} /> : null}
        </span>
        <Badge variant={value > 0 ? "default" : "muted"} className="font-mono">
          {asCurrency ? `$${Math.round(value).toLocaleString()}` : `${value}%`}
        </Badge>
      </div>
      <Slider value={[value]} onValueChange={([v]) => onChange(v)} min={min} max={max} step={step} />
    </div>
  );
}
