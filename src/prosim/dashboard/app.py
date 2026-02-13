"""Streamlit dashboard entry point for ProSim."""

from __future__ import annotations

import streamlit as st

from prosim.dashboard.components import (
    render_generation_panel,
    render_graph_viewer,
    render_intervention_panel,
    render_simulation_panel,
)

st.set_page_config(
    page_title="ProSim - Workflow Simulation Engine",
    page_icon="⚙️",
    layout="wide",
)

st.title("ProSim — Workflow Simulation Engine")
st.caption("Generate, simulate, and optimize business process workflows")

# Initialize session state
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "results" not in st.session_state:
    st.session_state.results = None
if "comparison" not in st.session_state:
    st.session_state.comparison = None

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Generate Workflow", "View & Edit Graph", "Simulate", "Intervene & Optimize"],
)

if page == "Generate Workflow":
    render_generation_panel()
elif page == "View & Edit Graph":
    render_graph_viewer()
elif page == "Simulate":
    render_simulation_panel()
elif page == "Intervene & Optimize":
    render_intervention_panel()
