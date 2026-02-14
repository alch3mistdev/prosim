"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface WorkflowDiagramProps {
  mermaidCode: string | null;
  loading?: boolean;
}

export function WorkflowDiagram({ mermaidCode, loading }: WorkflowDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const initializedRef = useRef(false);

  const renderDiagram = useCallback(async () => {
    if (!mermaidCode || !containerRef.current) return;
    setRenderError(null);

    try {
      const mermaid = (await import("mermaid")).default;

      // Initialize only once
      if (!initializedRef.current) {
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#6366f1",
            primaryTextColor: "#e4e4ef",
            primaryBorderColor: "#818cf8",
            lineColor: "#555570",
            secondaryColor: "#1a1a26",
            tertiaryColor: "#12121a",
            background: "#12121a",
            mainBkg: "#1a1a26",
            nodeBorder: "#3a3a5a",
            clusterBkg: "#12121a",
            clusterBorder: "#2a2a3a",
            titleColor: "#e4e4ef",
            edgeLabelBackground: "#12121a",
            nodeTextColor: "#e4e4ef",
          },
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: "basis",
          },
          securityLevel: "strict",
        });
        initializedRef.current = true;
      }

      // Clear previous render
      containerRef.current.innerHTML = "";

      const id = `mermaid-${Date.now()}`;
      const { svg } = await mermaid.render(id, mermaidCode);
      if (containerRef.current) {
        containerRef.current.innerHTML = svg;
      }
    } catch (err) {
      setRenderError(err instanceof Error ? err.message : "Diagram render failed");
    }
  }, [mermaidCode]);

  useEffect(() => {
    renderDiagram();
  }, [renderDiagram]);

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <CardTitle>Workflow</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-64 w-full" />}
        {!loading && !mermaidCode && (
          <div className="flex items-center justify-center h-48 text-text-dim text-sm">
            Generate or upload a workflow to see the diagram
          </div>
        )}
        {renderError && (
          <div className="text-sm text-warning bg-warning/10 border border-warning/20 rounded-lg p-3 mb-3 font-mono">
            {renderError}
          </div>
        )}
        <div
          ref={containerRef}
          className="mermaid-container overflow-auto max-h-[500px]"
        />
      </CardContent>
    </Card>
  );
}
