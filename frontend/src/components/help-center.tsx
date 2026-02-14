"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, CircleHelp, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createPortal } from "react-dom";

const GLOSSARY: Array<{ term: string; description: string }> = [
  {
    term: "Deterministic simulation",
    description:
      "Calculates expected outcomes from average values. Fast and useful for baseline planning.",
  },
  {
    term: "Monte Carlo simulation",
    description:
      "Runs many randomized transactions to estimate uncertainty, percentiles (P95/P99), and risk tails.",
  },
  {
    term: "Bottleneck",
    description:
      "A node that disproportionately drives cycle time, queueing, or utilization pressure.",
  },
  {
    term: "Sensitivity analysis",
    description:
      "Measures how much each parameter change affects system-level metrics.",
  },
  {
    term: "Leverage ranking",
    description:
      "Prioritized list of node/parameter combinations most likely to improve outcomes.",
  },
  {
    term: "Proposal comparison",
    description:
      "Before/after estimate against the baseline using configured intervention reductions.",
  },
];

const PARAMETER_HELP: Array<{ name: string; meaning: string }> = [
  {
    name: "Time (exec_time_mean)",
    meaning: "Average processing time at the node, before queueing and retries.",
  },
  {
    name: "Queue (queue_delay_mean)",
    meaning: "Average wait time before processing starts.",
  },
  {
    name: "Cost (cost_per_transaction)",
    meaning: "Average direct cost each time a transaction is handled at this node.",
  },
  {
    name: "Error % (error_rate)",
    meaning: "Probability that a transaction fails at this node.",
  },
  {
    name: "Workers (parallelization_factor)",
    meaning: "Parallel capacity multiplier. Higher values can reduce effective cycle time.",
  },
  {
    name: "Retries / Retry delay",
    meaning: "How many recovery attempts happen and how long each retry waits.",
  },
];

export function HelpCenter() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [open]);

  const quickSteps = useMemo(
    () => [
      "Describe or upload a process to create a baseline.",
      "Review KPI Storyboard and Priority Bottlenecks.",
      "Click Optimize or open Proposal Builder and configure reductions.",
      "Click Compare Proposal to estimate macro impact.",
      "Use Risk & Leverage for Monte Carlo and sensitivity checks.",
    ],
    [],
  );

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
        <CircleHelp className="h-4 w-4" />
        Help
      </Button>

      {open && mounted
        ? createPortal(
            <div className="fixed inset-0 z-[100]">
              <button
                type="button"
                className="absolute inset-0 bg-black/45 backdrop-blur-[1px]"
                onClick={() => setOpen(false)}
                aria-label="Close help center"
              />
              <aside className="absolute right-0 top-0 h-full w-full max-w-[560px] overflow-y-auto border-l border-border bg-[#0b1322]/98 px-4 py-4 shadow-2xl">
                <div className="mb-4 flex items-center justify-between gap-3 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-accent-bright" />
                    <h2 className="text-base font-semibold text-text">How To Use ProSim</h2>
                  </div>
                  <Button size="icon" variant="ghost" onClick={() => setOpen(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                <section className="space-y-2 rounded-lg border border-border bg-background/40 p-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Quick Start</h3>
                  <ol className="list-decimal space-y-1 pl-4 text-sm text-text-dim">
                    {quickSteps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>

                <section className="mt-4 space-y-2 rounded-lg border border-border bg-background/40 p-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Key Terms</h3>
                  <div className="space-y-2">
                    {GLOSSARY.map((item) => (
                      <div key={item.term} className="rounded-md border border-border/80 bg-surface/40 px-2.5 py-2">
                        <p className="text-sm font-medium text-text">{item.term}</p>
                        <p className="text-xs text-text-dim">{item.description}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="mt-4 space-y-2 rounded-lg border border-border bg-background/40 p-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Parameter Guide</h3>
                  <div className="space-y-2">
                    {PARAMETER_HELP.map((item) => (
                      <div key={item.name} className="rounded-md border border-border/80 bg-surface/40 px-2.5 py-2">
                        <p className="text-sm font-medium text-text">{item.name}</p>
                        <p className="text-xs text-text-dim">{item.meaning}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="mt-4 rounded-lg border border-accent/30 bg-accent/10 p-3 text-xs text-accent-bright">
                  Tip: Every major panel also includes a local help box with panel-specific guidance.
                </section>
              </aside>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
