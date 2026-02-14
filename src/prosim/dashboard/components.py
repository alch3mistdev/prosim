"""Streamlit UI components for the ProSim single-page napkin calculator dashboard."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from prosim.export.mermaid import generate_mermaid
from prosim.graph.models import NodeType, WorkflowGraph
from prosim.graph.serialization import graph_from_json, graph_to_json, save_graph
from prosim.intervention.engine import apply_interventions
from prosim.intervention.leverage import rank_leverage
from prosim.intervention.models import Intervention
from prosim.simulation.bottleneck import detect_bottlenecks
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.montecarlo import run_monte_carlo
from prosim.simulation.results import SimulationConfig, SimulationMode
from prosim.simulation.sensitivity import run_sensitivity_analysis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render_mermaid_html(mermaid_code: str, height: int = 400) -> None:
    """Render a Mermaid diagram as a visual SVG via Mermaid.js CDN.

    Uses ``mermaid.render()`` API to pass the diagram code as a JS string,
    avoiding browser HTML parsing that would corrupt entity refs and ``<br/>``
    tags before Mermaid sees them.
    """
    # JSON-encode so the code is a safe JS string literal (handles quotes,
    # backslashes, newlines, angle brackets, etc.)
    js_code_literal = json.dumps(mermaid_code)

    html = f"""<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  body {{ margin:0; padding:8px; background:transparent; font-family:sans-serif; }}
  #output {{ text-align:center; }}
  #output svg {{ max-width:100%; height:auto; }}
  .error {{ color:#c00; font-family:monospace; white-space:pre-wrap; padding:1em; }}
</style>
</head>
<body>
<div id="output"></div>
<script>
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'neutral',
    flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }},
    securityLevel: 'loose'
  }});

  mermaid.render('mermaid-diagram', {js_code_literal}).then(function(result) {{
    document.getElementById('output').innerHTML = result.svg;
  }}).catch(function(err) {{
    document.getElementById('output').innerHTML =
      '<div class="error">' + err.message + '</div>';
  }});
</script>
</body>
</html>"""
    components.html(html, height=height, scrolling=True)


def build_node_dataframe(wf: WorkflowGraph) -> pd.DataFrame:
    """Convert workflow nodes into an editable DataFrame for st.data_editor."""
    rows = []
    for node in wf.nodes:
        p = node.params
        rows.append({
            "id": node.id,
            "Name": node.name,
            "Type": node.node_type.value,
            "Time (s)": round(p.exec_time_mean, 2),
            "Queue (s)": round(p.queue_delay_mean, 2),
            "Cost ($)": round(p.cost_per_transaction, 4),
            "Error %": round(p.error_rate * 100, 2),
            "Drop %": round(p.drop_off_rate * 100, 2),
            "Workers": p.parallelization_factor,
            "Cap/hr": p.capacity_per_hour if p.capacity_per_hour else 0.0,
        })
    return pd.DataFrame(rows)


def apply_table_edits(wf: WorkflowGraph, edited_df: pd.DataFrame) -> bool:
    """Write DataFrame values back into the WorkflowGraph. Returns True if anything changed."""
    changed = False
    for _, row in edited_df.iterrows():
        node = wf.get_node(row["id"])
        if not node:
            continue
        p = node.params

        mappings: list[tuple[str, str, float]] = [
            ("Time (s)", "exec_time_mean", row["Time (s)"]),
            ("Queue (s)", "queue_delay_mean", row["Queue (s)"]),
            ("Cost ($)", "cost_per_transaction", row["Cost ($)"]),
        ]
        for _, attr, new_val in mappings:
            if abs(float(new_val) - getattr(p, attr)) > 1e-9:
                setattr(p, attr, float(new_val))
                changed = True

        # Error / drop are displayed as percentages, stored as 0-1
        new_error = float(row["Error %"]) / 100.0
        if abs(new_error - p.error_rate) > 1e-9:
            p.error_rate = max(0.0, min(1.0, new_error))
            changed = True

        new_drop = float(row["Drop %"]) / 100.0
        if abs(new_drop - p.drop_off_rate) > 1e-9:
            p.drop_off_rate = max(0.0, min(1.0, new_drop))
            changed = True

        new_workers = max(1, int(row["Workers"]))
        if new_workers != p.parallelization_factor:
            p.parallelization_factor = new_workers
            changed = True

        new_cap = float(row["Cap/hr"])
        old_cap = p.capacity_per_hour if p.capacity_per_hour else 0.0
        if abs(new_cap - old_cap) > 1e-9:
            p.capacity_per_hour = new_cap if new_cap > 0 else None
            changed = True

    return changed


def auto_simulate(wf: WorkflowGraph, volume: float, num_tx: int) -> None:
    """Run deterministic simulation and store in session state."""
    config = SimulationConfig(volume_per_hour=volume, num_transactions=num_tx)
    results = run_deterministic(wf, config)
    results.bottlenecks = detect_bottlenecks(results)
    st.session_state.baseline_results = results


def _format_time(seconds: float) -> str:
    """Format seconds into a human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


