"""Generate BPMN-style Mermaid flowchart diagrams from workflow graphs."""

from __future__ import annotations

from prosim.graph.models import EdgeType, NodeType, WorkflowGraph
from prosim.simulation.results import SimulationResults


# Mermaid shape mapping for BPMN-style rendering (v11-compatible)
_NODE_SHAPES = {
    NodeType.START: ("([", "])"),       # Stadium shape for start
    NodeType.END: ("([", "])"),         # Stadium shape for end
    NodeType.HUMAN: ("[/", "/]"),       # Parallelogram for human tasks
    NodeType.API: ("[[", "]]"),         # Subroutine for API calls
    NodeType.ASYNC: ("[[", "]]"),       # Subroutine for async
    NodeType.BATCH: ("[", "]"),         # Rectangle for batch
    NodeType.DECISION: ("{", "}"),      # Diamond for decisions
    NodeType.PARALLEL_GATEWAY: ("{{", "}}"),  # Hexagon for parallel
    NodeType.WAIT: ("(", ")"),          # Rounded for wait
}

_NODE_STYLES = {
    NodeType.START: "fill:#4CAF50,color:#fff",
    NodeType.END: "fill:#f44336,color:#fff",
    NodeType.HUMAN: "fill:#2196F3,color:#fff",
    NodeType.API: "fill:#FF9800,color:#fff",
    NodeType.ASYNC: "fill:#9C27B0,color:#fff",
    NodeType.BATCH: "fill:#607D8B,color:#fff",
    NodeType.DECISION: "fill:#FFC107,color:#000",
    NodeType.PARALLEL_GATEWAY: "fill:#00BCD4,color:#fff",
    NodeType.WAIT: "fill:#795548,color:#fff",
}


def generate_mermaid(
    workflow: WorkflowGraph,
    results: SimulationResults | None = None,
    show_metrics: bool = True,
) -> str:
    """Generate a Mermaid flowchart diagram string.

    Args:
        workflow: The workflow graph to render.
        results: Optional simulation results to annotate nodes with metrics.
        show_metrics: Whether to show metrics on nodes (requires results).
    """
    lines = ["flowchart LR"]

    # Generate node definitions
    for node in workflow.nodes:
        open_delim, close_delim = _NODE_SHAPES.get(node.node_type, ("[", "]"))
        label = node.name

        if show_metrics and results:
            nm = results.get_node_metrics(node.id)
            if nm and nm.transactions_processed > 0:
                label += f"\n{nm.avg_time:.1f}s / ${nm.avg_cost:.2f}"

        safe_id = _safe_id(node.id)
        escaped_label = _escape(label)
        lines.append(f"    {safe_id}{open_delim}\"{escaped_label}\"{close_delim}")

    lines.append("")

    # Generate edges
    for edge in workflow.edges:
        src = _safe_id(edge.source)
        tgt = _safe_id(edge.target)

        if edge.edge_type == EdgeType.LOOP:
            arrow = "-.->"
        elif edge.edge_type == EdgeType.CONDITIONAL:
            arrow = "-->"
        else:
            arrow = "-->"

        label = ""
        if edge.condition:
            label = _escape_edge(edge.condition)
        elif edge.probability < 1.0:
            label = f"{edge.probability:.0%}"

        if label:
            lines.append(f"    {src} {arrow}|{label}| {tgt}")
        else:
            lines.append(f"    {src} {arrow} {tgt}")

    lines.append("")

    # Generate styles
    styled = set()
    for node in workflow.nodes:
        style = _NODE_STYLES.get(node.node_type)
        if style and node.node_type not in styled:
            # Collect all nodes of this type
            node_ids = [
                _safe_id(n.id)
                for n in workflow.nodes
                if n.node_type == node.node_type
            ]
            for nid in node_ids:
                lines.append(f"    style {nid} {style}")
            styled.add(node.node_type)

    return "\n".join(lines)


def _safe_id(node_id: str) -> str:
    """Convert node ID to a Mermaid-safe identifier.

    Prefixes with ``n_`` to avoid conflicts with Mermaid reserved words
    (``end``, ``graph``, ``subgraph``, etc.).
    """
    safe = node_id.replace("-", "_").replace(" ", "_").replace(".", "_")
    return f"n_{safe}"


def _escape(text: str) -> str:
    """Escape special Mermaid characters in labels (v11-compatible).

    Handles: ``#`` (entity prefix), ``"`` (label delimiter), ``$`` (KaTeX
    trigger in v11+), and newlines (converted to ``<br/>`` for HTML labels).
    """
    text = text.replace("#", "#35;")    # Must escape # first (before adding entity refs)
    text = text.replace('"', "'")       # Quotes would break label delimiters
    text = text.replace("$", "#36;")    # Dollar triggers KaTeX math mode in Mermaid v11+
    text = text.replace("\n", "<br/>")  # HTML line breaks for multi-line labels
    return text


def _escape_edge(text: str) -> str:
    """Escape text for Mermaid edge labels (between ``|`` delimiters)."""
    text = _escape(text)
    text = text.replace("|", "#124;")   # Pipe would close the edge label
    return text
