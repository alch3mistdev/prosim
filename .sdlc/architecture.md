# ProSim Architecture

## Subsystem Overview

ProSim is decomposed into 6 bounded subsystems:

```
┌─────────────────────────────────────────────────────────┐
│                     CLI / Web UI                         │
│              (sys.cli + sys.dashboard)                   │
├─────────────────────────────────────────────────────────┤
│                   Intervention Layer                     │
│                   (sys.intervention)                     │
├─────────────────────────────────────────────────────────┤
│                   Simulation Engine                      │
│                   (sys.simulation)                       │
├─────────────────────────────────────────────────────────┤
│                   Graph / Data Model                     │
│                     (sys.graph)                          │
├─────────────────────────────────────────────────────────┤
│                   Domain Parser                          │
│                   (sys.parser)                           │
├─────────────────────────────────────────────────────────┤
│                   Export / Rendering                     │
│                   (sys.export)                           │
└─────────────────────────────────────────────────────────┘
```

## Dependency Graph (acyclic)

```
sys.parser → sys.graph
sys.simulation → sys.graph
sys.intervention → sys.simulation, sys.graph
sys.export → sys.graph, sys.simulation
sys.cli → sys.parser, sys.graph, sys.simulation, sys.intervention, sys.export
sys.dashboard → sys.parser, sys.graph, sys.simulation, sys.intervention, sys.export
```

## Subsystem Details

### 1. sys.graph — Graph Data Model
**Responsibility**: Define and manage the workflow graph data structures, node/edge schemas, and graph operations.
- Pydantic models for nodes, edges, and workflow graphs
- Graph construction, validation, and manipulation
- Decision probability normalization
- Serialization to/from JSON

### 2. sys.parser — Domain Parser
**Responsibility**: Transform natural language domain descriptions into structured workflow graphs via Claude API.
- Claude API client wrapper
- Structured output extraction (tool_use)
- Domain template fallbacks
- Graph validation post-generation

### 3. sys.simulation — Simulation Engine
**Responsibility**: Execute deterministic and Monte Carlo simulations on workflow graphs.
- Deterministic path analysis (expected values via graph traversal)
- Monte Carlo engine (stochastic simulation with configurable distributions)
- Bottleneck detection algorithm
- Sensitivity analysis (per-parameter marginal impact)
- Throughput computation under volume constraints

### 4. sys.intervention — Intervention Layer
**Responsibility**: Apply modifications to graph parameters and compute deltas.
- Intervention specification model
- Parameter modification with constraint validation
- Before/after metric comparison
- ROI computation
- Marginal leverage ranking

### 5. sys.export — Export & Rendering
**Responsibility**: Transform graph and simulation results into output formats.
- Mermaid diagram generation
- JSON export (nodes, edges, simulation results)
- Baseline vs. optimized summary reports
- Rich console table formatting

### 6. sys.cli — CLI Interface
**Responsibility**: Provide Click-based command-line interface for all operations.
- `prosim generate` — NL to workflow graph
- `prosim simulate` — Run simulation on a graph
- `prosim intervene` — Apply interventions
- `prosim export` — Export diagrams and reports
- `prosim dashboard` — Launch Streamlit UI

### 7. sys.dashboard — Web Dashboard
**Responsibility**: Provide Streamlit-based interactive UI.
- Graph visualization (Mermaid rendering)
- Parameter editing sidebar
- Simulation controls and results display
- Intervention builder and delta display

## Leaf Node Decomposition

### sys.graph
- `sys.graph.models` → `src/prosim/graph/models.py` — Pydantic models (Node, Edge, WorkflowGraph, enums)
- `sys.graph.operations` → `src/prosim/graph/operations.py` — Graph construction, validation, probability normalization
- `sys.graph.serialization` → `src/prosim/graph/serialization.py` — JSON import/export, graph persistence

### sys.parser
- `sys.parser.client` → `src/prosim/parser/client.py` — Claude API client with tool_use for structured extraction
- `sys.parser.prompts` → `src/prosim/parser/prompts.py` — System prompts and tool schemas for workflow generation
- `sys.parser.postprocess` → `src/prosim/parser/postprocess.py` — Validate and clean generated graphs, apply defaults

### sys.simulation
- `sys.simulation.deterministic` → `src/prosim/simulation/deterministic.py` — Expected value computation via DAG traversal
- `sys.simulation.montecarlo` → `src/prosim/simulation/montecarlo.py` — Stochastic simulation engine (NumPy vectorized)
- `sys.simulation.bottleneck` → `src/prosim/simulation/bottleneck.py` — Bottleneck detection and utilization analysis
- `sys.simulation.sensitivity` → `src/prosim/simulation/sensitivity.py` — Parameter sensitivity analysis
- `sys.simulation.results` → `src/prosim/simulation/results.py` — Simulation result models and aggregation

### sys.intervention
- `sys.intervention.models` → `src/prosim/intervention/models.py` — Intervention specification and delta models
- `sys.intervention.engine` → `src/prosim/intervention/engine.py` — Apply interventions, recompute metrics, compute ROI
- `sys.intervention.leverage` → `src/prosim/intervention/leverage.py` — Marginal leverage ranking algorithm

### sys.export
- `sys.export.mermaid` → `src/prosim/export/mermaid.py` — BPMN-style Mermaid diagram generation
- `sys.export.json_export` → `src/prosim/export/json_export.py` — Structured JSON output for graphs and results
- `sys.export.reports` → `src/prosim/export/reports.py` — Baseline vs. optimized summary, Rich table formatting

### sys.cli
- `sys.cli.main` → `src/prosim/cli/main.py` — Click group and command definitions
- `sys.cli.commands` → `src/prosim/cli/commands.py` — Command implementations (generate, simulate, intervene, export)

### sys.dashboard
- `sys.dashboard.app` → `src/prosim/dashboard/app.py` — Streamlit application entry point
- `sys.dashboard.components` → `src/prosim/dashboard/components.py` — Reusable UI components (graph viewer, param editor, results panel)

## File Structure

```
ProSim/
├── .sdlc/
├── src/
│   └── prosim/
│       ├── __init__.py
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── operations.py
│       │   └── serialization.py
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── prompts.py
│       │   └── postprocess.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── deterministic.py
│       │   ├── montecarlo.py
│       │   ├── bottleneck.py
│       │   ├── sensitivity.py
│       │   └── results.py
│       ├── intervention/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── engine.py
│       │   └── leverage.py
│       ├── export/
│       │   ├── __init__.py
│       │   ├── mermaid.py
│       │   ├── json_export.py
│       │   └── reports.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── commands.py
│       └── dashboard/
│           ├── __init__.py
│           ├── app.py
│           └── components.py
├── tests/
│   ├── __init__.py
│   ├── test_graph/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_operations.py
│   │   └── test_serialization.py
│   ├── test_simulation/
│   │   ├── __init__.py
│   │   ├── test_deterministic.py
│   │   ├── test_montecarlo.py
│   │   ├── test_bottleneck.py
│   │   └── test_sensitivity.py
│   ├── test_intervention/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_engine.py
│   │   └── test_leverage.py
│   ├── test_export/
│   │   ├── __init__.py
│   │   ├── test_mermaid.py
│   │   └── test_reports.py
│   └── test_cli/
│       ├── __init__.py
│       └── test_commands.py
├── pyproject.toml
├── README.md
└── .env.example
```

**Total leaf nodes: 22**
**Total test files: 13**
