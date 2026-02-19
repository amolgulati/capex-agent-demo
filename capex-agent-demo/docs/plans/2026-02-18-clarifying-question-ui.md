# Clarifying Question UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive clarifying question UI so the agent pauses during WI% mismatch detection, renders radio buttons, and resumes after user input.

**Architecture:** New `ask_user_question` tool that the agent calls with a question and options. Orchestrator yields a `ClarifyEvent` and stops. Streamlit renders `st.radio()` + Continue button, then resumes the agent with the user's choice as a tool_result.

**Tech Stack:** Streamlit (st.radio, st.button, st.session_state), Anthropic tool_use API

---

### Task 1: Add `ask_user_question` Tool Definition

**Files:**
- Modify: `capex-agent-demo/agent/tool_definitions.py:7` (append to TOOL_DEFINITIONS list)
- Test: `capex-agent-demo/tests/test_orchestrator.py` (new file)

**Step 1: Write the failing test**

Create `capex-agent-demo/tests/test_orchestrator.py`:

```python
"""Tests for agent orchestrator — tool definitions and event types."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.tool_definitions import TOOL_DEFINITIONS


class TestToolDefinitions:
    """Tool definition schema tests."""

    def test_ask_user_question_tool_exists(self):
        names = [t["name"] for t in TOOL_DEFINITIONS]
        assert "ask_user_question" in names

    def test_ask_user_question_has_required_params(self):
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "ask_user_question")
        schema = tool["input_schema"]
        assert "question" in schema["properties"]
        assert "options" in schema["properties"]
        assert "question" in schema["required"]
        assert "options" in schema["required"]

    def test_ask_user_question_options_is_array_of_strings(self):
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "ask_user_question")
        opts = tool["input_schema"]["properties"]["options"]
        assert opts["type"] == "array"
        assert opts["items"]["type"] == "string"
```

**Step 2: Run test to verify it fails**

Run: `pytest capex-agent-demo/tests/test_orchestrator.py::TestToolDefinitions -v`
Expected: FAIL — `ask_user_question` not in tool names

**Step 3: Add the tool definition**

In `capex-agent-demo/agent/tool_definitions.py`, append to the `TOOL_DEFINITIONS` list (before the closing `]`):

```python
    {
        "name": "ask_user_question",
        "description": (
            "Ask the user a clarifying question and wait for their response. "
            "Use this when you need human judgment before proceeding — for example, "
            "when WI% mismatches are found and you need confirmation to proceed "
            "with net-down adjustments. The user will see radio buttons with your "
            "options and a Continue button."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user.",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 answer choices for the user to pick from.",
                    "minItems": 2,
                    "maxItems": 4,
                },
            },
            "required": ["question", "options"],
        },
    },
```

**Step 4: Run test to verify it passes**

Run: `pytest capex-agent-demo/tests/test_orchestrator.py::TestToolDefinitions -v`
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add capex-agent-demo/agent/tool_definitions.py capex-agent-demo/tests/test_orchestrator.py
git commit -m "feat: add ask_user_question tool definition"
```

---

### Task 2: Add `ClarifyEvent` and Orchestrator Detection

**Files:**
- Modify: `capex-agent-demo/agent/orchestrator.py:77-112` (add ClarifyEvent dataclass)
- Modify: `capex-agent-demo/agent/orchestrator.py:157-205` (tool dispatch section of run())
- Test: `capex-agent-demo/tests/test_orchestrator.py` (add to existing)

**Step 1: Write the failing test**

Append to `capex-agent-demo/tests/test_orchestrator.py`:

```python
from agent.orchestrator import (
    ClarifyEvent,
    TextEvent,
    ToolCallEvent,
    DoneEvent,
)


class TestClarifyEvent:
    """ClarifyEvent dataclass tests."""

    def test_clarify_event_has_required_fields(self):
        evt = ClarifyEvent(
            question="Proceed with adjustments?",
            options=["Yes", "No"],
            tool_use_id="toolu_123",
        )
        assert evt.question == "Proceed with adjustments?"
        assert evt.options == ["Yes", "No"]
        assert evt.tool_use_id == "toolu_123"
        assert evt.type == "clarify"
```

**Step 2: Run test to verify it fails**

Run: `pytest capex-agent-demo/tests/test_orchestrator.py::TestClarifyEvent -v`
Expected: FAIL — cannot import ClarifyEvent

**Step 3: Add ClarifyEvent dataclass**

In `capex-agent-demo/agent/orchestrator.py`, after the `ErrorEvent` class (line ~112), add:

```python
@dataclass
class ClarifyEvent:
    """The agent is asking the user a clarifying question."""
    question: str
    options: list
    tool_use_id: str
    type: str = "clarify"
