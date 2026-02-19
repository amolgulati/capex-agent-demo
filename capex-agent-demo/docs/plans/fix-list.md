## Deep Dive Review: CapEx Close Agent Demo

### Status: 58 tests passing, Phases 1-2 done, Phases 3-5 scaffolded but not wired for real demo use yet

---

### CRITICAL — Will visibly break the demo

**1. No streaming in the orchestrator** (`orchestrator.py:143`)
The orchestrator uses `self.client.messages.create()` (synchronous, non-streaming). The PRD Section 8.3 explicitly calls out that the audience will see **5-10 seconds of dead air** while Claude generates a full response before anything appears on screen. For a projected demo in front of 100 people, this feels like the app froze. The fix is switching to `self.client.messages.stream()` and yielding `TextEvent` chunks as they arrive.

**2. Clarifying question UI doesn't exist** (`app.py`)
The PRD's "wow moment" is the agent pausing to ask how to handle a data issue, rendered as `st.radio()` with a "Continue" button. The current app has zero pause/resume logic — the agent just prints text, and the user has to type a reply. This is the #1 demo differentiator ("it asks for human judgment") and it's not implemented yet. The system prompt in `prompts.py:26` does instruct the agent to ask about WI% mismatches, but there's no UI to detect and render that as an interactive widget.

**3. Breadcrumbs don't persist across Streamlit reruns** (`app.py:221-224`)
Tool call breadcrumbs are rendered as HTML during the agent run but aren't stored in `st.session_state.messages`. When the user sends a follow-up message, Streamlit reruns the script and only the stored text messages are re-rendered — the breadcrumbs (showing which tools were called) vanish from previous turns. For the demo, the presenter loses the visual trail they need to narrate.

**4. "DEMO — Synthetic Data" banner is weak** (`app.py:183-184`)
PRD Story L2 requires a persistent, prominent "DEMO — Synthetic Data" banner. Currently:
- Sidebar: `"Monthly Close Demo — January 2026"` (says Demo but not Synthetic Data)
- Main: `"AI-powered capital expenditure close process — January 2026"` (no Demo/Synthetic mention)

When a Finance leader asks "is this real data?" (PRD rates this HIGH probability), the banner should be unmistakable.

---

### HIGH — Should fix before demo

**5. WBS-1005 gets a noisy double-exception**
The negative accrual well (WBS-1005) triggers both "Negative Accrual" (HIGH) and "Large Swing" (MEDIUM, 184%). The Large Swing is technically correct but misleading — the real issue is the negative accrual, and the swing is just a symptom. During the demo, this could confuse the audience ("why is it flagged twice?"). Fix: skip Large Swing check if the well already has a Negative Accrual exception.

**6. `get_exceptions` re-computes all 3 steps from scratch** (`tools.py:351-353`)
Every call to `get_exceptions()` calls `calculate_accruals()` + `calculate_net_down()` + `calculate_outlook()`, each of which re-reads the CSV. Same for `get_close_summary()` (calls all 3 per BU) and `generate_journal_entry()`. During a typical agent session, the same calculation runs 3-5 times. With 18 rows this is fast (~0.6s), but each redundant tool result eats API tokens:
- `load_wbs_master`: ~2,700 tokens
- `calculate_accruals`: ~2,200 tokens
- `generate_outlook_load_file`: ~4,100 tokens

Cumulative token cost across a full demo session could add up, increasing latency and cost.

**7. `generate_outlook_load_file` result is very large** (~4,100 tokens)
72 rows x 9 columns of JSON. If Claude calls this tool, it balloons the context. The PRD warns about token budget management. Consider truncating to a summary or only returning the first few rows with a total.

**8. Stale old plan documents** (`docs/plans/`)
Six plan documents from the original Phase 1/2 design reference an architecture that no longer exists (separate CSV files, session_state pattern, etc.). Not a demo issue per se, but could cause confusion for anyone looking at the docs.

---

### MEDIUM — Polish items

**9. `format_dollar` is dead code** (`utils/formatting.py`)
The `format_dollar` helper is never imported or used anywhere in the codebase. Only the old plan doc references it.

**10. PRD is significantly out of date**
The PRD describes:
- 5 separate CSV files → now 2 (wide table + drill schedule)
- `missing_itd_handling` parameter → now WI% mismatch
- Original 9 tools (load_wbs, load_itd, load_vow, etc.) → different 9 tools
- Exception types: Missing ITD, Missing VOW, Zero ITD → replaced with WI% Mismatch, Over Budget
- Session state pattern → direct CSV reads each time

The PRD session log should be updated, and the Build Progress Dashboard says "Phase 3: NOT STARTED" but orchestrator.py, prompts.py, cli.py, and app.py all exist.

**11. `max_tokens=4096` may be too low** (`orchestrator.py:145`)
If Claude needs to format a large results table with 18 wells across 4 cost categories, plus exception details, 4096 tokens might truncate the response. Consider bumping to 8192.

**12. No error recovery for missing API key in CLI** (`cli.py:38-41`)
The CLI prints an error and exits, which is fine. But the error mentions `.env.example` — should verify this file has correct content.

**13. Sidebar downloads run computations at load time** (`app.py:146-152`)
The `@st.cache_data` decorated functions `_generate_excel()` and `_generate_csv()` run the full calculation pipeline the first time the page loads. This adds a few hundred milliseconds to the initial page render. Not a big deal, but it means the Excel/CSV downloads are always available before the user even asks the agent to do anything — which slightly undermines the "watch the agent work" narrative.

---

### LOW — Cosmetic / nice-to-have

**14. CLI tool icons use emoji** (`cli.py:24-33`)
Minor, but some terminal configurations don't render emoji well. Could use ASCII fallbacks.

**15. No `@st.cache_data` on CSV reads in the tool functions** (`tools.py`, `data_loader.py`)
The `data_loader.py` functions don't use `@st.cache_data` (PRD Section 8.4 recommends this). In a Streamlit context, every agent turn re-reads the CSVs. For 18-row files this is negligible, but it's a minor optimization the PRD explicitly calls for.

**16. `drill_schedule.csv` has no `estimated_cost` column**
The PRD spec says it should. The refactored design uses `ops_budget` from wbs_master instead, which is fine, but the drill schedule is somewhat underutilized — it only provides phase dates for the outlook allocation.

---

### Summary — Recommended Fix Order

| Priority | Fix | Effort |
|----------|-----|--------|
| 1 | Add streaming to orchestrator | ~30 min |
| 2 | Add clarifying question detection + radio UI | ~1 hr |
| 3 | Store breadcrumbs in session state so they persist | ~30 min |
| 4 | Make "DEMO — Synthetic Data" banner prominent | ~5 min |
| 5 | Skip Large Swing on negative accrual wells | ~5 min |
| 6 | Increase max_tokens to 8192 | ~1 min |
| 7 | Update PRD session log / build dashboard | ~15 min |
