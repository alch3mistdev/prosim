"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { WorkflowGraph, SimulationResults } from "@/lib/types";
import { simulate, exportMermaid } from "@/lib/api";

interface ProSimState {
  workflow: WorkflowGraph | null;
  results: SimulationResults | null;
  mermaidCode: string | null;
  simulating: boolean;
  error: string | null;
  volumePerHour: number;
  numTransactions: number;
}

export function useProSim() {
  const [state, setState] = useState<ProSimState>({
    workflow: null,
    results: null,
    mermaidCode: null,
    simulating: false,
    error: null,
    volumePerHour: 100,
    numTransactions: 10_000,
  });

  const simDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);
  const abortRef = useRef<AbortController | null>(null);

  // Use refs to avoid stale closures in callbacks
  const latestRef = useRef(state);
  latestRef.current = state;

  const runSimulation = useCallback(
    async (wf: WorkflowGraph, volume: number, numTx: number) => {
      // Cancel any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState((s) => ({ ...s, simulating: true, error: null }));
      try {
        const [results, mermaid] = await Promise.all([
          simulate(wf, {
            mode: "deterministic",
            num_transactions: numTx,
            volume_per_hour: volume,
          }, controller.signal),
          exportMermaid(wf, undefined, false, controller.signal),
        ]);
        if (!controller.signal.aborted) {
          setState((s) => ({
            ...s,
            results,
            mermaidCode: mermaid,
            simulating: false,
          }));
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const msg = err instanceof Error ? err.message : "Simulation failed";
        setState((s) => ({
          ...s,
          simulating: false,
          error: msg.startsWith("API error") ? msg : `Workflow loaded but simulation failed: ${msg}`,
        }));
      }
    },
    [],
  );

  const setWorkflow = useCallback(
    (wf: WorkflowGraph) => {
      setState((s) => ({ ...s, workflow: wf, results: null, mermaidCode: null, error: null }));
      const { volumePerHour, numTransactions } = latestRef.current;
      runSimulation(wf, volumePerHour, numTransactions);
    },
    [runSimulation],
  );

  const updateWorkflow = useCallback(
    (wf: WorkflowGraph) => {
      setState((s) => ({ ...s, workflow: wf }));
      if (simDebounce.current) clearTimeout(simDebounce.current);
      simDebounce.current = setTimeout(() => {
        const { volumePerHour, numTransactions } = latestRef.current;
        runSimulation(wf, volumePerHour, numTransactions);
      }, 100);
    },
    [runSimulation],
  );

  const setVolumePerHour = useCallback(
    (v: number) => {
      setState((s) => ({ ...s, volumePerHour: v }));
      if (simDebounce.current) clearTimeout(simDebounce.current);
      simDebounce.current = setTimeout(() => {
        const { workflow, numTransactions } = latestRef.current;
        if (workflow) runSimulation(workflow, v, numTransactions);
      }, 200);
    },
    [runSimulation],
  );

  const setNumTransactions = useCallback(
    (n: number) => {
      setState((s) => ({ ...s, numTransactions: n }));
      if (simDebounce.current) clearTimeout(simDebounce.current);
      simDebounce.current = setTimeout(() => {
        const { workflow, volumePerHour } = latestRef.current;
        if (workflow) runSimulation(workflow, volumePerHour, n);
      }, 200);
    },
    [runSimulation],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (simDebounce.current) clearTimeout(simDebounce.current);
      abortRef.current?.abort();
    };
  }, []);

  return {
    ...state,
    setWorkflow,
    updateWorkflow,
    setVolumePerHour,
    setNumTransactions,
  };
}
