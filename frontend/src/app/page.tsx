"use client";

import { useMemo, useState } from "react";
import { InputBar } from "@/components/input-bar";
import { WorkflowGraphView } from "@/components/workflow-graph";
import { MetricsCards } from "@/components/metrics-cards";
import { NodeTable } from "@/components/node-table";
import { WhatIfPanel } from "@/components/whatif-panel";
import { AdvancedPanel } from "@/components/advanced-panel";
import { ScenarioComparisonBoard } from "@/components/scenario-comparison-board";
import { NodeInsightPanel } from "@/components/node-insight-panel";
import { DecisionSummaryStrip } from "@/components/decision-summary-strip";
import { HelpCenter } from "@/components/help-center";
import { InlineHelp } from "@/components/inline-help";
import { HelpTip } from "@/components/help-tip";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useProSim } from "@/hooks/use-prosim";
import type { LeverageRanking } from "@/lib/types";

const UI_V2_ENABLED = process.env.NEXT_PUBLIC_UI_V2 !== "0";

export default function Home() {
  const {
    workflow,
    results,
    simulating,
    error,
    volumePerHour,
    numTransactions,
    setWorkflow,
    updateWorkflow,
    setVolumePerHour,
    setNumTransactions,

    baseline,
    proposal,
    comparison,
    proposalControls,
    selectedNodeId,
    selectedNodeContext,
    setSelectedNodeId,
    setProposalTarget,
    setProposalControls,
    applyProposalIntervention,
    simulateProposalWorkflow,
    resetProposal,
  } = useProSim();

  const [searchQuery, setSearchQuery] = useState("");
  const [detailedLabels, setDetailedLabels] = useState(false);
  const [proposalJumpSignal, setProposalJumpSignal] = useState(0);
  const [proposalNotice, setProposalNotice] = useState<string | null>(null);

  const steps = useMemo(
    () => [
      {
        key: "build",
        label: "Step 1 | Build / Load",
        done: Boolean(workflow),
      },
      {
        key: "baseline",
        label: "Step 2 | Calibrate Baseline",
        done: Boolean(baseline.locked && baseline.results),
      },
      {
        key: "proposal",
        label: "Step 3 | Compare Proposal",
        done: Boolean(comparison),
      },
    ],
    [workflow, baseline.locked, baseline.results, comparison],
  );

  function optimizeBottleneck(nodeId: string) {
    const nodeName = workflow?.nodes.find((n) => n.id === nodeId)?.name ?? nodeId;
    setSelectedNodeId(nodeId);
    setProposalTarget(nodeId);
    setProposalControls({
      targetId: nodeId,
      timeReductionPct: 20,
      costReductionPct: 10,
      errorReductionPct: 5,
    });
    setProposalNotice(`Loaded optimization preset for ${nodeName}. Review Proposal Builder and click Compare Proposal.`);
    setProposalJumpSignal((s) => s + 1);
  }

  function applyNodePreset(patch: Partial<typeof proposalControls>) {
    if (patch.targetId) {
      setSelectedNodeId(patch.targetId);
      setProposalTarget(patch.targetId);
    }
    setProposalControls(patch);
  }

  function applyLeverageRecommendation(ranking: LeverageRanking) {
    const patch: Partial<typeof proposalControls> = { targetId: ranking.node_id };

    if (ranking.parameter.includes("time") || ranking.parameter.includes("queue")) {
      patch.timeReductionPct = 25;
      patch.costReductionPct = 10;
      patch.errorReductionPct = 10;
    } else if (ranking.parameter.includes("cost")) {
      patch.timeReductionPct = 10;
      patch.costReductionPct = 25;
      patch.errorReductionPct = 5;
    } else {
      patch.timeReductionPct = 15;
      patch.costReductionPct = 10;
      patch.errorReductionPct = 20;
    }

    applyNodePreset(patch);
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b border-border bg-background/85 backdrop-blur-lg">
        <div className="mx-auto flex max-w-[1700px] flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold tracking-tight text-text">ProSim</h1>
            <span className="hidden text-xs text-text-dim md:inline">Decision Cockpit</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {steps.map((step) => (
              <span
                key={step.key}
                className={`rounded-full border px-2.5 py-1 ${
                  step.done
                    ? "border-success/40 bg-success/15 text-success"
                    : "border-border bg-surface/40 text-text-dim"
                }`}
              >
                {step.label}
              </span>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 whitespace-nowrap text-xs text-text-muted">
                Vol/hr
                <HelpTip text="Input demand rate. Higher volume increases pressure on queueing and throughput constraints." />
              </label>
              <Input
                type="number"
                value={volumePerHour}
                onChange={(e) => setVolumePerHour(parseFloat(e.target.value) || 100)}
                className="h-8 w-24 text-xs"
                min={0.1}
                step={10}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 whitespace-nowrap text-xs text-text-muted">
                Txns
                <HelpTip text="Number of transactions simulated per run. Larger values improve stability but can be slower." />
              </label>
              <Input
                type="number"
                value={numTransactions}
                onChange={(e) => setNumTransactions(parseInt(e.target.value, 10) || 10_000)}
                className="h-8 w-28 text-xs"
                min={100}
                step={1000}
              />
            </div>
            {simulating ? (
              <div className="flex items-center gap-1.5 text-xs text-accent-bright">
                <div className="h-2 w-2 animate-pulse rounded-full bg-accent" />
                Baseline simulating
              </div>
            ) : null}
            <HelpCenter />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1700px] space-y-5 px-4 py-5">
        <InputBar onWorkflowLoaded={setWorkflow} />

        {UI_V2_ENABLED ? (
          <DecisionSummaryStrip
            baseline={baseline}
            proposal={proposal}
            volumePerHour={volumePerHour}
            numTransactions={numTransactions}
          />
        ) : null}

        {error ? (
          <div className="rounded-lg border border-error/20 bg-error/10 px-4 py-3 text-sm text-error">
            {error}
          </div>
        ) : null}

        {!workflow ? (
          <div className="rounded-xl border border-border bg-surface/30 py-24 text-center">
            <p className="text-lg text-text-dim">
              Describe a process above and generate a baseline, or upload a workflow JSON.
            </p>
          </div>
        ) : UI_V2_ENABLED ? (
          <>
            <section className="relative z-0 grid grid-cols-1 gap-5 overflow-hidden xl:grid-cols-7">
              <div className="min-w-0 space-y-3 xl:col-span-4">
                <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface/40 p-2.5">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search nodes by name or id"
                    className="h-8 max-w-sm"
                  />
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setDetailedLabels((v) => !v)}
                  >
                    {detailedLabels ? "Compact labels" : "Detailed labels"}
                  </Button>
                  <div className="basis-full">
                    <InlineHelp title="Workflow Graph Help">
                      Click any node to inspect details and quick actions on the right panel.
                      Use search to focus specific nodes. Toggle detailed labels to show
                      time/cost/utilization in the graph cards.
                    </InlineHelp>
                  </div>
                </div>

                <WorkflowGraphView
                  workflow={workflow}
                  results={results}
                  loading={simulating}
                  selectedNodeId={selectedNodeId}
                  searchQuery={searchQuery}
                  detailedLabels={detailedLabels}
                  onSelectNode={setSelectedNodeId}
                />
              </div>

              <div className="min-w-0 space-y-3 xl:col-span-3">
                <MetricsCards
                  baselineResults={baseline.results}
                  proposalResults={proposal.results}
                  comparison={comparison}
                  onOptimizeBottleneck={optimizeBottleneck}
                />
                <NodeInsightPanel
                  context={selectedNodeContext}
                  onApplyPreset={applyNodePreset}
                />
              </div>
            </section>

            {results ? (
              <section className="relative z-10 mt-2 space-y-4">
                <ScenarioComparisonBoard
                  comparison={comparison}
                  proposalStatus={proposal.status}
                  proposalError={proposal.error}
                />
                <WhatIfPanel
                  workflow={workflow}
                  baselineResults={results}
                  proposalControls={proposalControls}
                  comparison={comparison}
                  loading={proposal.status === "simulating"}
                  error={proposal.error}
                  onTargetChange={setProposalTarget}
                  onControlsChange={setProposalControls}
                  onApply={() => void applyProposalIntervention()}
                  onReset={resetProposal}
                  onRunFullSimulation={() => void simulateProposalWorkflow()}
                  focusSignal={proposalJumpSignal}
                  notice={proposalNotice}
                  onClearNotice={() => setProposalNotice(null)}
                />
              </section>
            ) : null}

            <section>
              <NodeTable
                workflow={workflow}
                onParamsChanged={updateWorkflow}
                selectedNodeId={selectedNodeId}
                onSelectNode={setSelectedNodeId}
                searchQuery={searchQuery}
              />
            </section>

            {results ? (
              <section>
                <AdvancedPanel
                  workflow={workflow}
                  results={results}
                  volumePerHour={volumePerHour}
                  numTransactions={numTransactions}
                  onApplyRecommendation={applyLeverageRecommendation}
                />
              </section>
            ) : null}
          </>
        ) : (
          <>
            <section className="grid grid-cols-1 gap-6 lg:grid-cols-5">
              <div className="lg:col-span-3">
                <WorkflowGraphView workflow={workflow} results={results} loading={simulating} />
              </div>
              <div className="lg:col-span-2">
                <MetricsCards results={results} />
              </div>
            </section>

            <section>
              <NodeTable workflow={workflow} onParamsChanged={updateWorkflow} />
            </section>

            {results ? (
              <section>
                <WhatIfPanel
                  workflow={workflow}
                  baselineResults={results}
                  proposalControls={proposalControls}
                  comparison={comparison}
                  loading={proposal.status === "simulating"}
                  error={proposal.error}
                  onTargetChange={setProposalTarget}
                  onControlsChange={setProposalControls}
                  onApply={() => void applyProposalIntervention()}
                  onReset={resetProposal}
                  onRunFullSimulation={() => void simulateProposalWorkflow()}
                  focusSignal={proposalJumpSignal}
                  notice={proposalNotice}
                  onClearNotice={() => setProposalNotice(null)}
                />
              </section>
            ) : null}

            {results ? (
              <section>
                <AdvancedPanel
                  workflow={workflow}
                  results={results}
                  volumePerHour={volumePerHour}
                  numTransactions={numTransactions}
                />
              </section>
            ) : null}
          </>
        )}
      </main>
    </div>
  );
}