# ---------------------------------------------------------------------------
# Zone 1: Input Bar
# ---------------------------------------------------------------------------

def render_input_bar() -> None:
    """Zone 1 — process description input, generate button, and file upload."""
    col_input, col_actions = st.columns([3, 1])

    with col_input:
        description = st.text_area(
            "Describe your process",
            placeholder='e.g. "invoice processing: receive invoice, validate, approve/reject, schedule payment, send confirmation"',
            height=80,
            label_visibility="collapsed",
        )

    with col_actions:
        generate_clicked = st.button(
            "Generate Workflow",
            type="primary",
            disabled=not description,
            width="stretch",
        )
        uploaded = st.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")

    # Handle file upload
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.workflow = graph_from_json(data)
            st.session_state.baseline_results = None
            st.toast(f"Loaded: {st.session_state.workflow.name}")
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

    # Handle generate
    if generate_clicked and description:
        with st.spinner("Generating workflow via Claude API..."):
            try:
                from prosim.parser.client import generate_workflow_raw
                from prosim.parser.postprocess import postprocess_raw_workflow

                raw = generate_workflow_raw(description)
                workflow = postprocess_raw_workflow(raw)
                st.session_state.workflow = workflow
                st.session_state.baseline_results = None
                st.toast(f"Generated: {workflow.name} ({len(workflow.nodes)} nodes)")
            except Exception as e:
                st.error(f"Generation failed: {e}")


# ---------------------------------------------------------------------------
# Zone 2: Dashboard — Diagram + Metrics
# ---------------------------------------------------------------------------

def render_dashboard(wf: WorkflowGraph, results) -> None:
    """Zone 2 — visual Mermaid diagram (left) + metric cards and bottlenecks (right)."""
    col_diagram, col_metrics = st.columns([3, 2])

    with col_diagram:
        show_metrics = results is not None
        mermaid_str = generate_mermaid(wf, results=results, show_metrics=show_metrics)

        # Dynamic height based on node count
        diagram_height = max(300, min(800, len(wf.nodes) * 55))
        render_mermaid_html(mermaid_str, height=diagram_height)

    with col_metrics:
        if results:
            # Key metric cards — 2x2 grid
            m1, m2 = st.columns(2)
            m1.metric("Avg Time", _format_time(results.avg_total_time))
            m2.metric("Avg Cost", f"${results.avg_total_cost:.4f}")

            m3, m4 = st.columns(2)
            m3.metric("Throughput", f"{results.throughput_per_hour:,.0f}/hr")
            completion_pct = (
                results.completed_transactions / max(results.total_transactions, 1)
            ) * 100
            m4.metric("Completion", f"{completion_pct:.1f}%")

            # Bottleneck chips
            if results.bottlenecks:
                st.markdown("##### Top Bottlenecks")
                for bn in results.bottlenecks[:3]:
                    st.caption(
                        f"**{bn.node_name}** — {bn.reason} "
                        f"({bn.time_contribution_pct:.0f}% of time)"
                    )
        else:
            st.info("Simulation results will appear here automatically.")


# ---------------------------------------------------------------------------
# Zone 3: Editable Node Table
# ---------------------------------------------------------------------------

