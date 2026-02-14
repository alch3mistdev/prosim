# Design Brief v2: ProSim — Next.js Dashboard Redesign

## Summary

Replace the Streamlit dashboard with a modern Next.js web application backed by a FastAPI API layer. The Python simulation engine (graph, simulation, intervention, export, parser) is unchanged — a thin FastAPI wrapper exposes its Pydantic APIs over HTTP. The frontend is a single-page dark-themed dashboard built with Next.js 15, Tailwind CSS, and shadcn/ui that enables rapid, zero-friction simulation tweaking: type a process description, see a visual workflow diagram, edit node parameters inline, drag what-if sliders, and watch metrics update in real time.

## Functional Requirements (Frontend + API)

- FR-18: FastAPI server exposes all existing ProSim functions as REST endpoints
- FR-19: `POST /api/workflow/generate` — NL description → WorkflowGraph JSON
- FR-20: `POST /api/workflow/parse` — Upload JSON → validated WorkflowGraph
- FR-21: `POST /api/simulate` — Run deterministic or Monte Carlo simulation
- FR-22: `POST /api/sensitivity` — Run sensitivity analysis
- FR-23: `POST /api/intervene` — Apply interventions, return comparison
- FR-24: `POST /api/leverage` — Rank leverage points
- FR-25: `POST /api/export/mermaid` — Generate Mermaid diagram string
- FR-26: Single-page dashboard with 5 zones: Input, Diagram+Metrics, Node Table, What-If, Advanced
- FR-27: Mermaid diagrams render as interactive SVG in the browser (client-side mermaid.js)
- FR-28: Editing any node parameter triggers instant deterministic re-simulation (< 200ms round-trip)
- FR-29: What-if sliders show live delta metrics without page reload
- FR-30: Monte Carlo simulation shows progress and distribution results
- FR-31: Dark theme with accent colors, card-based layout, responsive design
- FR-32: CLI command `prosim serve` starts the FastAPI server

## Non-Functional Requirements (Frontend)

- NFR-9: First contentful paint < 1 second on localhost
- NFR-10: Deterministic simulation round-trip (parameter change → updated metrics) < 200ms
- NFR-11: Frontend bundle < 500KB gzipped
- NFR-12: Responsive layout: usable at 1024px width minimum
- NFR-13: Accessible: keyboard navigation, ARIA labels on interactive elements, WCAG AA contrast

## Technical Constraints (Frontend)

- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Diagram**: mermaid (npm package, client-side rendering)
- **State**: React hooks (useState/useReducer) — no external state library
- **API**: FastAPI (uvicorn) on :8000, Next.js dev on :3000 with proxy
- **No database**: All state is in-memory per session

## Scope Boundaries

### In Scope
- FastAPI wrapper over existing ProSim Python modules
- Next.js single-page dashboard with all 5 zones
- Dark theme with shadcn/ui components
- Mermaid SVG rendering in browser
- Inline node parameter editing with auto re-simulation
- What-if sliders with live delta metrics
- Monte Carlo and sensitivity in expandable panels
- `prosim serve` CLI command
- CORS configuration for dev/prod

### Out of Scope
- Authentication / multi-user
- Database / persistence (beyond in-memory)
- Server-side rendering of Mermaid (client-side only)
- WebSocket streaming (REST polling is sufficient)
- E2E tests (unit tests for API, manual testing for frontend)
- Docker / deployment packaging
- Removing the old Streamlit dashboard (kept for backwards compatibility)

## Success Criteria

- SC-10: `prosim serve` starts FastAPI, all endpoints return correct responses
- SC-11: Frontend renders Mermaid diagram as visual SVG (not code block)
- SC-12: Editing a node's execution time in the table triggers re-simulation and metrics update within 200ms
- SC-13: What-if slider movement shows delta metrics without page navigation
- SC-14: Monte Carlo results display percentile metrics and completion stats
- SC-15: Dashboard is usable on a 1024px wide viewport
- SC-16: All existing 78 Python tests continue to pass
