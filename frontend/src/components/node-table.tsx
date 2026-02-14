"use client";

import { useState, useCallback, memo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { WorkflowGraph } from "@/lib/types";

interface NodeTableProps {
  workflow: WorkflowGraph;
  onParamsChanged: (workflow: WorkflowGraph) => void;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string) => void;
  searchQuery?: string;
}

interface FieldDef {
  key: string;
  label: string;
  format: (v: number) => string;
  step: number;
  pct?: boolean;
  integer?: boolean;
  advanced?: boolean;
}

const EDITABLE_FIELDS: FieldDef[] = [
  { key: "exec_time_mean", label: "Time (s)", format: (v: number) => v.toFixed(2), step: 0.1 },
  { key: "queue_delay_mean", label: "Queue (s)", format: (v: number) => v.toFixed(2), step: 0.1 },
  { key: "cost_per_transaction", label: "Cost ($)", format: (v: number) => v.toFixed(4), step: 0.001 },
  {
    key: "error_rate",
    label: "Error %",
    format: (v: number) => (v * 100).toFixed(2),
    step: 0.01,
    pct: true,
  },
  {
    key: "parallelization_factor",
    label: "Workers",
    format: (v: number) => v.toString(),
    step: 1,
    integer: true,
  },
  {
    key: "max_retries",
    label: "Retries",
    format: (v: number) => v.toString(),
    step: 1,
    integer: true,
    advanced: true,
  },
  {
    key: "retry_delay",
    label: "Retry delay (s)",
    format: (v: number) => v.toFixed(2),
    step: 0.1,
    advanced: true,
  },
];

const TYPE_COLORS: Record<string, "default" | "success" | "warning" | "error" | "muted"> = {
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
    if (field.pct) parsed /= 100;
    if (field.integer) parsed = Math.max(1, Math.round(parsed));
    if (parsed < 0) parsed = 0;
    if (Math.abs(parsed - value) > 1e-9) onChange(parsed);
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
        className="h-7 w-20 rounded border border-accent bg-background px-1.5 text-right font-mono text-xs text-text focus:outline-none focus:ring-1 focus:ring-accent"
        autoFocus
      />
    );
  }

  return (
    <button
      onClick={startEdit}
      className="h-7 w-20 cursor-text rounded px-1.5 text-right font-mono text-xs text-text-muted transition-colors hover:bg-surface-hover hover:text-text"
      title="Click to edit"
      type="button"
    >
      {displayValue}
    </button>
  );
});

export function NodeTable({
  workflow,
  onParamsChanged,
  selectedNodeId,
  onSelectNode,
  searchQuery = "",
}: NodeTableProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

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

  const editableNodes = workflow.nodes.filter(
    (n) => n.node_type !== "start" && n.node_type !== "end",
  );

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const visibleNodes = editableNodes.filter((node) => {
    if (!normalizedQuery) return true;
    return (
      node.name.toLowerCase().includes(normalizedQuery) ||
      node.id.toLowerCase().includes(normalizedQuery)
    );
  });

  const visibleFields = EDITABLE_FIELDS.filter((field) => showAdvanced || !field.advanced);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>Node Parameters</CardTitle>
            <p className="mt-1 text-xs text-text-dim">Select a node in graph or table, then tune assumptions.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowAdvanced((v) => !v)}
            >
              {showAdvanced ? "Basic fields" : "Advanced fields"}
            </Button>
            <span className="text-xs text-text-dim">Click any value to edit</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="px-2 py-2 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                Node
              </th>
              <th className="px-2 py-2 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                Type
              </th>
              {visibleFields.map((f) => (
                <th
                  key={f.key}
                  className="px-2 py-2 text-right text-xs font-medium uppercase tracking-wider text-text-muted"
                >
                  {f.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleNodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              return (
                <tr
                  key={node.id}
                  className={`border-b border-border/50 transition-colors ${
                    isSelected ? "bg-accent/10" : "hover:bg-surface-hover/50"
                  }`}
                  onClick={() => onSelectNode?.(node.id)}
                >
                  <td className="max-w-[220px] px-2 py-2 font-medium text-text">
                    <button
                      type="button"
                      onClick={() => onSelectNode?.(node.id)}
                      className="w-full truncate text-left"
                      title={node.name}
                    >
                      {node.name}
                    </button>
                  </td>
                  <td className="px-2 py-2">
                    <Badge variant={TYPE_COLORS[node.node_type] ?? "default"}>{node.node_type}</Badge>
                  </td>
                  {visibleFields.map((field) => (
                    <td key={field.key} className="px-1 py-1 text-right">
                      <EditableCell
                        value={node.params[field.key as keyof typeof node.params] as number}
                        field={field}
                        onChange={(val) => updateNodeParam(node.id, field.key, val)}
                      />
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {visibleNodes.length === 0 && (
          <div className="py-8 text-center text-sm text-text-dim">No nodes match your filter.</div>
        )}
      </CardContent>
    </Card>
  );
}
