import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  if (cost < 1) return `$${cost.toFixed(3)}`;
  if (cost < 1000) return `$${cost.toFixed(2)}`;
  return `$${cost.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function formatPct(pct: number): string {
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

export function formatThroughputPerHour(value: number): string {
  if (!isFinite(value) || value <= 0) return "0/hr";
  if (value < 1) return `${value.toFixed(2)}/hr`;
  if (value < 10) return `${value.toFixed(1)}/hr`;
  return `${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}/hr`;
}

export function formatRelativeDelta(current: number, baseline: number): string {
  if (Math.abs(baseline) < 1e-9) return current === 0 ? "0.0%" : "+100.0%";
  const pct = ((current - baseline) / baseline) * 100;
  return formatPct(pct);
}
