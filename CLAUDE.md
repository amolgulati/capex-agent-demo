# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **CapEx Gross Accrual Agent Demo** — a Streamlit web app demonstrating an AI agent that calculates capital expenditure accruals using synthetic oil & gas data. Built for a Finance department town hall presentation (~100 non-technical audience). The agent visibly reasons through steps, calls tools, asks clarifying questions, and produces formatted results with exception reports.

**Current status:** Phase 1 (Data Foundation) is complete. Phase 2 (Core Agent Tools) is next. See `planning/prd.md` → "Build Progress Dashboard" for the latest status.

## Commands

```bash
# Run all tests (from repo root)
pytest capex-agent-demo/tests/

# Run a single test file
pytest capex-agent-demo/tests/test_data.py

# Run a single test class or method
pytest capex-agent-demo/tests/test_data.py::TestNegativeAccrual
pytest capex-agent-demo/tests/test_data.py::TestDataLoader::test_load_wbs_master_all

# Regenerate synthetic CSV data (deterministic, seed=42)
python capex-agent-demo/data/generate_synthetic_data.py

# Install dependencies
pip install -r capex-agent-demo/requirements.txt

# Run the Streamlit app (Phase 4+)
streamlit run capex-agent-demo/app.py
```

## Architecture

### Repository Layout

The repo has two layers: top-level planning/context documents and the `capex-agent-demo/` subdirectory containing all code.

- **Top-level docs**: `Project_Overview.md`, `Executive_Summary.md`, `Technical_Briefing.md`, `CapEx_Forecasting_Business_Plan.md` — business context (generalized, no real data)
- **`planning/prd.md`** — The PRD is the **single source of truth** for all implementation decisions. It contains the build progress dashboard, acceptance criteria, tool specifications, session log, and domain model. Always read the PRD before starting work.
- **`capex-agent-demo-spec.md`** — Original demo spec. The PRD supersedes it where they differ.
- **`capex-agent-demo/`** — All application code lives here

### Code Structure (capex-agent-demo/)

```
data/
  generate_synthetic_data.py  — Deterministic generator (seed=42) for 5 CSV files
  *.csv                       — 5 synthetic datasets (wbs_master, itd_extract, vow_estimates,
                                prior_period_accruals, drill_schedule)
utils/
  data_loader.py              — CSV loading functions used by agent tools
agent/
  (Phase 2+)                  — tools.py, tool_definitions.py, orchestrator.py, prompts.py
tests/
  test_data.py                — 64 tests covering all Phase 1 acceptance criteria
```

### Data Flow and Domain Model

The core calculation: **Gross Accrual = VOW - ITD** (per WBS element)

- **WBS Element** — unique project/well identifier (WBS-1001 through WBS-1050)
- **ITD** (Incurred-to-Date) — costs already invoiced in SAP
- **VOW** (Value of Work) — engineer's estimate of work completed (this org's term for WIP)
- **Net-Down** = Current Gross Accrual - Prior Period Gross Accrual (the journal entry)

Data relationships (all join on `wbs_element`):
```
wbs_master (50 rows) → itd_extract (47 rows, 3 WBS deliberately missing)
wbs_master (50 rows) → vow_estimates (48 rows, 2 WBS deliberately missing)
wbs_master (50 rows) → prior_period_accruals (48 rows, 2 new wells missing)
wbs_master (50 rows) → drill_schedule (60-80 rows, ~20 wells × 3-5 phases)
```

### Intentional Exception Records

The synthetic data has hardcoded exception triggers — do not "fix" these:

| Exception | WBS Elements | Mechanism |
|-----------|-------------|-----------|
| Missing ITD (HIGH) | WBS-1031, WBS-1038, WBS-1044 | Absent from itd_extract |
| Negative Accrual (HIGH) | WBS-1027 | ITD ($2,627K) > VOW ($2,500K) |
| Missing VOW (MEDIUM) | WBS-1015, WBS-1042 | Absent from vow_estimates |
| Large Swing (MEDIUM) | WBS-1009 | Current accrual ($1,072K) vs prior ($800K) = +34% |
| Zero ITD (LOW) | WBS-1047, WBS-1048, WBS-1049 | itd_amount = 0 |

### Phase 2 Tool Architecture (Upcoming)

9 tool functions in `agent/tools.py` that Claude calls via tool_use API. Tools use session state (dict) to share data between calls. Build order:
- **P0 (demo-critical):** load_wbs_master, load_itd, load_vow, calculate_accruals, get_exceptions, get_accrual_detail
- **P1/P2 (deferrable):** generate_net_down_entry, get_summary, generate_outlook

The `calculate_accruals` tool requires a `missing_itd_handling` parameter — the agent must always ask the user how to handle missing ITD before calling it (this is the demo's key interactive moment).

### Streamlit Specifics (Phase 4)

- Dual message history: `display_messages` (UI) and `api_messages` (Claude API with tool_use/tool_result blocks)
- Clarifying question resume uses "Flag & Rerun" pattern (set `run_agent = True`, call `st.rerun()`)
- `@st.cache_data` on CSV loaders to avoid re-reading on every Streamlit rerun
- Reference date is hardcoded to `2026-01` — do not use `datetime.now()`

## Key Conventions

- Data generator uses `random.Random(SEED=42)` for deterministic output — changing the seed breaks test assertions
- Row count caps are strict (wbs_master=50, itd_extract=47, vow_estimates=48, prior_period=48, drill_schedule=60-80) — exceeding them bloats Claude API token usage
- All data is synthetic — no real corporate data anywhere
- The PRD session log should be updated at the end of each coding session