```

**Step 4: Run test to verify it passes**

Run: `pytest capex-agent-demo/tests/test_orchestrator.py::TestClarifyEvent -v`
Expected: PASS

**Step 5: Modify the orchestrator `run()` method**

In `capex-agent-demo/agent/orchestrator.py`, in the `run()` method, replace the tool processing section (lines ~183-205). After collecting tool_calls, before the existing tool dispatch loop, add detection for `ask_user_question`:

Replace this block (the section starting with `# Process tool calls and build tool results`):

```python
            # Process tool calls and build tool results
            tool_results = []
            for tc in tool_calls:
                result_str = dispatch_tool(tc.name, tc.input)
                # Truncate very large results to stay within token budget
                if len(result_str) > 50_000:
                    result_str = result_str[:50_000] + '..."}'

                yield ToolResultEvent(
                    tool_name=tc.name,
                    result_preview=result_str[:200],
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            # Add tool results as a user message and loop
            messages.append({
                "role": "user",
                "content": tool_results,
            })
```

With:

```python
            # Check for clarifying question tool
            clarify_tc = next(
                (tc for tc in tool_calls if tc.name == "ask_user_question"),
                None,
            )
            if clarify_tc:
                yield ClarifyEvent(
                    question=clarify_tc.input.get("question", ""),
                    options=clarify_tc.input.get("options", []),
                    tool_use_id=clarify_tc.id,
                )
                return  # Pause — UI will resume with tool_result

            # Process tool calls and build tool results
            tool_results = []
            for tc in tool_calls:
                result_str = dispatch_tool(tc.name, tc.input)
                # Truncate very large results to stay within token budget
                if len(result_str) > 50_000:
                    result_str = result_str[:50_000] + '..."}'

                yield ToolResultEvent(
                    tool_name=tc.name,
                    result_preview=result_str[:200],
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            # Add tool results as a user message and loop
            messages.append({
                "role": "user",
                "content": tool_results,
            })
```

**Step 6: Update the import in `__init__` or app.py**

In `capex-agent-demo/app.py` line 14-21, add `ClarifyEvent` to the imports:

```python
from agent.orchestrator import (
    AgentOrchestrator,
    ClarifyEvent,
    DoneEvent,
    ErrorEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
)
```

**Step 7: Run all tests**

Run: `pytest capex-agent-demo/tests/test_orchestrator.py -v`
Expected: All PASS

**Step 8: Commit**

```bash
git add capex-agent-demo/agent/orchestrator.py capex-agent-demo/tests/test_orchestrator.py capex-agent-demo/app.py
git commit -m "feat: add ClarifyEvent and ask_user_question detection in orchestrator"
```

---

### Task 3: Update System Prompt

**Files:**
- Modify: `capex-agent-demo/agent/prompts.py:24-29`

**Step 1: Update the WI% mismatch instruction**

In `capex-agent-demo/agent/prompts.py`, replace the Step 2 section (lines 23-29) that currently reads:

```
### Step 2: WI% Net-Down Adjustments
5. Check for working interest discrepancies (use `calculate_net_down`)
6. **IMPORTANT — Clarifying question:** If WI% mismatches are found, PAUSE and inform \
the user. Present the discrepancies clearly and ask:
   > "I found [N] wells where the Working Interest in the system doesn't match the \
actual WI%. The largest is [well] — system has [X]% but should be [Y]%. \
Should I proceed with the net-down adjustments?"
7. Only proceed after the user confirms
```

With:

```
### Step 2: WI% Net-Down Adjustments
5. Check for working interest discrepancies (use `calculate_net_down`)
6. **IMPORTANT — Clarifying question:** If WI% mismatches are found, use the \
`ask_user_question` tool to pause and ask the user. Include the number of mismatched \
wells and the largest discrepancy in the question. Provide options like:
   - "Yes, proceed with net-down adjustments"
   - "No, skip the net-down step"
   - "Show me the details first"
7. Only proceed after the user confirms via the tool response
```

**Step 2: Run existing tests to verify nothing broke**

