"""Reusable Streamlit UI components for the ProSim dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from prosim.export.mermaid import generate_mermaid
from prosim.graph.models import WorkflowGraph
from prosim.graph.serialization import graph_from_json, graph_to_json, load_graph, save_graph
from prosim.intervention.engine import apply_interventions
from prosim.intervention.leverage import rank_leverage
from prosim.intervention.models import Intervention
from prosim.simulation.bottleneck import detect_bottlenecks
from prosim.simulation.deterministic import run_deterministic
from prosim.simulation.montecarlo import run_monte_carlo
from prosim.simulation.results import SimulationConfig, SimulationMode
from prosim.simulation.sensitivity import run_sensitivity_analysis


def render_generation_panel() -> None:
    """Render the workflow generation panel."""
    st.header("Generate Workflow from Description")

    col1, col2 = st.columns([2, 1])

    with col1:
        description = st.text_area(
            "Process Description",
            placeholder="e.g., invoice processing system, KYC onboarding flow, support ticket lifecycle",
            height=150,
        )

    with col2:
        st.markdown("**Or load from file:**")
        uploaded = st.file_uploader("Upload workflow JSON", type=["json"])
        if uploaded:
            data = json.load(uploaded)
            st.session_state.workflow = graph_from_json(data)
            st.success(f"Loaded: {st.session_state.workflow.name}")

    if st.button("Generate Workflow", type="primary", disabled=not description):
        with st.spinner("Generating workflow via Claude API..."):
            try:
                from prosim.parser.client import generate_workflow_raw
                from prosim.parser.postprocess import postprocess_raw_workflow

                raw = generate_workflow_raw(description)
                workflow = postprocess_raw_workflow(raw)
                st.session_state.workflow = workflow
                st.session_state.results = None
                st.session_state.comparison = None
                st.success(f"Generated: {workflow.name} ({len(workflow.nodes)} nodes, {len(workflow.edges)} edges)")
            except Exception as e:
                st.error(f"Generation failed: {e}")

    # Quick display if workflow exists
    if st.session_state.workflow:
        wf = st.session_state.workflow
        st.divider()
        st.subheader(f"Current Workflow: {wf.name}")
        st.caption(f"{len(wf.nodes)} nodes, {len(wf.edges)} edges")

        # Save option
        col_save1, col_save2 = st.columns([1, 3])
        with col_save1:
            save_path = st.text_input("Save path", value="workflow.json")
        with col_save2:
            if st.button("Save Workflow"):
                save_graph(wf, save_path)
                st.success(f"Saved to {save_path}")


def render_graph_viewer() -> None:
    """Render the graph visualization and parameter editor."""
    st.header("Workflow Graph")

    if not st.session_state.workflow:
        st.info("No workflow loaded. Go to 'Generate Workflow' first.")
        return

    wf = st.session_state.workflow
    results = st.session_state.results

    # Mermaid diagram
    show_metrics = st.checkbox("Show metrics on diagram", value=bool(results))
    mermaid_str = generate_mermaid(wf, results=results, show_metrics=show_metrics)

    st.subheader("BPMN Diagram (Mermaid)")
    st.code(mermaid_str, language="mermaid")

    # Node parameter editor
    st.subheader("Node Parameters")
    selected_node_id = st.selectbox(
        "Select Node",
        [n.id for n in wf.nodes],
        format_func=lambda nid: f"{nid}: {wf.get_node(nid).name}" if wf.get_node(nid) else nid,
    )

    if selected_node_id:
        node = wf.get_node(selected_node_id)
        if node:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Time Parameters**")
                node.params.exec_time_mean = st.number_input(
                    "Exec Time Mean (s)", value=node.params.exec_time_mean, min_value=0.0, key=f"etm_{selected_node_id}"
                )
                node.params.exec_time_variance = st.number_input(
                    "Exec Time Variance", value=node.params.exec_time_variance, min_value=0.0, key=f"etv_{selected_node_id}"
                )
                node.params.queue_delay_mean = st.number_input(
                    "Queue Delay Mean (s)", value=node.params.queue_delay_mean, min_value=0.0, key=f"qdm_{selected_node_id}"
                )

            with col2:
                st.markdown("**Cost & Error Parameters**")
                node.params.cost_per_transaction = st.number_input(
                    "Cost/Transaction ($)", value=node.params.cost_per_transaction, min_value=0.0, key=f"cpt_{selected_node_id}"
                )
                node.params.error_rate = st.number_input(
                    "Error Rate", value=node.params.error_rate, min_value=0.0, max_value=1.0, key=f"er_{selected_node_id}"
                )
                node.params.drop_off_rate = st.number_input(
                    "Drop-off Rate", value=node.params.drop_off_rate, min_value=0.0, max_value=1.0, key=f"dor_{selected_node_id}"
                )

            with col3:
                st.markdown("**Capacity Parameters**")
                node.params.parallelization_factor = st.number_input(
                    "Parallel Workers", value=node.params.parallelization_factor, min_value=1, key=f"pf_{selected_node_id}"
                )
                node.params.max_retries = st.number_input(
                    "Max Retries", value=node.params.max_retries, min_value=0, key=f"mr_{selected_node_id}"
                )
                cap = node.params.capacity_per_hour or 0.0
                new_cap = st.number_input(
                    "Capacity/Hour (0=unlimited)", value=cap, min_value=0.0, key=f"cph_{selected_node_id}"
                )
                node.params.capacity_per_hour = new_cap if new_cap > 0 else None

    # JSON view
    with st.expander("Raw JSON"):
        st.json(graph_to_json(wf))


def render_simulation_panel() -> None:
    """Render the simulation controls and results."""
    st.header("Simulation")

    if not st.session_state.workflow:
        st.info("No workflow loaded. Go to 'Generate Workflow' first.")
        return

    wf = st.session_state.workflow

    col1, col2, col3 = st.columns(3)
    with col1:
        mode = st.selectbox("Mode", ["deterministic", "monte_carlo"])
    with col2:
        num_tx = st.number_input("Transactions", value=10000, min_value=1, max_value=1000000, step=1000)
    with col3:
        volume = st.number_input("Volume/Hour", value=100.0, min_value=0.1)

    col4, col5 = st.columns(2)
    with col4:
        seed = st.number_input("Random Seed", value=42, min_value=0)
    with col5:
        run_sens = st.checkbox("Run Sensitivity Analysis")

    if st.button("Run Simulation", type="primary"):
        config = SimulationConfig(
            mode=SimulationMode(mode),
            num_transactions=num_tx,
            seed=seed,
            volume_per_hour=volume,
        )

        with st.spinner(f"Running {mode} simulation ({num_tx:,} transactions)..."):
            if mode == "deterministic":
                results = run_deterministic(wf, config)
            else:
                results = run_monte_carlo(wf, config)

            results.bottlenecks = detect_bottlenecks(results)

            if run_sens:
                results.sensitivity = run_sensitivity_analysis(wf, config)

            st.session_state.results = results

    # Display results
    results = st.session_state.results
    if results:
        st.divider()

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Time", f"{results.avg_total_time:.2f}s")
        m2.metric("Avg Cost", f"${results.avg_total_cost:.4f}")
        m3.metric("Throughput", f"{results.throughput_per_hour:.0f}/hr")
        m4.metric("Completion", f"{results.completed_transactions:,}/{results.total_transactions:,}")

        # Node metrics table
        st.subheader("Node Metrics")
        node_data = []
        for nm in sorted(results.node_metrics, key=lambda m: m.bottleneck_score, reverse=True):
            if nm.transactions_processed > 0:
                node_data.append({
                    "Node": nm.node_name,
                    "Avg Time (s)": round(nm.avg_time, 2),
                    "Avg Cost ($)": round(nm.avg_cost, 4),
                    "Processed": nm.transactions_processed,
                    "Errors": nm.transactions_errored,
                    "Utilization": f"{nm.utilization:.1%}",
                    "Bottleneck Score": round(nm.bottleneck_score, 4),
                })
        if node_data:
            st.dataframe(node_data, use_container_width=True)

        # Bottlenecks
        if results.bottlenecks:
            st.subheader("Top Bottlenecks")
            for bn in results.bottlenecks[:3]:
                st.warning(f"**{bn.node_name}** — Score: {bn.score:.4f} — {bn.reason} ({bn.time_contribution_pct:.1f}% of total time)")

        # Sensitivity / Leverage
        if results.sensitivity:
            st.subheader("Leverage Rankings")
            rankings = rank_leverage(wf, results.sensitivity)
            for i, r in enumerate(rankings[:5], 1):
                st.info(f"**#{i} {r.node_name}** ({r.parameter}) — Score: {r.leverage_score:.4f} — {r.recommendation}")


def render_intervention_panel() -> None:
    """Render the intervention builder and delta display."""
    st.header("Intervene & Optimize")

    if not st.session_state.workflow:
        st.info("No workflow loaded. Go to 'Generate Workflow' first.")
        return

    wf = st.session_state.workflow

    st.subheader("Configure Intervention")

    node_id = st.selectbox(
        "Target Node",
        [n.id for n in wf.nodes],
        format_func=lambda nid: f"{nid}: {wf.get_node(nid).name}" if wf.get_node(nid) else nid,
        key="intervention_node",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        time_red = st.slider("Time Reduction %", 0, 100, 0, key="int_time")
        cost_red = st.slider("Cost Reduction %", 0, 100, 0, key="int_cost")
    with col2:
        error_red = st.slider("Error Reduction %", 0, 100, 0, key="int_error")
        queue_red = st.slider("Queue Reduction %", 0, 100, 0, key="int_queue")
    with col3:
        cap_inc = st.slider("Capacity Increase %", 0, 200, 0, key="int_cap")
        add_workers = st.number_input("Additional Workers", 0, 100, 0, key="int_workers")

    impl_cost = st.number_input("Implementation Cost ($)", 0.0, key="int_impl_cost")
    volume = st.number_input("Volume/Hour", value=100.0, min_value=0.1, key="int_volume")

    if st.button("Apply Intervention", type="primary"):
        intervention = Intervention(
            node_id=node_id,
            time_reduction_pct=float(time_red),
            cost_reduction_pct=float(cost_red),
            error_reduction_pct=float(error_red),
            capacity_increase_pct=float(cap_inc),
            parallelization_increase=add_workers,
            queue_reduction_pct=float(queue_red),
            implementation_cost=impl_cost,
        )

        config = SimulationConfig(volume_per_hour=volume)
        baseline = run_deterministic(wf, config)

        comparison = apply_interventions(wf, [intervention], baseline, config)
        st.session_state.comparison = comparison

    # Display comparison
    comparison = st.session_state.comparison
    if comparison:
        st.divider()
        st.subheader("Baseline vs. Optimized")

        for delta in comparison.deltas:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(delta.metric_name, f"{delta.baseline_value:.4f}", label_visibility="visible")
            col_b.metric("Optimized", f"{delta.optimized_value:.4f}")

            is_improvement = delta.relative_change_pct < 0
            if "Throughput" in delta.metric_name or "Completed" in delta.metric_name:
                is_improvement = delta.relative_change_pct > 0

            col_c.metric(
                "Change",
                f"{delta.relative_change_pct:+.2f}%",
                delta=f"{delta.absolute_change:+.4f}",
                delta_color="normal" if is_improvement else "inverse",
            )

        st.divider()
        st.subheader("ROI Summary")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Time Saved", f"{comparison.time_saved_pct:.1f}%")
        r2.metric("Cost Saved", f"{comparison.cost_saved_pct:.1f}%")
        r3.metric("Annual Savings", f"${comparison.annual_cost_savings:,.2f}")
        if comparison.roi_ratio is not None:
            r4.metric("ROI", f"{comparison.roi_ratio:.1f}x")
