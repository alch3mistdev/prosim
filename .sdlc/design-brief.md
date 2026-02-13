# Design Brief: ProSim — Workflow Simulation Engine with Process Mining

## Summary

ProSim is a modular Python engine that accepts a natural language description of a business process (e.g., "invoice processing system," "KYC onboarding flow") and automatically generates a canonical BPMN-style workflow model. The model is a parameterized directed graph where nodes represent state transforms and edges represent transitions. Users can edit parameters, run deterministic and Monte Carlo simulations (10K–1M transactions), apply interventions to individual nodes, and visualize results as Mermaid diagrams and structured JSON. The system models workflows as control networks: time = friction, cost = energy, errors = entropy, and optimization = entropy reduction under constraint.

## Functional Requirements

- FR-1: Accept natural language domain descriptions and generate canonical workflow graphs via Claude API
- FR-2: Classify inferred nodes by type: human, API, async, batch, decision, start, end
- FR-3: Infer transitions, branching logic, loops, and parallel paths from domain context
- FR-4: Construct directed graph with default parameter values (execution time, cost, error probability, retry logic, volume multiplier)
- FR-5: Normalize decision node branch probabilities to sum to 1.0
- FR-6: Support full parameter schema per node: execution time (mean + variance), cost per transaction, KPI metrics (error rate, drop-off, SLA breach probability, conversion rate), parallelization factor, queue delay, capacity constraints
- FR-7: Deterministic simulation: compute expected total time, cost, throughput per transaction via graph traversal
- FR-8: Monte Carlo simulation: run 10K–1M stochastic transaction simulations with configurable distributions
- FR-9: Bottleneck detection: identify nodes with highest friction/queue delay/utilization
- FR-10: Sensitivity analysis: compute marginal impact of each parameter on total system metrics
- FR-11: Intervention layer: allow per-node modifications (time reduction %, cost reduction %, error reduction %, capacity increase, parallelization factor)
- FR-12: Recompute all system metrics after intervention; show delta savings, ROI, and before/after comparison
- FR-13: Render BPMN-style diagrams as Mermaid-compatible output
- FR-14: Output structured node/edge JSON for programmatic consumption
- FR-15: Output baseline vs. optimized summary with highest marginal leverage node highlighted
- FR-16: CLI interface for all operations (generate, simulate, intervene, export)
- FR-17: Web dashboard (Streamlit) for visual graph editing and simulation result exploration

## Non-Functional Requirements

- NFR-1: Monte Carlo simulation of 100K transactions must complete in < 30 seconds on commodity hardware (4-core, 16GB RAM)
- NFR-2: 1M transaction simulation must complete in < 5 minutes
- NFR-3: Graph generation from NL description must complete in < 15 seconds (bounded by Claude API latency)
- NFR-4: System must handle workflow graphs with up to 200 nodes and 500 edges
- NFR-5: All simulation outputs must be reproducible given a fixed random seed
- NFR-6: Memory usage for 1M transaction simulation must stay below 4GB
- NFR-7: CLI must be usable without the web dashboard; web dashboard must be optional
- NFR-8: All configuration via environment variables or config files (no hardcoded secrets)

## Technical Constraints

- **Language**: Python 3.11+
- **LLM Provider**: Anthropic Claude API (claude-sonnet-4-5-20250929 for structured workflow extraction)
- **Graph Library**: NetworkX for graph construction and traversal
- **Simulation**: NumPy for vectorized Monte Carlo; SciPy for statistical distributions
- **Web Dashboard**: Streamlit for rapid prototyping of interactive UI
- **CLI Framework**: Click for command-line interface
- **Serialization**: Pydantic v2 for data models and JSON schema validation
- **Diagram Rendering**: Mermaid syntax generation (rendered client-side in dashboard)
- **Dependencies**: anthropic, networkx, numpy, scipy, pydantic, click, streamlit, rich (for CLI formatting)

## User Model

**Primary user**: Technical business analysts, process engineers, and operations managers who understand their business processes but want quantitative simulation without building custom models. They interact via CLI for scripting/automation or via the Streamlit dashboard for exploration. They are comfortable with JSON configuration but expect sensible defaults. They do NOT need to understand graph theory or simulation internals.

**Secondary user**: Developers integrating ProSim as a library into larger workflow orchestration or process mining pipelines. They interact via the Python API directly.

## Scope Boundaries

### In Scope
- Natural language to workflow graph generation (via Claude API)
- Parameterized graph data model with full BPMN-style node types
- Deterministic and Monte Carlo simulation engines
- Bottleneck detection and sensitivity analysis
- Node-level intervention with delta/ROI computation
- Mermaid diagram export
- Structured JSON import/export
- CLI interface (Click)
- Web dashboard (Streamlit)
- Reproducible simulations (seed control)

### Out of Scope
- Real-time process mining from event logs (future extension)
- BPMN XML import/export (Mermaid only for v1)
- Multi-user collaboration or authentication
- Persistent database storage (file-based only for v1)
- Deployment infrastructure (Docker, K8s — user responsibility)
- Custom distribution fitting from historical data
- Real-time streaming simulation
- Workflow execution (this is simulation only, not orchestration)

## Success Criteria

- SC-1: Given the input "invoice processing system", the engine generates a valid workflow graph with >= 5 nodes covering receive, validate, approve, pay, and close steps
- SC-2: Deterministic simulation produces consistent, mathematically correct expected time and cost for a known test graph
- SC-3: Monte Carlo simulation of 100K transactions completes in < 30 seconds and produces statistically valid distributions
- SC-4: Applying a 50% time reduction intervention to the bottleneck node reduces total expected time by a measurable, correct delta
- SC-5: Mermaid output renders a valid, readable BPMN-style diagram when pasted into any Mermaid renderer
- SC-6: CLI can complete a full generate -> simulate -> intervene -> export cycle without the web dashboard
- SC-7: Web dashboard displays interactive graph, simulation results, and intervention controls
- SC-8: All public API functions have type hints and docstrings
- SC-9: Test coverage >= 80% on core simulation and graph modules
