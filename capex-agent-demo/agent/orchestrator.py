"""Agent orchestrator — Claude API tool-use loop for the CapEx Close Agent."""

import json
from dataclasses import dataclass, field
from typing import Generator

import anthropic
import pandas as pd

from agent.prompts import SYSTEM_PROMPT
from agent.tool_definitions import TOOL_DEFINITIONS
from agent.tools import (
    calculate_accruals,
    calculate_net_down,
    calculate_outlook,
    generate_journal_entry,
    generate_outlook_load_file,
    get_close_summary,
    get_exceptions,
    get_well_detail,
)
from utils.data_loader import load_wbs_master, load_drill_schedule


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "load_wbs_master": lambda **kw: _df_to_dict(load_wbs_master(kw.get("business_unit", "all"))),
    "calculate_accruals": lambda **kw: calculate_accruals(kw.get("business_unit", "all")),
    "calculate_net_down": lambda **kw: calculate_net_down(kw.get("business_unit", "all")),
    "calculate_outlook": lambda **kw: calculate_outlook(kw.get("business_unit", "all")),
    "get_exceptions": lambda **kw: get_exceptions(
        kw.get("business_unit", "all"), kw.get("severity", "all")
    ),
    "get_well_detail": lambda **kw: get_well_detail(kw["wbs_element"]),
    "generate_journal_entry": lambda **kw: generate_journal_entry(kw.get("business_unit", "all")),
    "get_close_summary": lambda **kw: get_close_summary(kw.get("business_unit", "all")),
    "generate_outlook_load_file": lambda **kw: _outlook_to_dict(
        generate_outlook_load_file(kw.get("business_unit", "all"), kw.get("months_forward", 6))
    ),
}


def _df_to_dict(df: pd.DataFrame) -> dict:
    """Convert a DataFrame to a JSON-safe dict for tool results."""
    return {"rows": df.to_dict(orient="records"), "row_count": len(df)}


def _outlook_to_dict(result: dict) -> dict:
    """Convert outlook load file result (contains a DataFrame) to JSON-safe dict."""
    df = result["load_file"]
    return {
        "load_file": df.to_dict(orient="records"),
        "months": result["months"],
        "row_count": len(df),
    }


def dispatch_tool(name: str, input_args: dict) -> str:
    """Call a tool function and return the JSON result string."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**input_args)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Streaming event types
# ---------------------------------------------------------------------------

@dataclass
class TextEvent:
    """A chunk of assistant text."""
    text: str
    type: str = "text"


@dataclass
class ToolCallEvent:
    """The agent is calling a tool."""
    tool_name: str
    tool_input: dict = field(default_factory=dict)
    type: str = "tool_call"


@dataclass
class ToolResultEvent:
    """Result of a tool call (for UI breadcrumbs)."""
    tool_name: str
    result_preview: str = ""
    type: str = "tool_result"


@dataclass
class DoneEvent:
    """Agent loop is complete."""
    full_response: str = ""
    type: str = "done"


@dataclass
class ErrorEvent:
    """An error occurred."""
    message: str = ""
    type: str = "error"


@dataclass
class ClarifyEvent:
    """The agent is asking the user a clarifying question."""
    question: str
    options: list
    tool_use_id: str
    type: str = "clarify"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

MAX_TURNS = 15  # Safety limit on tool-use loops


class AgentOrchestrator:
    """Run the CapEx Close Agent via Claude API with tool-use loop."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def run(self, messages: list) -> Generator:
        """Run the agent loop, yielding events for streaming.

        Parameters
        ----------
        messages : list[dict]
            Conversation history in Claude API format
            (role="user"/"assistant", content=...).
        """
        for turn in range(MAX_TURNS):
            try:
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                ) as stream:
                    for text in stream.text_stream:
                        yield TextEvent(text=text)
                    response = stream.get_final_message()
            except anthropic.APIError as e:
                yield ErrorEvent(message=f"API error: {e}")
                return

            # Collect assistant text and tool calls from the final message
            assistant_text = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    assistant_text += block.text
                    # Text already streamed above via text_stream
                elif block.type == "tool_use":
                    tool_calls.append(block)
                    yield ToolCallEvent(
                        tool_name=block.name,
                        tool_input=block.input,
                    )

            # Append full assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # If no tool calls, we're done
            if not tool_calls:
                yield DoneEvent(full_response=assistant_text)
                return

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

        # Safety: exceeded max turns
        yield ErrorEvent(message="Exceeded maximum tool-use turns")
