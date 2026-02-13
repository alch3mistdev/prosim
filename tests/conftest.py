"""Shared test fixtures."""

import pytest

from prosim.graph.models import (
    Edge,
    EdgeType,
    Node,
    NodeParams,
    NodeType,
    WorkflowGraph,
)


@pytest.fixture
def linear_workflow() -> WorkflowGraph:
    """Simple linear workflow: start -> validate -> process -> end."""
    return WorkflowGraph(
        name="Linear Invoice",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START, params=NodeParams(exec_time_mean=0.0)),
            Node(
                id="validate",
                name="Validate Invoice",
                node_type=NodeType.API,
                params=NodeParams(
                    exec_time_mean=2.0,
                    exec_time_variance=0.5,
                    cost_per_transaction=0.01,
                    error_rate=0.02,
                    max_retries=2,
                    retry_delay=1.0,
                ),
            ),
            Node(
                id="process",
                name="Process Payment",
                node_type=NodeType.API,
                params=NodeParams(
                    exec_time_mean=5.0,
                    exec_time_variance=1.0,
                    cost_per_transaction=0.05,
                    error_rate=0.01,
                    queue_delay_mean=3.0,
                ),
            ),
            Node(id="end", name="End", node_type=NodeType.END, params=NodeParams(exec_time_mean=0.0)),
        ],
        edges=[
            Edge(source="start", target="validate"),
            Edge(source="validate", target="process"),
            Edge(source="process", target="end"),
        ],
    )


@pytest.fixture
def branching_workflow() -> WorkflowGraph:
    """Workflow with decision node and two branches."""
    return WorkflowGraph(
        name="Approval Flow",
        nodes=[
            Node(id="start", name="Start", node_type=NodeType.START, params=NodeParams(exec_time_mean=0.0)),
            Node(
                id="review",
                name="Manual Review",
                node_type=NodeType.HUMAN,
                params=NodeParams(
                    exec_time_mean=300.0,
                    exec_time_variance=100.0,
                    cost_per_transaction=5.0,
                    error_rate=0.03,
                ),
            ),
            Node(
                id="decide",
                name="Approval Decision",
                node_type=NodeType.DECISION,
                params=NodeParams(exec_time_mean=0.1),
            ),
            Node(
                id="approve",
                name="Process Approval",
                node_type=NodeType.API,
                params=NodeParams(
                    exec_time_mean=1.0,
                    cost_per_transaction=0.01,
                ),
            ),
            Node(
                id="reject",
                name="Send Rejection",
                node_type=NodeType.ASYNC,
                params=NodeParams(
                    exec_time_mean=0.5,
                    cost_per_transaction=0.005,
                ),
            ),
            Node(id="end", name="End", node_type=NodeType.END, params=NodeParams(exec_time_mean=0.0)),
        ],
        edges=[
            Edge(source="start", target="review"),
            Edge(source="review", target="decide"),
            Edge(source="decide", target="approve", probability=0.7, edge_type=EdgeType.CONDITIONAL, condition="Approved"),
            Edge(source="decide", target="reject", probability=0.3, edge_type=EdgeType.CONDITIONAL, condition="Rejected"),
            Edge(source="approve", target="end"),
            Edge(source="reject", target="end"),
        ],
    )
