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
} from "@xyflow/react";
import dagre from "@dagrejs/dagre";
import "@xyflow/react/dist/style.css";
import { Skeleton } from "@/components/ui/skeleton";
import type { WorkflowGraph, SimulationResults } from "@/lib/types";

const NODE_WIDTH = 160;
const NODE_HEIGHT = 44;

const TYPE_COLORS: Record<string, string> = {
  start: "#4CAF50",
  end: "#f44336",
  human: "#2196F3",
  api: "#FF9800",
  async: "#9C27B0",
  batch: "#607D8B",
  decision: "#FFC107",
  parallel_gateway: "#00BCD4",
  wait: "#795548",
};

const TYPE_STYLES: Record<string, { bg: string; border: string; text: string }> = {
  start: { bg: "bg-[#4CAF50]", border: "border-[#4CAF50]/60", text: "text-white" },
  end: { bg: "bg-[#f44336]", border: "border-[#f44336]/60", text: "text-white" },
  human: { bg: "bg-[#2196F3]", border: "border-[#2196F3]/60", text: "text-white" },
  api: { bg: "bg-[#FF9800]", border: "border-[#FF9800]/60", text: "text-white" },
  async: { bg: "bg-[#9C27B0]", border: "border-[#9C27B0]/60", text: "text-white" },
  batch: { bg: "bg-[#607D8B]", border: "border-[#607D8B]/60", text: "text-white" },
  decision: { bg: "bg-[#FFC107]", border: "border-[#FFC107]/60", text: "text-black" },
  parallel_gateway: { bg: "bg-[#00BCD4]", border: "border-[#00BCD4]/60", text: "text-white" },
  wait: { bg: "bg-[#795548]", border: "border-[#795548]/60", text: "text-white" },
};

function WorkflowNode({ data, selected }: NodeProps) {
  const d = data as { label: string; nodeType: string };
  const style = TYPE_STYLES[d.nodeType] ?? TYPE_STYLES.api;
  const isStart = d.nodeType === "start";
  const isEnd = d.nodeType === "end";
  const isDecision = d.nodeType === "decision";

  return (
    <div
      className={`
        px-3 py-2 rounded-lg border-2 shadow-lg transition-all min-w-[120px] max-w-[200px]
        ${style.bg} ${style.border} ${style.text}
        ${selected ? "ring-2 ring-accent ring-offset-2 ring-offset-surface" : ""}
        ${isDecision ? "transform rotate-0" : ""}
      `}
      style={
        isDecision
          ? { clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)", minWidth: 100 }
          : isStart || isEnd
            ? { borderRadius: 999 }
            : undefined
      }
    >
      {!isStart && <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-white/80" />}
      <div className="text-xs font-medium text-center truncate" title={d.label}>
        {d.label}
      </div>
      {!isEnd && <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-white/80" />}
    </div>
  );
}

const nodeTypes = { workflow: WorkflowNode };

function getLayoutedElements(
  workflow: WorkflowGraph,
  results: SimulationResults | null
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: "LR", nodesep: 40, ranksep: 60 });

  const nodeIdMap = new Map<string, string>();
  workflow.nodes.forEach((n, i) => nodeIdMap.set(n.id, `n_${n.id.replace(/[-.\s]/g, "_")}`));

  const rfNodes: Node[] = workflow.nodes.map((n) => {
    const nm = results?.node_metrics?.find((m) => m.node_id === n.id);
    let label = n.name;
    if (nm && nm.transactions_processed > 0) {
      label += ` • ${nm.avg_time.toFixed(1)}s / $${nm.avg_cost.toFixed(2)}`;
    }
    return {
      id: nodeIdMap.get(n.id) ?? n.id,
      type: "workflow",
      data: { label, nodeType: n.node_type },
      position: { x: 0, y: 0 },
    };
  });

  rfNodes.forEach((n) => dagreGraph.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
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
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    };
  });

  const rfEdges: Edge[] = workflow.edges.map((e, i) => {
    const src = nodeIdMap.get(e.source) ?? e.source;
    const tgt = nodeIdMap.get(e.target) ?? e.target;
    return {
      id: `e-${e.source}-${e.target}-${i}`,
      source: src,
      target: tgt,
      type: "smoothstep",
      animated: false,
      label: e.probability < 1 ? `${(e.probability * 100).toFixed(0)}%` : undefined,
    };
  });

  return { nodes: layoutedNodes, edges: rfEdges };
}

interface WorkflowGraphViewProps {
  workflow: WorkflowGraph | null;
  results: SimulationResults | null;
  loading?: boolean;
}

export function WorkflowGraphView({ workflow, results, loading }: WorkflowGraphViewProps) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    if (!workflow) return { nodes: [], edges: [] };
    return getLayoutedElements(workflow, results);
  }, [workflow, results]);

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
        <Skeleton className="h-[420px] w-full rounded-lg" />
      </div>
    );
  }
  if (!workflow) {
    return (
      <div className="h-full">
        <div className="pb-2 font-medium text-text">Workflow</div>
        <div className="flex items-center justify-center h-[420px] text-text-dim text-sm border border-border rounded-lg bg-surface/50">
          Generate or upload a workflow to see the diagram
        </div>
      </div>
    );
  }

  return (
    <div className="h-full">
      <div className="pb-2 font-medium text-text">Workflow</div>
      <div className="h-[420px] w-full rounded-lg border border-border overflow-hidden bg-surface/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        className="dark-theme"
      >
        <Background gap={16} size={1} color="var(--color-border)" />
        <Controls className="!bg-surface !border-border !shadow-lg" />
        <MiniMap
          className="!bg-surface !border-border"
          nodeColor={(n) => TYPE_COLORS[(n.data as { nodeType?: string }).nodeType ?? "api"] ?? "#FF9800"}
        />
        <Panel position="top-left" className="text-xs text-text-muted">
          {workflow.nodes.length} nodes · {workflow.edges.length} edges
        </Panel>
      </ReactFlow>
      </div>
    </div>
  );
}
