"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronRight, Loader2, Download, Zap, BarChart3, WandSparkles } from "lucide-react";
import type { WorkflowGraph, SimulationResults, LeverageRanking } from "@/lib/types";
import { simulate, runSensitivity, rankLeverage, exportMermaid } from "@/lib/api";
import { formatCost, formatTime } from "@/lib/utils";

interface AdvancedPanelProps {
  workflow: WorkflowGraph;
  results: SimulationResults;
  volumePerHour: number;
  numTransactions: number;
  onApplyRecommendation?: (ranking: LeverageRanking) => void;
}

function Collapsible({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <button
        className="flex w-full cursor-pointer items-center gap-2 px-4 py-3 text-sm font-medium text-text-muted transition-colors hover:bg-surface-hover hover:text-text"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <Icon className="h-4 w-4" />
        <span className="flex-1 text-left">{title}</span>
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
      {open ? <div className="border-t border-border px-4 pb-4 pt-2">{children}</div> : null}
    </div>
  );
}

export function AdvancedPanel({
  workflow,
  results,
  volumePerHour,
  numTransactions,
  onApplyRecommendation,
}: AdvancedPanelProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Risk & Leverage</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <MonteCarloSection workflow={workflow} volumePerHour={volumePerHour} />
        <SensitivitySection
          workflow={workflow}
          volumePerHour={volumePerHour}
          numTransactions={numTransactions}
          onApplyRecommendation={onApplyRecommendation}
        />
        <ExportSection workflow={workflow} results={results} />
      </CardContent>
    </Card>
  );
}

function MonteCarloSection({
  workflow,
  volumePerHour,
}: {
  workflow: WorkflowGraph;
  volumePerHour: number;
}) {
  const [txCount, setTxCount] = useState(100_000);
  const [seed, setSeed] = useState(42);
  const [loading, setLoading] = useState(false);
  const [mcResults, setMcResults] = useState<SimulationResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await simulate(workflow, {
        mode: "monte_carlo",
        num_transactions: txCount,
        volume_per_hour: volumePerHour,
        seed,
      });
      setMcResults(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Monte Carlo simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Collapsible title="Monte Carlo Risk Envelope" icon={BarChart3}>
      <div className="space-y-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <label className="mb-1 block text-xs text-text-muted">Transactions</label>
            <Input
              type="number"
              value={txCount}
              onChange={(e) => setTxCount(parseInt(e.target.value, 10) || 100_000)}
              min={100}
              max={1_000_000}
              step={10_000}
            />
          </div>
          <div className="w-24">
            <label className="mb-1 block text-xs text-text-muted">Seed</label>
            <Input
              type="number"
              value={seed}
              onChange={(e) => setSeed(parseInt(e.target.value, 10) || 42)}
              min={0}
            />
          </div>
          <Button onClick={() => void run()} disabled={loading} variant="secondary" className="shrink-0">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Run"}
          </Button>
        </div>
        {error ? (
          <div className="rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
            {error}
          </div>
        ) : null}
        {mcResults ? (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
            <StatBox label="P50" value={formatTime(mcResults.p50_total_time)} />
            <StatBox label="P95" value={formatTime(mcResults.p95_total_time)} />
            <StatBox label="P99" value={formatTime(mcResults.p99_total_time)} />
            <StatBox label="Avg Cost" value={formatCost(mcResults.avg_total_cost)} />
            <StatBox label="Completed" value={mcResults.completed_transactions.toLocaleString()} />
            <StatBox label="Failed" value={mcResults.failed_transactions.toLocaleString()} />
          </div>
        ) : null}
      </div>
    </Collapsible>
  );
}

function SensitivitySection({
  workflow,
  volumePerHour,
  numTransactions,
  onApplyRecommendation,
}: {
  workflow: WorkflowGraph;
  volumePerHour: number;
  numTransactions: number;
  onApplyRecommendation?: (ranking: LeverageRanking) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [rankings, setRankings] = useState<LeverageRanking[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const sensitivity = await runSensitivity(workflow, {
        volume_per_hour: volumePerHour,
        num_transactions: numTransactions,
      });
      const ranks = await rankLeverage(workflow, sensitivity, 5);
      setRankings(ranks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sensitivity analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Collapsible title="Leverage Ranking" icon={Zap}>
      <div className="space-y-3">
        <Button onClick={() => void run()} disabled={loading} variant="secondary" className="w-full">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Run Sensitivity Analysis"}
        </Button>
        {error ? (
          <div className="rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
            {error}
          </div>
        ) : null}
        {rankings ? (
          <div className="space-y-2">
            {rankings.map((r, i) => (
              <div
                key={`${r.node_id}-${r.parameter}`}
                className="flex items-center gap-3 rounded-lg border border-border bg-background px-3 py-2"
              >
                <span className="w-5 text-xs font-bold text-accent-bright">#{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text">{r.node_name}</p>
                  <p className="text-xs text-text-dim">{r.parameter} - {r.recommendation}</p>
                </div>
                <div className="hidden gap-1.5 lg:flex">
                  <Badge variant="default">{r.time_impact_pct.toFixed(1)}% time</Badge>
                  <Badge variant="muted">{r.cost_impact_pct.toFixed(1)}% cost</Badge>
                </div>
                {onApplyRecommendation ? (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => onApplyRecommendation(r)}
                  >
                    <WandSparkles className="h-3.5 w-3.5" />
                    Apply
                  </Button>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </Collapsible>
  );
}

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9_-]/g, "_").toLowerCase() || "workflow";
}

function ExportSection({
  workflow,
  results,
}: {
  workflow: WorkflowGraph;
  results: SimulationResults;
}) {
  const [error, setError] = useState<string | null>(null);

  function downloadJSON() {
    const blob = new Blob([JSON.stringify(workflow, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${sanitizeFilename(workflow.name)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function downloadMermaid() {
    setError(null);
    try {
      const code = await exportMermaid(workflow, results);
      const blob = new Blob([code], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${sanitizeFilename(workflow.name)}.mmd`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mermaid export failed");
    }
  }

  return (
    <Collapsible title="Export Artifacts" icon={Download}>
      <div className="space-y-3">
        {error ? (
          <div className="rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
            {error}
          </div>
        ) : null}
        <div className="flex gap-3">
          <Button onClick={downloadJSON} variant="secondary" className="flex-1">
            <Download className="h-4 w-4" />
            Workflow JSON
          </Button>
          <Button onClick={() => void downloadMermaid()} variant="secondary" className="flex-1">
            <Download className="h-4 w-4" />
            Mermaid Diagram
          </Button>
        </div>
      </div>
    </Collapsible>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background p-2 text-center">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="font-mono text-sm font-bold text-text">{value}</p>
    </div>
  );
}
