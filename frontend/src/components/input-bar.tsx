"use client";

import { useRef, useState, useEffect } from "react";
import { Sparkles, Upload, Loader2, RotateCcw, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { InlineHelp } from "@/components/inline-help";
import type { WorkflowGraph } from "@/lib/types";
import { generateWorkflow, parseWorkflow } from "@/lib/api";

interface InputBarProps {
  onWorkflowLoaded: (wf: WorkflowGraph) => void;
}

const STARTER_TEMPLATES = [
  "invoice processing workflow with approval and payment",
  "accounting audit process from intake to final report",
  "customer onboarding flow with KYC, risk review, and activation",
];

const GENERATION_STAGES = [
  "Interpreting process description",
  "Generating workflow structure",
  "Validating graph integrity",
];

export function InputBar({ onWorkflowLoaded }: InputBarProps) {
  const [description, setDescription] = useState("");
  const [maxNodes, setMaxNodes] = useState<number | "">(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!loading) {
      setStageIndex(0);
      return;
    }

    const timer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % GENERATION_STAGES.length);
    }, 1600);

    return () => clearInterval(timer);
  }, [loading]);

  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    setUploadMessage(null);

    try {
      const wf = await generateWorkflow(description, {
        max_nodes: maxNodes === "" ? undefined : maxNodes,
      });
      onWorkflowLoaded(wf);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploadMessage(null);

    if (file.size > 5 * 1024 * 1024) {
      setError("File too large. Maximum 5 MB.");
      if (fileRef.current) fileRef.current.value = "";
      return;
    }

    try {
      const text = await file.text();
      const data = JSON.parse(text) as Record<string, unknown>;
      const wf = await parseWorkflow(data);
      onWorkflowLoaded(wf);
      setUploadMessage(`Loaded \"${wf.name}\" (${wf.nodes.length} nodes, ${wf.edges.length} edges).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid JSON file");
    }

    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-border/80 bg-surface/40 p-4 backdrop-blur-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start">
          <div className="flex-1 space-y-2">
            <Textarea
              placeholder='Describe your process... e.g. "invoice processing: receive, validate, approve/reject, schedule payment, confirm"'
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="flex-1 min-h-[64px] max-h-[140px]"
              aria-label="Workflow description"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  void handleGenerate();
                }
              }}
            />
            <div className="flex flex-wrap gap-2">
              {STARTER_TEMPLATES.map((template) => (
                <button
                  key={template}
                  type="button"
                  className="rounded-full border border-border/80 bg-background/50 px-3 py-1 text-xs text-text-muted transition-colors hover:border-accent/50 hover:text-text"
                  onClick={() => setDescription(template)}
                >
                  {template}
                </button>
              ))}
            </div>
            <p className="text-xs text-text-dim">
              Generation typically takes 30-60 seconds. Use <span className="font-mono">Cmd/Ctrl + Enter</span> to run.
            </p>
            <InlineHelp title="Input Help">
              Describe the process as ordered steps and decision points, for example:
              intake - validate - decision - approval - completion. Upload JSON if you
              already have a workflow model. Max nodes limits generated complexity.
            </InlineHelp>
          </div>

          <div className="flex min-w-[170px] flex-col gap-2">
            <div className="flex items-center justify-between gap-2 rounded-lg border border-border bg-background/40 px-2.5 py-1.5">
              <span className="text-xs text-text-muted whitespace-nowrap">Max nodes</span>
              <Input
                type="number"
                value={maxNodes}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "") setMaxNodes("");
                  else {
                    const n = parseInt(v, 10);
                    if (!isNaN(n)) setMaxNodes(Math.min(100, Math.max(3, n)));
                  }
                }}
                placeholder="max"
                className="h-8 w-[4.5rem] text-xs"
                min={3}
                max={100}
                title="Max nodes in workflow (3-100, empty = no limit)"
                aria-label="Maximum node count"
              />
            </div>

            <Button
              onClick={() => void handleGenerate()}
              disabled={!description.trim() || loading}
              className="whitespace-nowrap"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Generate Baseline
            </Button>

            <Button
              variant="secondary"
              onClick={() => fileRef.current?.click()}
              className="whitespace-nowrap"
            >
              <Upload className="h-4 w-4" />
              Upload JSON
            </Button>

            <input
              ref={fileRef}
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleUpload}
            />
          </div>
        </div>
      </div>

      {loading && (
        <div className="rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent-bright">
          <span className="font-medium">Generating:</span> {GENERATION_STAGES[stageIndex]}
        </div>
      )}

      {uploadMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
          <CheckCircle2 className="h-4 w-4" />
          <span>{uploadMessage}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-error/20 bg-error/10 px-3 py-2 text-sm text-error">
          <span className="min-w-0 flex-1">{error}</span>
          {description.trim() ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setError(null);
                void handleGenerate();
              }}
              disabled={!description.trim() || loading}
              className="shrink-0"
            >
              <RotateCcw className="mr-1 h-3.5 w-3.5" />
              Retry
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}
