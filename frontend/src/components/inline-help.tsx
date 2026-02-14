"use client";

import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface InlineHelpProps {
  title: string;
  children: ReactNode;
  className?: string;
  defaultOpen?: boolean;
}

export function InlineHelp({ title, children, className, defaultOpen = false }: InlineHelpProps) {
  return (
    <details className={cn("rounded-md border border-border/80 bg-background/40", className)} open={defaultOpen}>
      <summary className="flex cursor-pointer list-none items-center gap-2 px-2.5 py-1.5 text-xs text-text-muted marker:content-none">
        <Info className="h-3.5 w-3.5 text-accent-bright" />
        <span>{title}</span>
      </summary>
      <div className="border-t border-border/70 px-2.5 py-2 text-xs leading-relaxed text-text-dim">
        {children}
      </div>
    </details>
  );
}
