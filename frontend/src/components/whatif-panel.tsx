"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, TrendingUp, Minus, Loader2 } from "lucide-react";
import type { WorkflowGraph, SimulationResults, InterventionComparison } from "@/lib/types";
import { intervene } from "@/lib/api";
import { formatPct } from "@/lib/utils";

interface WhatIfPanelProps {
  workflow: WorkflowGraph;
  results: SimulationResults;
  volumePerHour: number;
  numTransactions: number;
}

function DeltaMetric({
  label,
  value,
  positive = true,
}: {
  label: string;
  value: number;
  positive?: boolean;
}) {
  const isGood = positive ? value > 0 : value < 0;
  const Icon = value > 0.1 ? TrendingUp : value < -0.1 ? TrendingDown : Minus;
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-background border border-border">
      <span className="text-sm text-text-muted">{label}</span>
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${isGood ? "text-success" : value === 0 ? "text-text-dim" : "text-error"}`} />
        <span className={`text-sm font-bold font-mono ${isGood ? "text-success" : value === 0 ? "text-text-dim" : "text-error"}`}>
          {formatPct(value)}
        </span>
      </div>
    </div>
  );
}

export function WhatIfPanel({ workflow, results, volumePerHour, numTransactions }: WhatIfPanelProps) {
  const actionableNodes = workflow.nodes.filter(
    (n) => n.node_type !== "start" && n.node_type !== "end",
  );
  const [targetId, setTargetId] = useState(actionableNodes[0]?.id ?? "");
  const [timeRed, setTimeRed] = useState(0);
  const [costRed, setCostRed] = useState(0);
  const [errorRed, setErrorRed] = useState(0);
  const [comparison, setComparison] = useState<InterventionComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Use refs for values that shouldn't trigger the effect
  const latestRef = useRef({ workflow, results, volumePerHour, numTransactions });
  latestRef.current = { workflow, results, volumePerHour, numTransactions };

  // Reset targetId and sliders when workflow changes
  const workflowId = workflow.nodes.map((n) => n.id).join(",");
  useEffect(() => {
    setTargetId(actionableNodes[0]?.id ?? "");
    setTimeRed(0);
    setCostRed(0);
    setErrorRed(0);
    setComparison(null);
    setError(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  const hasChange = timeRed > 0 || costRed > 0 || errorRed > 0;

  const runIntervention = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!hasChange || !targetId) {
      setComparison(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      const { workflow: wf, results: res, volumePerHour: vph, numTransactions: ntx } = latestRef.current;
      try {
        const result = await intervene(
          wf,
          [{
            node_id: targetId,
            time_reduction_pct: timeRed,
            cost_reduction_pct: costRed,
            error_reduction_pct: errorRed,
          }],
          res,
          { volume_per_hour: vph, num_transactions: ntx },
        );
        setComparison(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Intervention failed");
        setComparison(null);
      } finally {
        setLoading(false);
      }
    }, 150);
  }, [targetId, timeRed, costRed, errorRed, hasChange]);

  useEffect(() => {
    runIntervention();
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [runIntervention]);

  if (actionableNodes.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>What-If Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Node selector */}
          <div className="space-y-4">
            <div>
              <label className="text-xs text-text-muted uppercase tracking-wide mb-1.5 block">
                Target Node
              </label>
              <Select value={targetId} onValueChange={setTargetId}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {actionableNodes.map((n) => (
                    <SelectItem key={n.id} value={n.id}>
                      {n.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Sliders */}
          <div className="space-y-5">
            <SliderRow label="Time reduction" value={timeRed} onChange={setTimeRed} />
            <SliderRow label="Cost reduction" value={costRed} onChange={setCostRed} />
            <SliderRow label="Error reduction" value={errorRed} onChange={setErrorRed} />
          </div>

          {/* Delta metrics */}
          <div className="space-y-2">
            {error && (
              <div className="text-sm text-error bg-error/10 border border-error/20 rounded-lg px-3 py-2">
                {error}
              </div>
            )}
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-accent" />
              </div>
            )}
            {!loading && !error && comparison && (
              <>
                <DeltaMetric label="Time saved" value={comparison.time_saved_pct} />
                <DeltaMetric label="Cost saved" value={comparison.cost_saved_pct} />
                <DeltaMetric label="Throughput" value={comparison.throughput_increase_pct} />
                {comparison.annual_cost_savings > 0 && (
                  <div className="text-xs text-text-dim text-center pt-1">
                    Annual savings: <span className="text-success font-medium">${comparison.annual_cost_savings.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
                  </div>
                )}
              </>
            )}
            {!loading && !comparison && hasChange && (
              <div className="text-sm text-text-dim text-center py-8">
                Computing...
              </div>
            )}
            {!hasChange && (
              <div className="text-sm text-text-dim text-center py-8">
                Drag sliders to see impact
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SliderRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-text-muted">{label}</span>
        <Badge variant={value > 0 ? "default" : "muted"} className="font-mono">
          {value}%
        </Badge>
      </div>
      <Slider
        value={[value]}
        onValueChange={([v]) => onChange(v)}
        min={0}
        max={80}
        step={5}
      />
    </div>
  );
}
