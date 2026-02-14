"use client";

import { useState, useCallback, memo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { WorkflowGraph, WorkflowNode } from "@/lib/types";

interface NodeTableProps {
  workflow: WorkflowGraph;
  onParamsChanged: (workflow: WorkflowGraph) => void;
}

interface FieldDef {
  key: string;
  label: string;
  format: (v: number) => string;
  step: number;
  pct?: boolean;
  integer?: boolean;
}

const EDITABLE_FIELDS: FieldDef[] = [
  { key: "exec_time_mean", label: "Time (s)", format: (v: number) => v.toFixed(2), step: 0.1 },
  { key: "queue_delay_mean", label: "Queue (s)", format: (v: number) => v.toFixed(2), step: 0.1 },
  { key: "cost_per_transaction", label: "Cost ($)", format: (v: number) => v.toFixed(4), step: 0.001 },
  { key: "error_rate", label: "Error %", format: (v: number) => (v * 100).toFixed(2), step: 0.01, pct: true },
  { key: "parallelization_factor", label: "Workers", format: (v: number) => v.toString(), step: 1, integer: true },
];

const TYPE_COLORS: Record<string, string> = {
  start: "success",
  end: "error",
  human: "default",
  api: "warning",
  async: "default",
  batch: "muted",
  decision: "warning",
  parallel_gateway: "default",
  wait: "muted",
};

const EditableCell = memo(function EditableCell({
  value,
  field,
  onChange,
}: {
  value: number;
  field: FieldDef;
  onChange: (newVal: number) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  const displayValue = field.format(value);

  function startEdit() {
    setDraft(field.pct ? (value * 100).toFixed(2) : value.toString());
    setEditing(true);
  }

  function commitEdit() {
    setEditing(false);
    let parsed = parseFloat(draft);
    if (isNaN(parsed)) return;
    if (field.pct) parsed = parsed / 100;
    if (field.integer) parsed = Math.max(1, Math.round(parsed));
    if (parsed < 0) parsed = 0;
    if (Math.abs(parsed - value) > 1e-9) {
      onChange(parsed);
    }
  }

  if (editing) {
    return (
      <input
        type="number"
        value={draft}
        step={field.step}
        min={0}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commitEdit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commitEdit();
          if (e.key === "Escape") setEditing(false);
        }}
        className="w-20 h-7 px-1.5 text-xs font-mono bg-background border border-accent rounded text-text text-right focus:outline-none focus:ring-1 focus:ring-accent"
        autoFocus
      />
    );
  }

  return (
    <button
      onClick={startEdit}
      className="w-20 h-7 px-1.5 text-xs font-mono text-right text-text-muted hover:text-text hover:bg-surface-hover rounded transition-colors cursor-text"
      title="Click to edit"
    >
      {displayValue}
    </button>
  );
});

export function NodeTable({ workflow, onParamsChanged }: NodeTableProps) {
  const updateNodeParam = useCallback(
    (nodeId: string, paramKey: string, newValue: number) => {
      const updated: WorkflowGraph = {
        ...workflow,
        nodes: workflow.nodes.map((n) => {
          if (n.id !== nodeId) return n;
          return {
            ...n,
            params: { ...n.params, [paramKey]: newValue },
          };
        }),
      };
      onParamsChanged(updated);
    },
    [workflow, onParamsChanged],
  );

  // Filter out start/end nodes (not editable)
  const editableNodes = workflow.nodes.filter(
    (n) => n.node_type !== "start" && n.node_type !== "end",
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Node Parameters</CardTitle>
          <span className="text-xs text-text-dim">Click any value to edit</span>
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 px-2 text-xs text-text-muted font-medium uppercase tracking-wider">
                Node
              </th>
              <th className="text-left py-2 px-2 text-xs text-text-muted font-medium uppercase tracking-wider">
                Type
              </th>
              {EDITABLE_FIELDS.map((f) => (
                <th
                  key={f.key}
                  className="text-right py-2 px-2 text-xs text-text-muted font-medium uppercase tracking-wider"
                >
                  {f.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {editableNodes.map((node) => (
              <tr
                key={node.id}
                className="border-b border-border/50 hover:bg-surface-hover/50 transition-colors"
              >
                <td className="py-2 px-2 font-medium text-text max-w-[180px] truncate">
                  {node.name}
                </td>
                <td className="py-2 px-2">
                  <Badge variant={TYPE_COLORS[node.node_type] as "default" | "success" | "warning" | "error" | "muted"}>
                    {node.node_type}
                  </Badge>
                </td>
                {EDITABLE_FIELDS.map((field) => (
                  <td key={field.key} className="py-1 px-1 text-right">
                    <EditableCell
                      value={node.params[field.key as keyof typeof node.params] as number}
                      field={field}
                      onChange={(val) => updateNodeParam(node.id, field.key, val)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
