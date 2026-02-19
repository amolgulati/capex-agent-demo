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

_USE_ASCII = os.environ.get("CAPEX_ASCII", "").strip() == "1"

TOOL_ICONS_EMOJI = {
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

TOOL_ICONS_ASCII = {
    "load_wbs_master": "[data]",
    "calculate_accruals": "[calc]",
    "calculate_net_down": "[net]",
    "calculate_outlook": "[outlook]",
    "get_exceptions": "[!]",
    "get_well_detail": "[detail]",
    "generate_journal_entry": "[journal]",
    "get_close_summary": "[summary]",
    "generate_outlook_load_file": "[file]",
}

TOOL_ICONS = TOOL_ICONS_ASCII if _USE_ASCII else TOOL_ICONS_EMOJI


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
                fallback = "[>]" if _USE_ASCII else "🔧"
                icon = TOOL_ICONS.get(event.tool_name, fallback)
                print(f"  {icon} Calling {event.tool_name}...", flush=True)
            elif isinstance(event, ToolResultEvent):
                pass  # Handled by the tool call event
            elif isinstance(event, TextEvent):
                print(event.text, end="", flush=True)
            elif isinstance(event, DoneEvent):
                pass
            elif isinstance(event, ErrorEvent):
                err_icon = "[X]" if _USE_ASCII else "❌"
                print(f"\n{err_icon} Error: {event.message}")

        print("\n")


if __name__ == "__main__":
    main()
