# Clarifying Question UI Design

**Fix-list item #2** — The PRD's "wow moment" is the agent pausing to ask how to handle a WI% mismatch, rendered as `st.radio()` with a "Continue" button.

## Detection Mechanism: Dedicated Tool

Add an `ask_user_question` tool that the agent calls with structured options. The agent explicitly signals it needs input, options are structured data, and the UI knows exactly when to pause.

## Flow

```
1. User: "Run the monthly close"
2. Agent runs Steps 1-2, calls ask_user_question tool
3. Orchestrator yields ClarifyEvent, returns (stops the loop)
4. App stores pending question in session_state
5. Streamlit reruns -> renders radio + Continue button
6. User picks option, clicks Continue
7. App appends tool_result to api_messages, sets run_agent=True, reruns
8. Agent resumes where it left off (Step 3 onward)
```

## Changes by File

### tool_definitions.py
Add `ask_user_question` tool schema with `question` (string) and `options` (array of strings) parameters.

### orchestrator.py
- New `ClarifyEvent` dataclass with question, options, tool_use_id fields
- When `ask_user_question` appears in tool_calls, yield `ClarifyEvent` and return
- The assistant message (with tool_use) is already appended to messages before returning

### prompts.py
Update system prompt to tell agent to use `ask_user_question` tool instead of writing questions as free text. Keep the WI% mismatch instruction but point it at the tool.

### app.py
- New session state key: `pending_question` (stores question, options, tool_use_id)
- In the event loop: detect `ClarifyEvent`, store it, stop processing
- After event loop: if `pending_question` exists, render `st.radio()` + `st.button("Continue")`
- On Continue: append tool_result to api_messages, clear pending_question, set run_agent=True, call st.rerun()
- On rerun with run_agent=True: run the agent (it picks up from the tool_result)

## Out of Scope
- Multi-question support (one question at a time is sufficient)
- Timeout/auto-answer (presenter will always click)
- Custom text input option (radio options cover demo scenarios)
- CLI changes (Streamlit-only UI)