def render_node_table(wf: WorkflowGraph, volume: float, num_tx: int) -> None:
    """Zone 3 — editable node parameter table with auto re-simulation on change."""
    st.markdown("##### Node Parameters")
    st.caption("Edit any cell to re-simulate instantly")

    df = build_node_dataframe(wf)

    edited_df = st.data_editor(
        df,
        key="node_editor",
        width="stretch",
        hide_index=True,
        disabled=["id", "Name", "Type"],
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Time (s)": st.column_config.NumberColumn(
                "Time (s)", min_value=0.0, format="%.2f",
                help="Mean execution time in seconds",
            ),
            "Queue (s)": st.column_config.NumberColumn(
                "Queue (s)", min_value=0.0, format="%.2f",
                help="Mean queue delay in seconds",
            ),
            "Cost ($)": st.column_config.NumberColumn(
                "Cost ($)", min_value=0.0, format="%.4f",
                help="Cost per transaction in USD",
            ),
            "Error %": st.column_config.NumberColumn(
                "Error %", min_value=0.0, max_value=100.0, format="%.2f",
                help="Error probability as percentage",
            ),
            "Drop %": st.column_config.NumberColumn(
                "Drop %", min_value=0.0, max_value=100.0, format="%.2f",
                help="Drop-off probability as percentage",
            ),
            "Workers": st.column_config.NumberColumn(
                "Workers", min_value=1, step=1, format="%d",
                help="Number of parallel workers",
            ),
            "Cap/hr": st.column_config.NumberColumn(
                "Cap/hr", min_value=0.0, format="%.0f",
                help="Max capacity per hour (0 = unlimited)",
            ),
        },
    )

    if apply_table_edits(wf, edited_df):
        auto_simulate(wf, volume, num_tx)
        st.rerun()


# ---------------------------------------------------------------------------
# Zone 4: What-If Sliders
# ---------------------------------------------------------------------------

def render_whatif(wf: WorkflowGraph, baseline, config: SimulationConfig) -> None:
    """Zone 4 — select a node, drag sliders, see live delta metrics."""
    st.markdown("##### What-If Analysis")

    # Filter to non-trivial nodes (skip start/end)
    actionable_nodes = [
        n for n in wf.nodes
        if n.node_type not in (NodeType.START, NodeType.END)
    ]
    if not actionable_nodes:
        return

    wi_node, wi_sliders, wi_results = st.columns([1, 2, 2])

    with wi_node:
        target_id = st.selectbox(
            "Target node",
            [n.id for n in actionable_nodes],
            format_func=lambda nid: wf.get_node(nid).name if wf.get_node(nid) else nid,
            key="wi_target",
        )
        show_advanced = st.checkbox("More sliders", key="wi_advanced")

    with wi_sliders:
        time_red = st.slider("Time reduction %", 0, 80, 0, step=5, key="wi_time")
        cost_red = st.slider("Cost reduction %", 0, 80, 0, step=5, key="wi_cost")
        error_red = st.slider("Error reduction %", 0, 80, 0, step=5, key="wi_error")

        queue_red = 0
        add_workers = 0
        impl_cost = 0.0
        if show_advanced:
            queue_red = st.slider("Queue reduction %", 0, 80, 0, step=5, key="wi_queue")
            add_workers = st.slider("Add workers", 0, 10, 0, key="wi_workers")
            impl_cost = st.number_input("Implementation cost ($)", 0.0, step=1000.0, key="wi_impl")

    with wi_results:
        has_change = (time_red > 0 or cost_red > 0 or error_red > 0
                      or queue_red > 0 or add_workers > 0)

        if has_change and baseline:
            intervention = Intervention(
                node_id=target_id,
                time_reduction_pct=float(time_red),
                cost_reduction_pct=float(cost_red),
                error_reduction_pct=float(error_red),
                queue_reduction_pct=float(queue_red),
                parallelization_increase=add_workers,
                implementation_cost=impl_cost,
            )
            comparison = apply_interventions(wf, [intervention], baseline, config)

            st.metric(
                "Time saved",
                f"{comparison.time_saved_pct:+.1f}%",
                delta=f"{comparison.time_saved_pct:+.1f}%",
                delta_color="normal" if comparison.time_saved_pct > 0 else "off",
            )
            st.metric(
                "Cost saved",
                f"{comparison.cost_saved_pct:+.1f}%",
                delta=f"{comparison.cost_saved_pct:+.1f}%",
                delta_color="normal" if comparison.cost_saved_pct > 0 else "off",
            )
            st.metric(
                "Throughput",
                f"{comparison.throughput_increase_pct:+.1f}%",
                delta=f"{comparison.throughput_increase_pct:+.1f}%",
                delta_color="normal" if comparison.throughput_increase_pct > 0 else "off",
            )
            if comparison.annual_cost_savings != 0:
                st.caption(f"Annual savings: **${comparison.annual_cost_savings:,.0f}**")
            if comparison.roi_ratio is not None and comparison.roi_ratio > 0:
                st.caption(f"ROI: **{comparison.roi_ratio:.1f}x** | Payback: **{comparison.payback_months:.0f}mo**")
        else:
            st.caption("Move the sliders to see the impact of changes on this node.")


