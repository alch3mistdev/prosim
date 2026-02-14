"use client";

import { InputBar } from "@/components/input-bar";
import { WorkflowDiagram } from "@/components/workflow-diagram";
import { MetricsCards } from "@/components/metrics-cards";
import { NodeTable } from "@/components/node-table";
import { WhatIfPanel } from "@/components/whatif-panel";
import { AdvancedPanel } from "@/components/advanced-panel";
import { Input } from "@/components/ui/input";
import { useProSim } from "@/hooks/use-prosim";

export default function Home() {
  const {
    workflow,
    results,
    mermaidCode,
    simulating,
    error,
    volumePerHour,
    numTransactions,
    setWorkflow,
    updateWorkflow,
    setVolumePerHour,
    setNumTransactions,
  } = useProSim();

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-text tracking-tight">ProSim</h1>
            <span className="text-xs text-text-dim hidden sm:inline">Workflow Simulation</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs text-text-muted whitespace-nowrap">Vol/hr</label>
              <Input
                type="number"
                value={volumePerHour}
                onChange={(e) => setVolumePerHour(parseFloat(e.target.value) || 100)}
                className="w-24 h-8 text-xs"
                min={0.1}
                step={10}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-text-muted whitespace-nowrap">Txns</label>
              <Input
                type="number"
                value={numTransactions}
                onChange={(e) => setNumTransactions(parseInt(e.target.value) || 10_000)}
                className="w-28 h-8 text-xs"
                min={100}
                step={1000}
              />
            </div>
            {simulating && (
              <div className="flex items-center gap-1.5 text-xs text-accent">
                <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                Simulating
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1600px] mx-auto px-4 py-6 space-y-6">
        {/* Zone 1: Input Bar */}
        <section>
          <InputBar onWorkflowLoaded={setWorkflow} />
        </section>

        {error && (
          <div className="text-sm text-error bg-error/10 border border-error/20 rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        {!workflow ? (
          <div className="text-center py-20">
            <p className="text-text-dim text-lg">
              Describe a business process above and click <strong className="text-text">Generate</strong>, or upload a workflow JSON file.
            </p>
          </div>
        ) : (
          <>
            {/* Zone 2: Diagram + Metrics */}
            <section className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3">
                <WorkflowDiagram mermaidCode={mermaidCode} loading={simulating && !mermaidCode} />
              </div>
              <div className="lg:col-span-2">
                <MetricsCards results={results} />
              </div>
            </section>

            {/* Zone 3: Node Table */}
            <section>
              <NodeTable workflow={workflow} onParamsChanged={updateWorkflow} />
            </section>

            {/* Zone 4: What-If */}
            {results && (
              <section>
                <WhatIfPanel
                  workflow={workflow}
                  results={results}
                  volumePerHour={volumePerHour}
                  numTransactions={numTransactions}
                />
              </section>
            )}

            {/* Zone 5: Advanced */}
            {results && (
              <section>
                <AdvancedPanel
                  workflow={workflow}
                  results={results}
                  volumePerHour={volumePerHour}
                  numTransactions={numTransactions}
                />
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
