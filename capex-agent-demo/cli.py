#!/usr/bin/env python3
"""CLI for testing the CapEx Close Agent interactively."""

import os
import sys
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from agent.orchestrator import (
    AgentOrchestrator,
    DoneEvent,
    ErrorEvent,
    TextEvent,
    ToolCallEvent,
    ToolResultEvent,
)

load_dotenv()

TOOL_ICONS = {
    "load_wbs_master": "📊",
    "calculate_accruals": "🧮",
    "calculate_net_down": "⚖️",
    "calculate_outlook": "🔮",
    "get_exceptions": "⚠️",
    "get_well_detail": "🔍",
    "generate_journal_entry": "📝",
    "get_close_summary": "📋",
    "generate_outlook_load_file": "📁",
}


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    model = os.environ.get("CAPEX_MODEL", "claude-sonnet-4-6")
    agent = AgentOrchestrator(api_key=api_key, model=model)
    messages = []

    print("=" * 60)
    print("  CapEx Close Agent — CLI")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        print()
        for event in agent.run(messages):
            if isinstance(event, ToolCallEvent):
                icon = TOOL_ICONS.get(event.tool_name, "🔧")
                print(f"  {icon} Calling {event.tool_name}...", flush=True)
            elif isinstance(event, ToolResultEvent):
                pass  # Handled by the tool call event
            elif isinstance(event, TextEvent):
                print(event.text, end="", flush=True)
            elif isinstance(event, DoneEvent):
                pass
            elif isinstance(event, ErrorEvent):
                print(f"\n❌ Error: {event.message}")

        print("\n")


if __name__ == "__main__":
    main()