Run: `pytest capex-agent-demo/tests/ -v`
Expected: All PASS (prompt changes don't affect tool/data tests)

**Step 3: Commit**

```bash
git add capex-agent-demo/agent/prompts.py
git commit -m "feat: update system prompt to use ask_user_question tool"
```

---

### Task 4: Add Streamlit Pause/Resume UI

**Files:**
- Modify: `capex-agent-demo/app.py:77-84` (session state init)
- Modify: `capex-agent-demo/app.py:172-177` (reset button)
- Modify: `capex-agent-demo/app.py:186-236` (main chat area — major changes)

**Step 1: Add `pending_question` to session state**

In `capex-agent-demo/app.py`, after line 84 (`st.session_state.run_agent = False`), add:

```python
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None  # {question, options, tool_use_id, partial_response}
```

**Step 2: Clear pending_question on reset**

In the reset button handler (line ~173-177), add `st.session_state.pending_question = None`:

```python
    if st.button("Reset Conversation", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.session_state.tools_called = []
        st.session_state.run_agent = False
        st.session_state.pending_question = None
        st.rerun()
```

**Step 3: Rewrite the main chat area**

Replace the entire section from `# Display message history` through end of file (lines ~186-236) with:

```python
# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("breadcrumbs"):
            for bc in msg["breadcrumbs"]:
                st.markdown(
                    f'<div class="tool-breadcrumb">🔧 {bc}</div>',
                    unsafe_allow_html=True,
                )
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Clarifying question widget (rendered when agent is paused)
# ---------------------------------------------------------------------------

if st.session_state.pending_question:
    pq = st.session_state.pending_question

    with st.chat_message("assistant"):
        # Show the partial response text the agent produced before asking
        if pq.get("partial_response"):
            st.markdown(pq["partial_response"])

        # Render interactive widget
        st.divider()
        st.markdown("**🤔 The agent needs your input:**")
        st.markdown(pq["question"])
        choice = st.radio(
            "Select an option:",
            pq["options"],
            key="clarify_radio",
            label_visibility="collapsed",
        )
        if st.button("Continue", type="primary", key="clarify_continue"):
            # Append tool_result to api_messages
            st.session_state.api_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": pq["tool_use_id"],
                    "content": choice,
                }],
            })
            # Store the question + answer in display messages
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"{pq.get('partial_response', '')}\n\n---\n**🤔 {pq['question']}**\n\n> You selected: **{choice}**",
            })
            st.session_state.pending_question = None
            st.session_state.run_agent = True
            st.rerun()


# ---------------------------------------------------------------------------
# Agent runner (handles both fresh input and resumed runs)
# ---------------------------------------------------------------------------

def _run_agent():
    """Run the agent and process events."""
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
        breadcrumbs = []

        try:
            for event in agent.run(st.session_state.api_messages):
                if isinstance(event, ToolCallEvent):
                    st.session_state.tools_called.append(event.tool_name)
                    display_name = TOOL_DISPLAY_NAMES.get(event.tool_name, event.tool_name)
                    breadcrumbs.append(display_name)
                    breadcrumb_container.markdown(
                        f'<div class="tool-breadcrumb">🔧 {display_name}</div>',
                        unsafe_allow_html=True,
                    )
                elif isinstance(event, TextEvent):
                    full_response += event.text
                    response_container.markdown(full_response + "▌")
                elif isinstance(event, ClarifyEvent):
                    # Agent is asking a clarifying question — pause
                    response_container.markdown(full_response)
                    st.session_state.pending_question = {
                        "question": event.question,
                        "options": event.options,
                        "tool_use_id": event.tool_use_id,
                        "partial_response": full_response,
                    }
                    # Store breadcrumbs with partial response
                    if full_response or breadcrumbs:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "breadcrumbs": breadcrumbs,
                        })
                    st.rerun()
                elif isinstance(event, DoneEvent):
                    response_container.markdown(full_response)
                elif isinstance(event, ErrorEvent):
                    st.error(f"Error: {event.message}")
        except Exception as e:
            st.error(f"Agent error: {e}")

    if full_response:
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "breadcrumbs": breadcrumbs,
        })


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

if prompt := st.chat_input("Ask the agent to run the monthly close..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.api_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    _run_agent()

elif st.session_state.run_agent:
    st.session_state.run_agent = False
    _run_agent()
```

**Step 4: Run all tests**

Run: `pytest capex-agent-demo/tests/ -v`
Expected: All existing tests PASS (app.py changes are UI-only, no unit tests break)

**Step 5: Manual smoke test**

Run: `streamlit run capex-agent-demo/app.py`
- Type "Run the monthly close"
- Agent should run Steps 1-2, then show radio buttons for WI% mismatch
- Select an option, click Continue
- Agent should resume and complete Steps 3+

**Step 6: Commit**

```bash
git add capex-agent-demo/app.py
git commit -m "feat: add clarifying question UI with radio buttons and pause/resume"
```

---

### Task 5: Final Integration Test

**Step 1: Run full test suite**

Run: `pytest capex-agent-demo/tests/ -v`
Expected: All PASS

**Step 2: Manual end-to-end test**

Run: `streamlit run capex-agent-demo/app.py`
Verify:
1. Agent starts and runs through Step 1 (accruals)
2. Agent calls calculate_net_down, finds WI% mismatches
3. Agent calls ask_user_question — radio widget appears
4. Select "Yes, proceed with net-down adjustments" and click Continue
5. Agent resumes and completes Steps 3 + Final Summary
6. Previous turn (including breadcrumbs and clarifying Q&A) persists in chat history

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: integration adjustments for clarifying question UI"
```