# ---------------------------------------------------------------------------
# Zone 5: Advanced (Expanders)
# ---------------------------------------------------------------------------

def render_advanced(wf: WorkflowGraph, results, config: SimulationConfig) -> None:
    """Zone 5 — Monte Carlo, sensitivity analysis, and export in expanders."""

    with st.expander("Monte Carlo Simulation"):
        mc1, mc2 = st.columns(2)
        with mc1:
            mc_tx = st.number_input(
                "Transactions", value=100_000, min_value=100,
                max_value=1_000_000, step=10_000, key="mc_tx",
            )
        with mc2:
            mc_seed = st.number_input("Seed", value=42, min_value=0, key="mc_seed")

        if st.button("Run Monte Carlo", type="secondary"):
            mc_config = SimulationConfig(
                mode=SimulationMode.MONTE_CARLO,
                num_transactions=mc_tx,
                seed=mc_seed,
                volume_per_hour=config.volume_per_hour,
            )
            with st.spinner(f"Simulating {mc_tx:,} transactions..."):
                mc_results = run_monte_carlo(wf, mc_config)
                mc_results.bottlenecks = detect_bottlenecks(mc_results)

            d1, d2, d3 = st.columns(3)
            d1.metric("P50 Time", _format_time(mc_results.p50_total_time))
            d2.metric("P95 Time", _format_time(mc_results.p95_total_time))
            d3.metric("P99 Time", _format_time(mc_results.p99_total_time))

            d4, d5, d6 = st.columns(3)
            d4.metric("Avg Cost", f"${mc_results.avg_total_cost:.4f}")
            d5.metric("Completed", f"{mc_results.completed_transactions:,}")
            d6.metric("Failed", f"{mc_results.failed_transactions:,}")

    with st.expander("Sensitivity & Leverage"):
        if st.button("Run Sensitivity Analysis", type="secondary"):
            with st.spinner("Analyzing parameter sensitivity..."):
                sensitivity = run_sensitivity_analysis(wf, config)
                rankings = rank_leverage(wf, sensitivity)

            for i, r in enumerate(rankings[:5], 1):
                marker = " **<-- best lever**" if i == 1 else ""
                st.markdown(
                    f"**#{i} {r.node_name}** ({r.parameter}) — "
                    f"time impact {r.time_impact_pct:.1f}%, "
                    f"cost impact {r.cost_impact_pct:.1f}% — "
                    f"{r.recommendation}{marker}"
                )

    with st.expander("Export & Raw Data"):
        json_str = json.dumps(graph_to_json(wf), indent=2)
        st.download_button(
            "Download Workflow JSON",
            data=json_str,
            file_name=f"{wf.name.replace(' ', '_').lower()}.json",
            mime="application/json",
        )

        mermaid_str = generate_mermaid(wf, results=results, show_metrics=results is not None)
        st.code(mermaid_str, language="mermaid")

        if results:
            st.json(results.model_dump(mode="json"))
