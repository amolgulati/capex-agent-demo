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
