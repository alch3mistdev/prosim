# ProSim

Workflow Simulation Engine with Process Mining Capabilities.

Generate, simulate, and optimize business process workflows from natural language descriptions.

## Features

- **Domain Parsing**: Describe a process in natural language, get a BPMN-style workflow graph via Claude API
- **Parameterized Graphs**: Full parameter schema per node (time, cost, error rate, capacity, parallelization, queue delay)
- **Deterministic Simulation**: Expected-value computation via probability-weighted DAG traversal
- **Monte Carlo Simulation**: Stochastic simulation of 10K-1M transactions with configurable distributions
- **Bottleneck Detection**: Identify the highest-friction nodes in your workflow
- **Sensitivity Analysis**: Compute marginal impact of each parameter on system-level metrics
- **Intervention Layer**: Apply what-if modifications, see delta savings and ROI
- **Mermaid Diagrams**: Export BPMN-style diagrams compatible with any Mermaid renderer
- **CLI**: Full command-line interface for all operations
- **Next.js Dashboard**: Modern dark-themed single-page app with live editing and instant re-simulation
- **Streamlit Dashboard**: Legacy dashboard (still available)

## Setup

### Backend

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set your `ANTHROPIC_API_KEY`.

### Frontend (Next.js Dashboard)

```bash
cd frontend
npm install
```

## Usage

### Quick Start (Web Dashboard)

Start both the API server and the Next.js dev server:

```bash
# Terminal 1: Start the FastAPI backend
prosim serve --port 8000

# Terminal 2: Start the Next.js frontend
cd frontend
npm run dev
```

Open http://localhost:3000. Type a process description, click Generate, and start tweaking.

### CLI Commands

#### Generate a workflow from a description

```bash
prosim generate "invoice processing system" -o workflow.json
```

#### Simulate the workflow

```bash
# Deterministic (expected values)
prosim simulate workflow.json --mode deterministic -n 10000

# Monte Carlo (stochastic, 100K transactions)
prosim simulate workflow.json --mode monte_carlo -n 100000 --seed 42

# With sensitivity analysis
prosim simulate workflow.json --sensitivity
```

#### Apply interventions

```bash
prosim intervene workflow.json \
  --node process_payment \
  --time-reduction 30 \
  --cost-reduction 20 \
  --impl-cost 50000
```

#### Export diagrams

```bash
prosim export workflow.json -f mermaid
prosim export workflow.json -f json -o full_export.json
```

#### Legacy Streamlit dashboard

```bash
prosim dashboard
```

## Architecture

```
ProSim/
├── src/prosim/
│   ├── graph/          # Pydantic data models, NetworkX operations, serialization
│   ├── parser/         # Claude API client for NL->workflow generation
│   ├── simulation/     # Deterministic + Monte Carlo engines, bottleneck detection
│   ├── intervention/   # What-if modifications, ROI computation, leverage ranking
│   ├── export/         # Mermaid diagrams, JSON export, Rich reports
│   ├── cli/            # Click CLI commands (generate, simulate, intervene, export, serve)
│   ├── api/            # FastAPI REST layer for the Next.js frontend
│   └── dashboard/      # Legacy Streamlit web UI
├── frontend/           # Next.js 15 + Tailwind CSS + shadcn/ui dashboard
│   └── src/
│       ├── app/        # Next.js App Router (page.tsx, layout.tsx, globals.css)
│       ├── components/ # Dashboard zones (input-bar, diagram, metrics, node-table, whatif, advanced)
│       ├── hooks/      # useProSim state management hook
│       └── lib/        # TypeScript types, API client, utilities
└── tests/              # 87 tests across all subsystems
```

### Frontend Zones

The Next.js dashboard is a single-page reactive app organized into 5 zones:

1. **Input Bar** — Describe a process or upload JSON
2. **Diagram + Metrics** — Live Mermaid SVG + 4 metric cards + bottleneck list
3. **Node Table** — Click-to-edit parameters, auto re-simulates on change
4. **What-If** — Target a node with time/cost/error reduction sliders, see live delta metrics
5. **Advanced** — Monte Carlo simulation, sensitivity/leverage analysis, export

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/workflow/generate` | Generate workflow from description (Claude API) |
| POST | `/api/workflow/parse` | Validate and normalize uploaded JSON |
| POST | `/api/simulate` | Run deterministic or Monte Carlo simulation |
| POST | `/api/sensitivity` | Sensitivity analysis |
| POST | `/api/intervene` | Apply interventions, get before/after comparison |
| POST | `/api/leverage` | Rank nodes by improvement leverage |
| POST | `/api/export/mermaid` | Generate Mermaid diagram code |

## Running Tests

```bash
# Python backend tests (87 tests)
pytest tests/ -v

# Build frontend (type checking + production build)
cd frontend && npx next build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required for workflow generation |
| `PROSIM_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated CORS origins |
| `NEXT_PUBLIC_API_BASE` | `/api` | API base URL (frontend) |
