"use client";

import { useRef, useState } from "react";
import { Sparkles, Upload, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { WorkflowGraph } from "@/lib/types";
import { generateWorkflow, parseWorkflow } from "@/lib/api";

interface InputBarProps {
  onWorkflowLoaded: (wf: WorkflowGraph) => void;
}

export function InputBar({ onWorkflowLoaded }: InputBarProps) {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleGenerate() {
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const wf = await generateWorkflow(description);
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
    if (file.size > 5 * 1024 * 1024) {
      setError("File too large. Maximum 5 MB.");
      if (fileRef.current) fileRef.current.value = "";
      return;
    }
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const wf = await parseWorkflow(data);
      onWorkflowLoaded(wf);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid JSON file");
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3 items-start">
        <Textarea
          placeholder='Describe your process... e.g. "invoice processing: receive, validate, approve/reject, schedule payment, confirm"'
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="flex-1 min-h-[56px] max-h-[120px]"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              handleGenerate();
            }
          }}
        />
        <div className="flex flex-col gap-2">
          <Button
            onClick={handleGenerate}
            disabled={!description.trim() || loading}
            className="whitespace-nowrap"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Generate
          </Button>
          <Button
            variant="secondary"
            onClick={() => fileRef.current?.click()}
            className="whitespace-nowrap"
          >
            <Upload className="h-4 w-4" />
            Upload
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
      {error && (
        <div className="flex items-center justify-between gap-3 text-sm text-error bg-error/10 border border-error/20 rounded-lg px-3 py-2">
          <span className="flex-1 min-w-0">{error}</span>
          {description.trim() ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setError(null);
                handleGenerate();
              }}
              disabled={!description.trim() || loading}
              className="shrink-0"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" />
              Retry
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}
