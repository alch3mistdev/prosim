"""Pydantic models for workflow graph nodes, edges, and the complete graph structure.

Models the system as a control network:
- Nodes = state transforms
- Time = friction
- Cost = energy
- Errors = entropy
- Optimization = entropy reduction under constraint
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class NodeType(str, Enum):
    """Classification of workflow node types."""

    START = "start"
    END = "end"
    HUMAN = "human"
    API = "api"
    ASYNC = "async"
    BATCH = "batch"
    DECISION = "decision"
    PARALLEL_GATEWAY = "parallel_gateway"
    WAIT = "wait"


class EdgeType(str, Enum):
    """Classification of edge types."""

    NORMAL = "normal"
    CONDITIONAL = "conditional"
    DEFAULT = "default"
    LOOP = "loop"


class NodeParams(BaseModel):
    """Parameters for a workflow node — the physics of the state transform."""

    # Time (friction)
    exec_time_mean: float = Field(default=1.0, ge=0, description="Mean execution time in seconds")
    exec_time_variance: float = Field(default=0.1, ge=0, description="Variance of execution time")

    # Cost (energy)
    cost_per_transaction: float = Field(default=0.0, ge=0, description="Cost per transaction in currency units")

    # Errors (entropy)
    error_rate: float = Field(default=0.0, ge=0, le=1, description="Probability of error per execution")
    drop_off_rate: float = Field(default=0.0, ge=0, le=1, description="Probability of transaction dropping off")
    sla_breach_probability: float = Field(default=0.0, ge=0, le=1, description="Probability of SLA breach")
    conversion_rate: float = Field(default=1.0, ge=0, le=1, description="Conversion rate through this node")

    # Capacity and throughput
    parallelization_factor: int = Field(default=1, ge=1, description="Number of parallel workers")
    queue_delay_mean: float = Field(default=0.0, ge=0, description="Mean queue delay in seconds")
    queue_delay_variance: float = Field(default=0.0, ge=0, description="Variance of queue delay")
    capacity_per_hour: Optional[float] = Field(default=None, ge=0, description="Max transactions per hour (None=unlimited)")

    # Retry logic
    max_retries: int = Field(default=0, ge=0, description="Maximum retry attempts on error")
    retry_delay: float = Field(default=0.0, ge=0, description="Delay between retries in seconds")

    # Volume
    volume_multiplier: float = Field(default=1.0, ge=0, description="Multiplier for transaction volume at this node")


class Node(BaseModel):
    """A workflow node representing a state transform in the control network."""

    id: str = Field(description="Unique node identifier")
    name: str = Field(description="Human-readable node name")
    node_type: NodeType = Field(description="Classification of this node")
    description: str = Field(default="", description="Description of what this node does")
    params: NodeParams = Field(default_factory=NodeParams, description="Node parameters")

    @field_validator("id")
    @classmethod
    def id_must_be_nonempty(cls, v: str) -> str:
        """Validate that node ID is non-empty."""
        if not v.strip():
            raise ValueError("Node ID must be non-empty")
        return v.strip()


class Edge(BaseModel):
    """A directed edge representing a transition between workflow nodes."""

    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    edge_type: EdgeType = Field(default=EdgeType.NORMAL, description="Type of edge")
    probability: float = Field(default=1.0, ge=0, le=1, description="Transition probability (for decision branches)")
    condition: str = Field(default="", description="Condition label for conditional edges")


class WorkflowGraph(BaseModel):
    """Complete workflow graph with nodes and edges.

    Represents the full control network where:
    - Nodes are state transforms with friction (time), energy (cost), and entropy (errors)
    - Edges are transitions with probabilities
    - The graph supports branching, loops, and parallel paths
    """

    name: str = Field(description="Name of the workflow")
    description: str = Field(default="", description="Description of the workflow")
    nodes: list[Node] = Field(default_factory=list, description="List of workflow nodes")
    edges: list[Edge] = Field(default_factory=list, description="List of workflow edges")

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_start_nodes(self) -> list[Node]:
        """Get all start nodes in the graph."""
        return [n for n in self.nodes if n.node_type == NodeType.START]

    def get_end_nodes(self) -> list[Node]:
        """Get all end nodes in the graph."""
        return [n for n in self.nodes if n.node_type == NodeType.END]

    def get_outgoing_edges(self, node_id: str) -> list[Edge]:
        """Get all outgoing edges from a node."""
        return [e for e in self.edges if e.source == node_id]

    def get_incoming_edges(self, node_id: str) -> list[Edge]:
        """Get all incoming edges to a node."""
        return [e for e in self.edges if e.target == node_id]

    def get_decision_nodes(self) -> list[Node]:
        """Get all decision nodes."""
        return [n for n in self.nodes if n.node_type == NodeType.DECISION]

    @property
    def node_ids(self) -> set[str]:
        """Get all node IDs."""
        return {n.id for n in self.nodes}
