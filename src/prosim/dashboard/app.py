"""ProSim Dashboard — single-page napkin calculator for workflow simulation."""

from __future__ import annotations

import streamlit as st

from prosim.dashboard.components import (
    auto_simulate,
    render_advanced,
    render_dashboard,
    render_input_bar,
    render_node_table,
    render_whatif,
)
from prosim.graph.serialization import graph_to_json, save_graph
from prosim.simulation.results import SimulationConfig

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ProSim",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    "<h2 style='margin-bottom:0'>ProSim</h2>"
    "<p style='color:gray;margin-top:0'>Workflow simulation — rapid napkin calculations</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "baseline_results" not in st.session_state:
    st.session_state.baseline_results = None

# ---------------------------------------------------------------------------
# Sidebar — global simulation config + file ops
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Config")
    volume_per_hour = st.number_input(
        "Volume / hour",
        value=100.0,
        min_value=0.1,
        step=10.0,
        help="Transaction volume entering the process per hour",
    )
    num_transactions = st.number_input(
        "Transactions",
        value=10_000,
        min_value=100,
        step=1_000,
        help="Sample size for deterministic expected values",
    )

    if st.session_state.workflow:
        st.divider()
        st.header("File")
        wf = st.session_state.workflow
        json_str = __import__("json").dumps(graph_to_json(wf), indent=2)
        st.download_button(
            "Download JSON",
            data=json_str,
            file_name=f"{wf.name.replace(' ', '_').lower()}.json",
            mime="application/json",
            width="stretch",
        )

# ---------------------------------------------------------------------------
# Zone 1: Input bar
# ---------------------------------------------------------------------------

render_input_bar()

# ---------------------------------------------------------------------------
# Auto-simulate when workflow exists but results are stale
# ---------------------------------------------------------------------------

wf = st.session_state.workflow
if wf and st.session_state.baseline_results is None:
    auto_simulate(wf, volume_per_hour, num_transactions)

# ---------------------------------------------------------------------------
# Main content (only shown when a workflow is loaded)
# ---------------------------------------------------------------------------

if not wf:
    st.divider()
    st.markdown(
        "**Get started:** Describe a business process above and click **Generate Workflow**, "
        "or upload an existing workflow JSON file."
    )
    st.stop()

results = st.session_state.baseline_results
config = SimulationConfig(volume_per_hour=volume_per_hour, num_transactions=num_transactions)

# Zone 2: Diagram + Metrics
st.divider()
render_dashboard(wf, results)

# Zone 3: Editable node table
st.divider()
render_node_table(wf, volume_per_hour, num_transactions)

# Zone 4: What-if sliders
st.divider()
render_whatif(wf, results, config)

# Zone 5: Advanced
st.divider()
render_advanced(wf, results, config)
