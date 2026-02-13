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
- **CLI + Web Dashboard**: Full CLI interface and optional Streamlit dashboard

## Setup

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set your `ANTHROPIC_API_KEY`.

## Usage

### Generate a workflow from a description

```bash
prosim generate "invoice processing system" -o workflow.json
```

### Simulate the workflow

```bash
# Deterministic (expected values)
prosim simulate workflow.json --mode deterministic -n 10000

# Monte Carlo (stochastic, 100K transactions)
prosim simulate workflow.json --mode monte_carlo -n 100000 --seed 42

# With sensitivity analysis
prosim simulate workflow.json --sensitivity
```

### Apply interventions

```bash
prosim intervene workflow.json \
  --node process_payment \
  --time-reduction 30 \
  --cost-reduction 20 \
  --impl-cost 50000
```

### Export diagrams

```bash
prosim export workflow.json -f mermaid
prosim export workflow.json -f json -o full_export.json
```

### Launch the web dashboard

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
│   ├── cli/            # Click CLI commands
│   └── dashboard/      # Streamlit web UI
└── tests/              # 78 tests across all subsystems
```

The system models workflows as **control networks**:
- **Nodes** = state transforms
- **Time** = friction
- **Cost** = energy
- **Errors** = entropy
- **Optimization** = entropy reduction under constraint

## Running Tests

```bash
pytest tests/ -v
```
