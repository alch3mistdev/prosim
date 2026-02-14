"use client";

import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import type {
  InterventionComparison,
  ProposalControls,
  ScenarioState,
  SelectedNodeContext,
  WorkflowGraph,
} from "@/lib/types";
import { intervene, simulate } from "@/lib/api";

interface ProSimState {
  baseline: ScenarioState;
  proposal: ScenarioState;
  comparison: InterventionComparison | null;
  volumePerHour: number;
  numTransactions: number;
  selectedNodeId: string | null;
  proposalControls: ProposalControls;
}

function emptyScenario(id: "baseline" | "proposal"): ScenarioState {
  return {
    id,
    workflow: null,
    results: null,
    status: "idle",
    error: null,
    locked: false,
    updatedAt: null,
  };
}

function cloneWorkflow(workflow: WorkflowGraph): WorkflowGraph {
  return JSON.parse(JSON.stringify(workflow)) as WorkflowGraph;
}

function firstActionableNodeId(workflow: WorkflowGraph | null): string {
  if (!workflow) return "";
  return (
    workflow.nodes.find((n) => n.node_type !== "start" && n.node_type !== "end")?.id ?? ""
  );
}

function applyInterventionToWorkflow(
  workflow: WorkflowGraph,
  controls: ProposalControls,
): WorkflowGraph {
  const next = cloneWorkflow(workflow);
  next.nodes = next.nodes.map((node) => {
    if (node.id !== controls.targetId) return node;

    const timeMultiplier = Math.max(0, 1 - controls.timeReductionPct / 100);
    const costMultiplier = Math.max(0, 1 - controls.costReductionPct / 100);
    const errorMultiplier = Math.max(0, 1 - controls.errorReductionPct / 100);

    return {
      ...node,
      params: {
        ...node.params,
        exec_time_mean: node.params.exec_time_mean * timeMultiplier,
        queue_delay_mean: node.params.queue_delay_mean * timeMultiplier,
        cost_per_transaction: node.params.cost_per_transaction * costMultiplier,
        error_rate: Math.max(0, Math.min(1, node.params.error_rate * errorMultiplier)),
      },
    };
  });
  return next;
}

