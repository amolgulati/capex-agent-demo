"""Streamlit UI for the CapEx Close Agent Demo."""

import os
import sys
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent.orchestrator import (
    AgentOrchestrator,
    DoneEvent,
    ErrorEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from agent.tools import generate_outlook_load_file
from utils.excel_export import generate_close_package

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="CapEx Close Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1E2329;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="stMetric"] label {
        color: #4CAF50;
    }

    /* Tool breadcrumb style */
    .tool-breadcrumb {
        background-color: #1E2329;
        border-left: 3px solid #4CAF50;
        padding: 6px 12px;
        margin: 4px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.85em;
        color: #aaa;
    }

    /* Streamlit chat message tweaks */
    .stChatMessage {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []  # display messages: [{role, content}]
if "api_messages" not in st.session_state:
    st.session_state.api_messages = []  # Claude API messages (includes tool_use/tool_result)
if "tools_called" not in st.session_state:
    st.session_state.tools_called = []
if "run_agent" not in st.session_state:
    st.session_state.run_agent = False

TOOL_DISPLAY_NAMES = {
    "load_wbs_master": "Loading WBS Master Data",
    "calculate_accruals": "Step 1: Calculating Accruals",
    "calculate_net_down": "Step 2: WI% Net-Down Adjustments",
    "calculate_outlook": "Step 3: Future Outlook",
    "get_exceptions": "Reviewing Exceptions",
    "get_well_detail": "Well Detail Lookup",
    "generate_journal_entry": "Generating Journal Entry",
    "get_close_summary": "Generating Close Summary",
    "generate_outlook_load_file": "Generating OneStream Load File",
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("CapEx Close Agent")
    st.caption("Monthly Close Demo — January 2026")

    st.divider()

    # Status
    st.subheader("Agent Status")
    if st.session_state.tools_called:
        last_tool = st.session_state.tools_called[-1]
        st.success(f"Last: {TOOL_DISPLAY_NAMES.get(last_tool, last_tool)}")
    else:
        st.info("Waiting for input...")

    # Tool call history
    if st.session_state.tools_called:
        st.subheader("Tools Used")
        for i, t in enumerate(st.session_state.tools_called, 1):
            st.text(f"  {i}. {TOOL_DISPLAY_NAMES.get(t, t)}")

    st.divider()

    # Data summary
    st.subheader("Data")
    from utils.data_loader import load_wbs_master

    @st.cache_data
    def _load_summary():
        df = load_wbs_master()
        return {
            "wells": len(df),
            "bus": list(df["business_unit"].unique()),
        }

    summary = _load_summary()
    st.metric("Wells", summary["wells"])
    st.caption(f"BUs: {', '.join(summary['bus'])}")

    st.divider()

    # Downloads
    st.subheader("Downloads")

    @st.cache_data
    def _generate_excel():
        return generate_close_package()

    @st.cache_data
    def _generate_csv():
        result = generate_outlook_load_file()
        return result["load_file"].to_csv(index=False)

    st.download_button(
        label="Close Package (Excel)",
        data=_generate_excel(),
        file_name="capex_close_package_2026-01.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.download_button(
        label="OneStream Load File (CSV)",
        data=_generate_csv(),
        file_name="onestream_load_2026-01.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()

    # Reset
    if st.button("Reset Conversation", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.session_state.tools_called = []
        st.session_state.run_agent = False
        st.rerun()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.title("CapEx Monthly Close Agent")
st.caption("AI-powered capital expenditure close process — January 2026")

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

if prompt := st.chat_input("Ask the agent to run the monthly close..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set. Create a .env file with your key.")
        st.stop()

    model = os.environ.get("CAPEX_MODEL", "claude-sonnet-4-6")
    agent = AgentOrchestrator(api_key=api_key, model=model)

    with st.chat_message("assistant"):
        response_container = st.empty()
        breadcrumb_container = st.container()
        full_response = ""

        try:
            for event in agent.run(st.session_state.api_messages):
                if isinstance(event, ToolCallEvent):
                    st.session_state.tools_called.append(event.tool_name)
                    display_name = TOOL_DISPLAY_NAMES.get(event.tool_name, event.tool_name)
                    breadcrumb_container.markdown(
                        f'<div class="tool-breadcrumb">🔧 {display_name}</div>',
                        unsafe_allow_html=True,
                    )
                elif isinstance(event, TextEvent):
                    full_response += event.text
                    response_container.markdown(full_response + "▌")
                elif isinstance(event, DoneEvent):
                    response_container.markdown(full_response)
                elif isinstance(event, ErrorEvent):
                    st.error(f"Error: {event.message}")
        except Exception as e:
            st.error(f"Agent error: {e}")

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
