"""System prompts and tool schemas for Claude API workflow generation."""

from __future__ import annotations

SYSTEM_PROMPT = """You are a business process modeling expert. Given a natural language description of a business process, you must generate a structured BPMN-style workflow model.

Your output must be a valid workflow graph with:
1. Nodes representing process steps, classified by type
2. Edges representing transitions between steps
3. Realistic default parameters for each node

Node types:
- "start": Process entry point
- "end": Process termination point
- "human": Steps requiring human action (review, approval, manual entry)
- "api": Automated API calls or system integrations
- "async": Asynchronous processing (background jobs, notifications)
- "batch": Batch processing operations
- "decision": Decision points with multiple outcomes
- "parallel_gateway": Points where parallel paths fork or join
- "wait": Waiting states (timers, external triggers)

For each node, provide realistic default parameters:
- exec_time_mean: Average execution time in seconds (be realistic: human tasks 60-3600s, API calls 0.1-10s, batch 10-600s)
- exec_time_variance: Variance proportional to mean (typically 10-30% of mean squared)
- cost_per_transaction: Cost in USD (human labor ~$0.50-$10, API calls ~$0.001-$0.10, batch ~$0.01-$1.00)
- error_rate: Probability of error (human 0.01-0.05, API 0.001-0.01, batch 0.01-0.03)
- queue_delay_mean: Queue waiting time in seconds
- capacity_per_hour: Maximum throughput per hour (null for unlimited)
- max_retries: Number of retries on error (0-3)

For decision nodes, ensure branch probabilities sum to 1.0.

CRITICAL - Graph structure requirements:
1. Include exactly one "start" node and one "end" node.
2. Every node MUST appear in at least one edge — either as source or target. No orphaned nodes.
3. Edges must form a connected flow from start to end. Use source/target IDs that EXACTLY match the node "id" field (same spelling, underscores, no typos).
4. For each edge, source and target must be valid node IDs from your nodes list.

Example of correct edge format (node IDs must match exactly):
  nodes: [{"id": "start", ...}, {"id": "validate_invoice", ...}, {"id": "end", ...}]
  edges: [{"source": "start", "target": "validate_invoice"}, {"source": "validate_invoice", "target": "end"}]

Generate a complete, realistic workflow that captures the essential steps, decision points, and error paths of the described process."""


WORKFLOW_TOOL = {
    "name": "generate_workflow",
    "description": "Generate a structured workflow graph from a process description",
    "input_schema": {
        "type": "object",
        "required": ["name", "description", "nodes", "edges"],
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the workflow",
            },
            "description": {
                "type": "string",
                "description": "Brief description of the workflow",
            },
            "nodes": {
                "type": "array",
                "description": "List of workflow nodes. Must include exactly one start and one end node.",
                "items": {
                    "type": "object",
                    "required": ["id", "name", "node_type"],
                    "properties": {
                        "id": {"type": "string", "description": "Unique node identifier (snake_case)"},
                        "name": {"type": "string", "description": "Human-readable node name"},
                        "node_type": {
                            "type": "string",
                            "enum": ["start", "end", "human", "api", "async", "batch", "decision", "parallel_gateway", "wait"],
                        },
                        "description": {"type": "string", "description": "What this step does"},
                        "exec_time_mean": {"type": "number", "description": "Average execution time in seconds"},
                        "exec_time_variance": {"type": "number", "description": "Variance of execution time"},
                        "cost_per_transaction": {"type": "number", "description": "Cost per transaction in USD"},
                        "error_rate": {"type": "number", "description": "Error probability (0-1)"},
                        "drop_off_rate": {"type": "number", "description": "Drop-off probability (0-1)"},
                        "queue_delay_mean": {"type": "number", "description": "Average queue delay in seconds"},
                        "capacity_per_hour": {"type": ["number", "null"], "description": "Max capacity per hour"},
                        "max_retries": {"type": "integer", "description": "Max retry attempts"},
                        "retry_delay": {"type": "number", "description": "Delay between retries in seconds"},
                        "parallelization_factor": {"type": "integer", "description": "Number of parallel workers"},
                    },
                },
            },
            "edges": {
                "type": "array",
                "minItems": 1,
                "description": "List of workflow edges. Every node must appear in at least one edge (as source or target). Edges must connect all nodes from start to end.",
                "items": {
                    "type": "object",
                    "required": ["source", "target"],
                    "properties": {
                        "source": {"type": "string", "description": "Source node ID — must exactly match a node id from the nodes array"},
                        "target": {"type": "string", "description": "Target node ID — must exactly match a node id from the nodes array"},
                        "edge_type": {
                            "type": "string",
                            "enum": ["normal", "conditional", "default", "loop"],
                            "description": "Type of edge",
                        },
                        "probability": {"type": "number", "description": "Transition probability (0-1)"},
                        "condition": {"type": "string", "description": "Condition label"},
                    },
                },
            },
        },
    },
}