export function useProSim() {
  const [state, setState] = useState<ProSimState>({
    baseline: emptyScenario("baseline"),
    proposal: emptyScenario("proposal"),
    comparison: null,
    volumePerHour: 100,
    numTransactions: 10_000,
    selectedNodeId: null,
    proposalControls: {
      targetId: "",
      timeReductionPct: 0,
      costReductionPct: 0,
      errorReductionPct: 0,
      implementationCost: 0,
    },
  });

  const simDebounce = useRef<ReturnType<typeof setTimeout>>(undefined);
  const baselineAbortRef = useRef<AbortController | null>(null);
  const proposalAbortRef = useRef<AbortController | null>(null);

  const latestRef = useRef(state);
  latestRef.current = state;

  const runBaselineSimulation = useCallback(
    async (workflow: WorkflowGraph, volumePerHour: number, numTransactions: number) => {
      baselineAbortRef.current?.abort();
      const controller = new AbortController();
      baselineAbortRef.current = controller;

      setState((s) => ({
        ...s,
        baseline: {
          ...s.baseline,
          status: "simulating",
          error: null,
        },
      }));

      try {
        const results = await simulate(
          workflow,
          {
            mode: "deterministic",
            num_transactions: numTransactions,
            volume_per_hour: volumePerHour,
          },
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setState((s) => ({
            ...s,
            baseline: {
              ...s.baseline,
              results,
              status: "ready",
              error: null,
              locked: true,
              updatedAt: new Date().toISOString(),
            },
          }));
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        const msg = err instanceof Error ? err.message : "Simulation failed";
        setState((s) => ({
          ...s,
          baseline: {
            ...s.baseline,
            status: "error",
            error: msg.startsWith("API error")
              ? msg
              : `Workflow loaded but simulation failed: ${msg}`,
          },
        }));
      }
    },
    [],
  );

  const loadWorkflow = useCallback(
    (workflow: WorkflowGraph) => {
      const cloned = cloneWorkflow(workflow);
      const targetId = firstActionableNodeId(workflow);
      setState((s) => ({
        ...s,
        baseline: {
          ...emptyScenario("baseline"),
          workflow,
        },
        proposal: {
          ...emptyScenario("proposal"),
          workflow: cloned,
        },
        comparison: null,
        selectedNodeId: targetId || null,
        proposalControls: {
          ...s.proposalControls,
          targetId,
          timeReductionPct: 0,
          costReductionPct: 0,
          errorReductionPct: 0,
          implementationCost: 0,
        },
      }));
      const { volumePerHour, numTransactions } = latestRef.current;
      runBaselineSimulation(workflow, volumePerHour, numTransactions);
    },
    [runBaselineSimulation],
  );

  const updateBaselineWorkflow = useCallback(
    (workflow: WorkflowGraph) => {
      const targetId =
        workflow.nodes.some((n) => n.id === latestRef.current.proposalControls.targetId)
          ? latestRef.current.proposalControls.targetId
          : firstActionableNodeId(workflow);

      setState((s) => ({
        ...s,
        baseline: {
          ...s.baseline,
          workflow,
          status: "idle",
          error: null,
        },
        proposal: {
          ...s.proposal,
          workflow: cloneWorkflow(workflow),
          results: null,
          status: "idle",
          error: null,
        },
        comparison: null,
        selectedNodeId: s.selectedNodeId && workflow.nodes.some((n) => n.id === s.selectedNodeId)
          ? s.selectedNodeId
          : targetId || null,
        proposalControls: {
          ...s.proposalControls,
          targetId,
        },
      }));

      if (simDebounce.current) clearTimeout(simDebounce.current);
      simDebounce.current = setTimeout(() => {
        const { volumePerHour, numTransactions } = latestRef.current;
        runBaselineSimulation(workflow, volumePerHour, numTransactions);
      }, 180);
    },
    [runBaselineSimulation],
  );

  const scheduleBaselineSimulation = useCallback(
    (volumePerHour: number, numTransactions: number) => {
      if (simDebounce.current) clearTimeout(simDebounce.current);
      simDebounce.current = setTimeout(() => {
        const workflow = latestRef.current.baseline.workflow;
        if (workflow) runBaselineSimulation(workflow, volumePerHour, numTransactions);
      }, 220);
    },
    [runBaselineSimulation],
  );

  const setVolumePerHour = useCallback(
    (volumePerHour: number) => {
      setState((s) => ({ ...s, volumePerHour }));
      scheduleBaselineSimulation(volumePerHour, latestRef.current.numTransactions);
    },
    [scheduleBaselineSimulation],
  );

  const setNumTransactions = useCallback(
    (numTransactions: number) => {
      setState((s) => ({ ...s, numTransactions }));
      scheduleBaselineSimulation(latestRef.current.volumePerHour, numTransactions);
    },
    [scheduleBaselineSimulation],
  );

  const setSelectedNodeId = useCallback((selectedNodeId: string | null) => {
    setState((s) => ({ ...s, selectedNodeId }));
  }, []);

  const setProposalTarget = useCallback((targetId: string) => {
    setState((s) => ({
      ...s,
      selectedNodeId: targetId,
      proposalControls: {
        ...s.proposalControls,
        targetId,
      },
    }));
  }, []);

  const setProposalControls = useCallback((patch: Partial<ProposalControls>) => {
    setState((s) => ({
      ...s,
      proposalControls: {
        ...s.proposalControls,
        ...patch,
      },
    }));
  }, []);

  const applyProposalIntervention = useCallback(async () => {
    proposalAbortRef.current?.abort();
    const controller = new AbortController();
    proposalAbortRef.current = controller;

    const {
      baseline,
      proposalControls,
      volumePerHour,
      numTransactions,
    } = latestRef.current;

    if (!baseline.workflow || !baseline.results || !proposalControls.targetId) {
      return;
    }

    const hasChange =
      proposalControls.timeReductionPct > 0 ||
      proposalControls.costReductionPct > 0 ||
      proposalControls.errorReductionPct > 0;

    if (!hasChange) {
      setState((s) => ({
        ...s,
        comparison: null,
        proposal: {
          ...s.proposal,
          status: "idle",
          error: null,
          workflow: s.baseline.workflow ? cloneWorkflow(s.baseline.workflow) : s.proposal.workflow,
          results: null,
        },
      }));
      return;
    }

    setState((s) => ({
      ...s,
      proposal: {
        ...s.proposal,
        status: "simulating",
        error: null,
      },
    }));

    try {
      const comparison = await intervene(
        baseline.workflow,
        [
          {
            node_id: proposalControls.targetId,
            time_reduction_pct: proposalControls.timeReductionPct,
            cost_reduction_pct: proposalControls.costReductionPct,
            error_reduction_pct: proposalControls.errorReductionPct,
            implementation_cost: proposalControls.implementationCost,
            capacity_increase_pct: 0,
            parallelization_increase: 0,
            queue_reduction_pct: 0,
          },
        ],
        baseline.results,
        {
          volume_per_hour: volumePerHour,
          num_transactions: numTransactions,
        },
        controller.signal,
      );

      if (!controller.signal.aborted) {
        const proposedWorkflow = applyInterventionToWorkflow(
          baseline.workflow,
          proposalControls,
        );
        setState((s) => ({
          ...s,
          comparison,
          proposal: {
            ...s.proposal,
            workflow: proposedWorkflow,
            status: "ready",
            error: null,
            locked: true,
            updatedAt: new Date().toISOString(),
          },
        }));
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Intervention failed";
      setState((s) => ({
        ...s,
        proposal: {
          ...s.proposal,
          status: "error",
          error: msg,
        },
      }));
    }
  }, []);

  const simulateProposalWorkflow = useCallback(async () => {
    proposalAbortRef.current?.abort();
    const controller = new AbortController();
    proposalAbortRef.current = controller;

    const { proposal, volumePerHour, numTransactions } = latestRef.current;
    if (!proposal.workflow) return;

    setState((s) => ({
      ...s,
      proposal: {
        ...s.proposal,
        status: "simulating",
        error: null,
      },
    }));

    try {
      const results = await simulate(
        proposal.workflow,
        {
          mode: "deterministic",
          num_transactions: numTransactions,
          volume_per_hour: volumePerHour,
        },
        controller.signal,
      );

      if (!controller.signal.aborted) {
        setState((s) => ({
          ...s,
          proposal: {
            ...s.proposal,
            results,
            status: "ready",
            error: null,
            updatedAt: new Date().toISOString(),
          },
        }));
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      const msg = err instanceof Error ? err.message : "Proposal simulation failed";
      setState((s) => ({
        ...s,
        proposal: {
          ...s.proposal,
          status: "error",
          error: msg,
        },
      }));
    }
  }, []);

  const resetProposal = useCallback(() => {
    setState((s) => ({
      ...s,
      proposal: {
        ...s.proposal,
        workflow: s.baseline.workflow ? cloneWorkflow(s.baseline.workflow) : null,
        results: null,
        status: "idle",
        error: null,
        locked: false,
      },
      comparison: null,
      proposalControls: {
        ...s.proposalControls,
        timeReductionPct: 0,
        costReductionPct: 0,
        errorReductionPct: 0,
        implementationCost: 0,
      },
    }));
  }, []);

  const selectedNodeContext = useMemo<SelectedNodeContext>(() => {
    const workflow = state.baseline.workflow;
    const results = state.baseline.results;
    const selectedNodeId = state.selectedNodeId;

    if (!workflow || !selectedNodeId) {
      return {
        node: null,
        metrics: null,
        bottleneck: null,
        recommendations: [],
      };
    }

    const node = workflow.nodes.find((n) => n.id === selectedNodeId) ?? null;
    const metrics = results?.node_metrics.find((m) => m.node_id === selectedNodeId) ?? null;
    const bottleneck = results?.bottlenecks.find((b) => b.node_id === selectedNodeId) ?? null;
    const recommendations = [
      metrics && metrics.utilization > 0.8
        ? "High utilization: increase parallel workers or reduce queue delay."
        : null,
      metrics && metrics.avg_time > 60
        ? "Execution time is high: prioritize time reduction interventions."
        : null,
      metrics && metrics.avg_cost > 10
        ? "Cost per transaction is elevated: evaluate automation or API alternatives."
        : null,
    ].filter((v): v is string => Boolean(v));

    return { node, metrics, bottleneck, recommendations };
  }, [state.baseline.workflow, state.baseline.results, state.selectedNodeId]);

  useEffect(() => {
    return () => {
      if (simDebounce.current) clearTimeout(simDebounce.current);
      baselineAbortRef.current?.abort();
      proposalAbortRef.current?.abort();
    };
  }, []);

  return {
    baseline: state.baseline,
    proposal: state.proposal,
    comparison: state.comparison,
    volumePerHour: state.volumePerHour,
    numTransactions: state.numTransactions,
    selectedNodeId: state.selectedNodeId,
    selectedNodeContext,
    proposalControls: state.proposalControls,
    setWorkflow: loadWorkflow,
    updateWorkflow: updateBaselineWorkflow,
    setVolumePerHour,
    setNumTransactions,
    setSelectedNodeId,
    setProposalTarget,
    setProposalControls,
    applyProposalIntervention,
    simulateProposalWorkflow,
    resetProposal,

    // Backward-compatible aliases for existing fallback layout.
    workflow: state.baseline.workflow,
    results: state.baseline.results,
    simulating: state.baseline.status === "simulating",
    error: state.baseline.error,
  };
}
