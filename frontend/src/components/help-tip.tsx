"use client";

import { CircleHelp } from "lucide-react";
import { cn } from "@/lib/utils";

interface HelpTipProps {
  text: string;
  className?: string;
}

export function HelpTip({ text, className }: HelpTipProps) {
  return (
    <span className={cn("group relative inline-flex", className)}>
      <button
        type="button"
        aria-label={text}
        title={text}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full text-text-dim transition-colors hover:text-accent-bright focus:outline-none focus-visible:ring-1 focus-visible:ring-accent"
      >
        <CircleHelp className="h-3.5 w-3.5" />
      </button>
      <span className="pointer-events-none absolute left-1/2 top-0 z-[95] hidden w-64 -translate-x-1/2 -translate-y-[110%] rounded-md border border-border bg-[#0b1424]/98 px-2 py-1.5 text-[11px] leading-relaxed text-text-muted shadow-xl group-hover:block group-focus-within:block">
        {text}
      </span>
    </span>
  );
}
