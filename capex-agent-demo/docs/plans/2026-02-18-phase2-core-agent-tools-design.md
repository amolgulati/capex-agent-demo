# Phase 2 Design: Core Agent Tools

**Date:** 2026-02-18
**Status:** Approved

## Architecture

All 9 tool functions live in `agent/tools.py`. Each takes a `session_state: dict` as the first parameter, plus tool-specific parameters matching the PRD signatures (Section 5). Tools return plain dicts (JSON-serializable for the Claude API).

The `utils/data_loader.py` functions from Phase 1 are the data access layer — tool functions call them, then shape the results into the dict format Claude expects.

## State Management

Session state is a plain `dict` passed to each tool function. The caller (test harness, CLI, or Streamlit orchestrator) creates and owns the dict.

```
session_state = {}
load_wbs_master → stores session_state['wbs_data'] (DataFrame)
load_itd        → stores session_state['itd_data'] (DataFrame)
load_vow        → stores session_state['vow_data'] (DataFrame)
calculate_accruals → reads wbs/itd/vow, loads prior_period internally
                   → stores session_state['accrual_results'] (dict)
                   → stores session_state['exceptions'] (list)
get_exceptions / get_accrual_detail / get_summary / generate_net_down_entry
                → read from session_state['accrual_results']
generate_outlook → reads drill_schedule independently
```

## Files to Create

| File | Purpose |
|------|---------|
| `agent/tools.py` | 9 tool functions |
| `agent/tool_definitions.py` | Claude API JSON tool schemas |
| `utils/formatting.py` | Dollar formatting helpers |
| `tests/test_tools.py` | Unit tests for all 14 acceptance criteria |

## Key Decisions

1. **Session state = plain dict** — testable, compatible with `st.session_state` in Phase 4
2. **`calculate_accruals` loads prior_period internally** — no separate load tool needed
3. **Exception detection lives in `calculate_accruals`** — all 5 types checked there
4. **`tool_definitions.py` omits `session_state`** — orchestrator injects it at dispatch time
5. **Build order: P0 first (6 core tools), then P1/P2 (3 extended tools)**

## Reference

Full specifications in `planning/prd.md` Section 5 (tool signatures) and Phase 2 acceptance criteria.
