# Architecture v2: Next.js Dashboard + FastAPI API

## Subsystems

### 1. sys.api — FastAPI Backend
**Responsibility**: Thin HTTP wrapper over existing ProSim Python modules.

| Leaf | File | Lines |
|------|------|-------|
| sys.api.server | `src/prosim/api/server.py` | FastAPI app, CORS, static file serving |
| sys.api.routes | `src/prosim/api/routes.py` | All REST endpoints (workflow, simulate, intervene, export) |

### 2. sys.frontend.config — Next.js Project Scaffold
**Responsibility**: Project configuration and build setup.

| Leaf | File | Lines |
|------|------|-------|
| sys.frontend.config.package | `frontend/package.json` | Dependencies and scripts |
| sys.frontend.config.next | `frontend/next.config.ts` | Next.js config with API proxy |
| sys.frontend.config.tailwind | `frontend/tailwind.config.ts` | Tailwind with shadcn/ui dark theme |
| sys.frontend.config.postcss | `frontend/postcss.config.mjs` | PostCSS for Tailwind |
| sys.frontend.config.tsconfig | `frontend/tsconfig.json` | TypeScript config |
| sys.frontend.config.styles | `frontend/src/app/globals.css` | Global styles + Tailwind imports |
| sys.frontend.config.layout | `frontend/src/app/layout.tsx` | Root layout with dark theme + fonts |
| sys.frontend.config.cn | `frontend/src/lib/utils.ts` | cn() utility for shadcn |

### 3. sys.frontend.lib — Types + API Client
**Responsibility**: TypeScript type definitions mirroring Pydantic models + API fetch wrappers.

| Leaf | File | Lines |
|------|------|-------|
| sys.frontend.lib.types | `frontend/src/lib/types.ts` | All TS interfaces matching Python models |
| sys.frontend.lib.api | `frontend/src/lib/api.ts` | Typed fetch functions for each endpoint |

### 4. sys.frontend.ui — shadcn/ui Components
**Responsibility**: Reusable UI primitives from shadcn/ui.

| Leaf | File |
|------|------|
| sys.frontend.ui.button | `frontend/src/components/ui/button.tsx` |
| sys.frontend.ui.card | `frontend/src/components/ui/card.tsx` |
| sys.frontend.ui.input | `frontend/src/components/ui/input.tsx` |
| sys.frontend.ui.textarea | `frontend/src/components/ui/textarea.tsx` |
| sys.frontend.ui.slider | `frontend/src/components/ui/slider.tsx` |
| sys.frontend.ui.badge | `frontend/src/components/ui/badge.tsx` |
| sys.frontend.ui.select | `frontend/src/components/ui/select.tsx` |
| sys.frontend.ui.table | `frontend/src/components/ui/table.tsx` |
| sys.frontend.ui.separator | `frontend/src/components/ui/separator.tsx` |
| sys.frontend.ui.skeleton | `frontend/src/components/ui/skeleton.tsx` |
| sys.frontend.ui.label | `frontend/src/components/ui/label.tsx` |
| sys.frontend.ui.tabs | `frontend/src/components/ui/tabs.tsx` |

### 5. sys.frontend.components — Dashboard Zones
**Responsibility**: The 5 zone components that compose the dashboard.

| Leaf | File | Responsibility |
|------|------|----------------|
| sys.frontend.components.input_bar | `frontend/src/components/input-bar.tsx` | Zone 1: Process description + Generate + Upload |
| sys.frontend.components.workflow_diagram | `frontend/src/components/workflow-diagram.tsx` | Mermaid SVG rendering with client-side mermaid.js |
| sys.frontend.components.metrics_cards | `frontend/src/components/metrics-cards.tsx` | Key metric cards (time, cost, throughput, completion) + bottleneck list |
| sys.frontend.components.node_table | `frontend/src/components/node-table.tsx` | Editable parameter table with inline editing |
| sys.frontend.components.whatif_panel | `frontend/src/components/whatif-panel.tsx` | Node selector + sliders + delta metrics |
| sys.frontend.components.advanced_panel | `frontend/src/components/advanced-panel.tsx` | Monte Carlo, sensitivity, export in collapsible sections |

### 6. sys.frontend.page — Main Page + State
**Responsibility**: Compose all zones, manage workflow/results state.

| Leaf | File | Responsibility |
|------|------|----------------|
| sys.frontend.page.main | `frontend/src/app/page.tsx` | Main page composing all dashboard zones |
| sys.frontend.page.hooks | `frontend/src/hooks/use-prosim.ts` | useProSim hook: workflow state, auto-simulate, API calls |

### 7. sys.cli.serve — CLI Integration
**Responsibility**: Add `prosim serve` command to launch FastAPI.

| Leaf | File |
|------|------|
| sys.cli.serve | `src/prosim/cli/commands.py` (modify) | Add `serve` command |

## Dependency Graph

```
sys.cli.serve → sys.api
sys.frontend.page → sys.frontend.components → sys.frontend.lib → sys.api
sys.frontend.components → sys.frontend.ui
sys.frontend.ui → sys.frontend.config
```

## Total: 7 subsystems, ~30 leaf nodes
