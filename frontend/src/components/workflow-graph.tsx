"use client";

import { useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
  MarkerType,
} from "@xyflow/react";
import dagre from "@dagrejs/dagre";
import {
  Play,
  Flag,
  UserRound,
  Server,
  Clock3,
  GitBranch,
  SplitSquareVertical,
  Layers3,
  LucideIcon,
} from "lucide-react";
import "@xyflow/react/dist/style.css";
import { Skeleton } from "@/components/ui/skeleton";
import type { WorkflowGraph, SimulationResults } from "@/lib/types";

const NODE_WIDTH = 232;
const NODE_HEIGHT = 88;

const TYPE_ACCENTS: Record<string, { color: string; bg: string; label: string; icon: LucideIcon }> = {
  start: { color: "#4ade80", bg: "rgba(74,222,128,0.12)", label: "Start", icon: Play },
  end: { color: "#f87171", bg: "rgba(248,113,113,0.12)", label: "End", icon: Flag },
  human: { color: "#60a5fa", bg: "rgba(96,165,250,0.12)", label: "Human", icon: UserRound },
  api: { color: "#f59e0b", bg: "rgba(245,158,11,0.12)", label: "API", icon: Server },
  async: { color: "#22d3ee", bg: "rgba(34,211,238,0.12)", label: "Async", icon: Clock3 },
  batch: { color: "#a78bfa", bg: "rgba(167,139,250,0.12)", label: "Batch", icon: Layers3 },
  decision: { color: "#f97316", bg: "rgba(249,115,22,0.12)", label: "Decision", icon: GitBranch },
  parallel_gateway: {
    color: "#38bdf8",
    bg: "rgba(56,189,248,0.12)",
    label: "Parallel",
    icon: SplitSquareVertical,
  },
  wait: { color: "#94a3b8", bg: "rgba(148,163,184,0.12)", label: "Wait", icon: Clock3 },
};

interface WorkflowNodeData {
  nodeId: string;
  label: string;
  subtitle: string;
  nodeType: string;
  isDimmed: boolean;
  isBottleneck: boolean;
}

function WorkflowNode({ data, selected }: NodeProps) {
  const d = data as unknown as WorkflowNodeData;
  const accent = TYPE_ACCENTS[d.nodeType] ?? TYPE_ACCENTS.api;
  const Icon = accent.icon;

  return (
    <div
      className={`relative w-[232px] rounded-2xl border bg-[#0f1828]/90 p-3 shadow-[0_10px_28px_rgba(2,8,20,0.45)] transition-all ${
        selected
          ? "border-accent shadow-[0_0_0_1px_rgba(59,130,246,0.5),0_14px_32px_rgba(2,8,20,0.55)]"
          : d.isBottleneck
            ? "border-warning/70"
            : "border-border/80"
      } ${d.isDimmed ? "opacity-40" : "opacity-100"}`}
      style={{
        backgroundImage:
          "linear-gradient(155deg, rgba(59,130,246,0.08) 0%, rgba(15,24,40,0.88) 45%, rgba(15,24,40,0.98) 100%)",
      }}
    >
      <Handle type="target" position={Position.Left} className="!h-2.5 !w-2.5 !border !border-white/30 !bg-[#cbd5e1]" />

      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="inline-flex min-w-0 items-center gap-2 rounded-md border border-border/80 bg-background/40 px-2 py-1">
          <span
            className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
            style={{ backgroundColor: accent.bg, color: accent.color }}
          >
            <Icon className="h-3.5 w-3.5" />
          </span>
          <span className="truncate text-[11px] uppercase tracking-wide text-text-muted">{accent.label}</span>
        </div>

        {d.isBottleneck ? (
          <span className="rounded-full border border-warning/40 bg-warning/15 px-2 py-0.5 text-[10px] uppercase tracking-wide text-warning">
            Bottleneck
          </span>
        ) : null}
      </div>

      <p className="truncate text-sm font-semibold text-text" title={d.label}>
        {d.label}
      </p>
      <p className="mt-1 truncate font-mono text-[11px] text-text-dim" title={d.subtitle}>
        {d.subtitle}
      </p>

      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !border !border-white/30 !bg-[#cbd5e1]" />
    </div>
  );
}

const nodeTypes = { workflow: WorkflowNode };

function getLayoutedElements(
  workflow: WorkflowGraph,
  results: SimulationResults | null,
  selectedNodeId: string | null,
  searchQuery: string,
  detailedLabels: boolean,
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: "LR",
    nodesep: 42,
    ranksep: 90,
    marginx: 18,
    marginy: 12,
  });

  const nodeIdMap = new Map<string, string>();
  workflow.nodes.forEach((n) => nodeIdMap.set(n.id, `n_${n.id.replace(/[-.\s]/g, "_")}`));

  const metricByNode = new Map(results?.node_metrics.map((m) => [m.node_id, m]) ?? []);
  const bottleneckIds = getHighlightedBottleneckIds(results);
  const normalizedQuery = searchQuery.trim().toLowerCase();

  const rfNodes: Node[] = workflow.nodes.map((n) => {
    const nm = metricByNode.get(n.id);
    const subtitle = detailedLabels && nm
      ? `${nm.avg_time.toFixed(1)}s avg | $${nm.avg_cost.toFixed(2)} cost | ${Math.round(nm.utilization * 100)}% util`
      : n.description || n.id;
    const match =
      normalizedQuery.length === 0 ||
      n.name.toLowerCase().includes(normalizedQuery) ||
      n.id.toLowerCase().includes(normalizedQuery);

    return {
      id: nodeIdMap.get(n.id) ?? n.id,
      type: "workflow",
      selected: selectedNodeId === n.id,
      data: {
        nodeId: n.id,
        label: n.name,
        subtitle,
        nodeType: n.node_type,
        isDimmed: normalizedQuery.length > 0 && !match,
        isBottleneck: bottleneckIds.has(n.id),
      } satisfies WorkflowNodeData,
      position: { x: 0, y: 0 },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    };
  });

  rfNodes.forEach((n) => {
    dagreGraph.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  workflow.edges.forEach((e) => {
    const src = nodeIdMap.get(e.source) ?? e.source;
    const tgt = nodeIdMap.get(e.target) ?? e.target;
    if (dagreGraph.hasNode(src) && dagreGraph.hasNode(tgt)) dagreGraph.setEdge(src, tgt);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = rfNodes.map((node) => {
    const nodeWithPos = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPos.x - NODE_WIDTH / 2,
        y: nodeWithPos.y - NODE_HEIGHT / 2,
      },
    };
  });

  const rfEdges: Edge[] = workflow.edges.map((e, i) => {
    const src = nodeIdMap.get(e.source) ?? e.source;
    const tgt = nodeIdMap.get(e.target) ?? e.target;

    const edgeTouchesSelected = selectedNodeId !== null && (e.source === selectedNodeId || e.target === selectedNodeId);
    const edgeTouchesBottleneck = bottleneckIds.has(e.source) || bottleneckIds.has(e.target);

    const stroke = edgeTouchesSelected
      ? "rgba(96,165,250,0.92)"
      : edgeTouchesBottleneck
        ? "rgba(245,158,11,0.8)"
        : "rgba(148,163,184,0.45)";

    return {
      id: `e-${e.source}-${e.target}-${i}`,
      source: src,
      target: tgt,
      type: "bezier",
      animated: edgeTouchesSelected,
      label: e.probability < 1 ? `${(e.probability * 100).toFixed(0)}%` : undefined,
      labelStyle: {
        fill: "#cbd5e1",
        fontSize: 11,
        fontWeight: 600,
      },
      labelBgStyle: {
        fill: "rgba(10,16,28,0.95)",
        fillOpacity: 1,
        stroke: "rgba(71,85,105,0.75)",
        strokeWidth: 1,
      },
      labelBgPadding: [6, 2],
      style: {
        stroke,
        strokeWidth: edgeTouchesSelected ? 2.4 : edgeTouchesBottleneck ? 2.1 : 1.7,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 16,
        height: 16,
        color: stroke,
      },
    };
  });

  return { nodes: layoutedNodes, edges: rfEdges };
}

interface WorkflowGraphViewProps {
  workflow: WorkflowGraph | null;
  results: SimulationResults | null;
  loading?: boolean;
  selectedNodeId?: string | null;
  searchQuery?: string;
  detailedLabels?: boolean;
  onSelectNode?: (nodeId: string) => void;
}

export function WorkflowGraphView({
  workflow,
  results,
  loading,
  selectedNodeId = null,
  searchQuery = "",
  detailedLabels = false,
  onSelectNode,
}: WorkflowGraphViewProps) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    if (!workflow) return { nodes: [], edges: [] };
    return getLayoutedElements(
      workflow,
      results,
      selectedNodeId,
      searchQuery,
      detailedLabels,
    );
  }, [workflow, results, selectedNodeId, searchQuery, detailedLabels]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges]);

  if (loading && !workflow) {
    return (
      <div className="h-full">
        <div className="pb-2 font-medium text-text">Workflow</div>
        <Skeleton className="h-[470px] w-full rounded-lg" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="h-full">
        <div className="pb-2 font-medium text-text">Workflow</div>
        <div className="flex h-[470px] items-center justify-center rounded-lg border border-border bg-surface/50 text-sm text-text-dim">
          Generate or upload a workflow to see the diagram
        </div>
      </div>
    );
  }

  const topBottlenecks = getHighlightedBottleneckIds(results).size;

  return (
    <div className="h-full">
      <div className="pb-2 font-medium text-text">Workflow</div>
      <div
        className="h-[470px] w-full overflow-hidden rounded-xl border border-border/80"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 0%, rgba(59,130,246,0.12) 0, rgba(15,23,42,0) 42%), linear-gradient(180deg, rgba(9,14,24,0.95) 0%, rgba(6,10,18,0.98) 100%)",
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => {
            const nodeId = (node.data as unknown as WorkflowNodeData).nodeId;
            onSelectNode?.(nodeId);
          }}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.22 }}
          minZoom={0.25}
          maxZoom={1.8}
          proOptions={{ hideAttribution: true }}
          className="dark-theme"
        >
          <Background gap={28} size={1} color="rgba(71,85,105,0.24)" />
          <Controls className="!border-border !bg-surface !shadow-lg" showInteractive={false} />
          <MiniMap
            className="!border-border !bg-[#0b1422]/95"
            nodeStrokeWidth={2}
            nodeColor={(n) => {
              const type = (n.data as unknown as { nodeType?: string }).nodeType ?? "api";
              return TYPE_ACCENTS[type]?.color ?? TYPE_ACCENTS.api.color;
            }}
          />

          <Panel position="top-left" className="rounded-md border border-border/70 bg-[#0a1322]/80 px-2.5 py-1.5 text-xs text-text-muted backdrop-blur-sm">
            {workflow.nodes.length} nodes | {workflow.edges.length} edges
          </Panel>
          <Panel position="top-right" className="rounded-md border border-border/70 bg-[#0a1322]/80 px-2.5 py-1.5 text-xs text-text-muted backdrop-blur-sm">
            {topBottlenecks} priority bottlenecks highlighted
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
}

function getHighlightedBottleneckIds(results: SimulationResults | null): Set<string> {
  const ids = new Set<string>();
  if (!results?.bottlenecks?.length) return ids;

  const sorted = [...results.bottlenecks]
    .filter((b) => b.time_contribution_pct > 0)
    .sort((a, b) => b.time_contribution_pct - a.time_contribution_pct);
  if (sorted.length === 0) return ids;

  const leader = sorted[0];
  const relativeThreshold = Math.max(12, leader.time_contribution_pct * 0.45);

  sorted.forEach((bottleneck, index) => {
    const isLeader = index === 0;
    const isMaterialContributor = bottleneck.time_contribution_pct >= relativeThreshold;
    const isHighUtilization = bottleneck.utilization >= 0.82;
    const isSevereScore = bottleneck.score >= 0.55;

    if (isLeader || isMaterialContributor || isHighUtilization || isSevereScore) {
      ids.add(bottleneck.node_id);
    }
  });

  if (ids.size === 0) ids.add(leader.node_id);
  return ids;
}
