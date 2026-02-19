# CapEx Gross Accrual Agent — Product Requirements Document

**Version:** 2.0
**Date:** February 18, 2026
**Author:** Amol Gulati
**Status:** Complete — All 5 phases done. v2.0: updated to reflect refactored data model (2 CSVs), current tool architecture, and completed polish pass.

---

## Build Progress Dashboard

<!-- UPDATE THIS SECTION at the start/end of each coding session -->

| Phase | Status | Key Files | Last Updated |
|-------|--------|-----------|--------------|
| **Phase 1 — Data Foundation** | DONE | `data/*.csv`, `utils/data_loader.py`, `tests/test_data.py` | 2026-02-18 |
| **Phase 2 — Core Agent Tools** | DONE | `agent/tools.py`, `agent/tool_definitions.py`, `tests/test_tools.py` | 2026-02-18 |
| **Phase 3 — Agent Orchestration** | DONE | `agent/orchestrator.py`, `agent/prompts.py`, `cli.py` | 2026-02-18 |
| **Phase 4 — Streamlit UI** | DONE | `app.py`, `.streamlit/config.toml`, `utils/excel_export.py` | 2026-02-18 |
| **Phase 5 — Polish & Demo-Ready** | DONE | Streaming, breadcrumbs, banner, polish fixes | 2026-02-18 |

**Status values:** `NOT STARTED` · `IN PROGRESS` · `BLOCKED — [reason]` · `DONE`

**Current focus:** Demo ready
**Next action:** None — all phases complete. Run demo with `streamlit run capex-agent-demo/app.py`
**Known blockers:** None

---

## Table of Contents

- [Build Progress Dashboard](#build-progress-dashboard) **← START HERE EACH SESSION**
1. [Product Overview](#1-product-overview)
2. [User Stories](#2-user-stories)
3. [Domain Model](#3-domain-model)
4. [Synthetic Data Requirements](#4-synthetic-data-requirements)
5. [Agent Logic & Tool Specifications](#5-agent-logic--tool-specifications)
6. [Agent Orchestration Flow](#6-agent-orchestration-flow)
7. [System Prompt](#7-system-prompt)
8. [UI/UX Specification](#8-uiux-specification)
9. [Demo Script](#9-demo-script)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Build Phases](#11-build-phases)
- [Session Log](#session-log) **← UPDATE AT END OF EACH SESSION**

---

## 1. Product Overview

### What This Is

A Streamlit web app that demonstrates an AI agent calculating CapEx gross accruals using synthetic data. The agent visibly reasons through each step, calls data-loading and calculation tools, asks clarifying questions when it encounters ambiguous data, and produces formatted results with exception reports — making "agentic AI" tangible for a Finance audience that has never seen one work.

### Who It's For

**Primary audience:** ~100 non-technical Finance professionals at a department town hall presentation. This includes BU Controllers, FP&A analysts, Accounting staff, and Finance leadership.

**Primary user during demo:** The presenter (Amol), who types prompts and narrates the agent's behavior live.

### Why It Matters

1. **Proof of concept.** This is Agent #1 on the Finance AI program roadmap. It proves that the agentic pattern (tool-calling, reasoning, exception handling, interactive decision-making) works for real Finance workflows.
2. **Immediate recognition.** BU Controllers currently spend 40-60 hours/month manually calculating gross accruals in Excel. Seeing an agent do it in 2 minutes, while showing its work, is immediately understood as valuable.
3. **Pattern establishment.** Once this agent is proven, the same architecture applies to depreciation checks, forecast variance analysis, journal entry review — any workflow with rules and data.
4. **Stakeholder confidence.** Leadership evaluating the Finance AI program needs a concrete demonstration, not slides. This gives them something to point to when asked "what does AI in Finance actually look like?"

### What This Is NOT

- Not a production system. It uses synthetic data and runs on Streamlit Cloud.
- Not a replacement for the full CapEx forecasting platform (which uses SAP Datasphere, AWS Lambda, SAC). This is a standalone demo app.
- Not connected to any real ERP, data warehouse, or corporate system.

### Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Frontend | Streamlit | Chat interface, `st.chat_message`, `st.status` for breadcrumbs |
| LLM | Claude API (Anthropic SDK) | `claude-sonnet-4-6` (default); override via `CAPEX_MODEL` env var |
| Data | Pandas + CSV files | Loaded at startup, queried by agent tools |
| Hosting | Streamlit Cloud (free tier) | Public URL, auto-deploys from GitHub |
| Export | openpyxl | Excel download of accrual schedules |

---

## 2. User Stories

### Priority Tiers

If build time runs short, use these tiers to decide what to cut:

| Tier | What's Included | Rationale |
|------|----------------|-----------|
| **P0 — Demo Critical** | Load data → clarifying question → calculate accruals → display results with metrics + exceptions. Stories: P1, P2, P3, A1, A2, A3, A4, L1, L2 | This is the core demo flow. Without it, there is no demo. |
| **P1 — High Value** | Follow-up queries, net-down journal entry, Excel download, sidebar data counters. Stories: P4, P5 | Makes the demo feel polished and interactive, but the core message lands without them. |
| **P2 — Nice to Have** | Outlook projection, get_summary grouping, sidebar status indicators, theme polish beyond dark mode. Stories: L3 | Impressive but not essential. Can be added post-demo or shown as "coming soon." |

### 2.1 The Presenter (Live Demo)

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| P1 | As the presenter, I can type a natural-language prompt and see the agent start working within 2 seconds, so there is no awkward dead air during the town hall. | First streaming token appears within 2s of pressing Enter. |
| P2 | As the presenter, I can see the agent's step-by-step reasoning as it works (streaming breadcrumbs), so I can narrate what's happening to the audience. | Each tool call is preceded by a visible "thinking" step explaining why the tool is being called. |
| P3 | As the presenter, I can respond to the agent's clarifying question by clicking a radio button, so the demo feels interactive without requiring typing. | Clarifying question renders as radio buttons with a "Continue" button. Selection resumes the agent loop. |
| P4 | As the presenter, I can ask follow-up questions ("Show me all negative accruals", "Which wells have the largest accruals?") and get contextual responses, so the demo shows the agent maintains conversation state. | Follow-up queries reference previously loaded data and calculations without re-running the full flow. |
| P5 | As the presenter, I can reset the demo with one click to start fresh if something goes wrong. | Sidebar "Reset Demo" button clears all chat history and cached state. |

### 2.2 The Audience (Finance Professionals)

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| A1 | As a BU Controller, I can see that the agent follows the same VOW - ITD calculation I do manually, so I trust it understands my workflow. | The agent explicitly states "Gross Accrual = VOW - ITD" and shows the math for at least one example WBS element. |
| A2 | As an FP&A analyst, I can see that the agent catches data exceptions (missing ITD, negative accruals, large swings) and flags them by severity, so I know it handles edge cases I worry about. | Exception report displays all 5 exception types with correct severity labels. |
| A3 | As an Accounting team member, I can see a formatted summary with total accrual amount, WBS count, and exception count, so the output looks like what I'd produce in Excel. | Summary displays metric cards with Total Gross Accrual, WBS Element count, and Exception count. |
| A4 | As a Finance professional, I can see every number traced back to source data (VOW file, ITD extract), so the agent isn't a "black box." | The agent's thinking breadcrumbs reference specific data sources and record counts. |

### 2.3 Leadership (Evaluating the Program)

| ID | Story | Acceptance Criteria |
|----|-------|-------------------|
| L1 | As a Finance leader, I can see that this demo runs end-to-end in under 3 minutes, so I believe it could meaningfully reduce manual effort. | Full demo flow (prompt → clarifying question → results) completes within 3 minutes. |
| L2 | As a Finance leader, I can see the "DEMO — Synthetic Data" banner on every screen, so I know this isn't making claims about real data. | Persistent banner/subtitle visible at all times. |
| L3 | As a program evaluator, I can understand from the demo that the same pattern applies to other Finance workflows, so I see this as a platform investment, not a one-off. | Presenter's closing line references future agents (depreciation, forecast variance, journal entry review). |

---

## 3. Domain Model

This section contains everything a developer with zero Finance knowledge needs to understand every calculation, data relationship, and exception rule in the app.

### 3.1 Core Concepts

**WBS Element (Work Breakdown Structure):** The project/well identifier that ties everything together. In oil & gas, each well or capital project gets a unique WBS number in SAP (e.g., "WBS-1001"). Every financial transaction, estimate, and forecast is tracked against a WBS.

**ITD (Incurred-to-Date):** What SAP says has been invoiced and recorded. This is the "actuals" — real money that has already been posted to the general ledger. Comes from SAP ERP extracts.

**VOW (Value of Work):** What the engineers say has been done. Also known as WIP (Work-in-Progress) in standard accounting terminology, but this organization uses VOW. This is an estimate submitted monthly by BU engineers as Excel files. VOW is typically higher than ITD because work gets done before invoices arrive.

**Gross Accrual:** The gap between work done and costs recorded. This is the amount Finance needs to book to correctly state the company's liabilities.

**Net-Down Journal Entry:** The incremental change in accruals from one period to the next. This is the actual journal entry that gets posted to the general ledger.

**Outlook:** A forward-looking projection of future accruals based on the drill/frac schedule and cost templates.

### 3.2 The Core Calculation

```
Gross Accrual = VOW - ITD
```

**For each WBS Element, for each Cost Category, for each Fiscal Period:**

1. Look up the **VOW amount** (engineer's estimate of total work completed to date)
2. Look up the **ITD amount** (costs already invoiced and posted in SAP)
3. Subtract: `Gross Accrual = VOW - ITD`
4. Run exception checks (see Section 3.5)

**Worked Example:**
- Engineers say $5M of work is done on Well ABC → VOW = $5,000,000
- SAP shows $3.2M has been invoiced → ITD = $3,200,000
- Gross Accrual = $5,000,000 - $3,200,000 = **$1,800,000**
- This $1.8M needs to be booked as an accrual liability

### 3.3 Net-Down Journal Entry

After calculating gross accruals for the current period, Finance creates a net-down entry:

```
Net-Down = Current Period Gross Accrual - Prior Period Gross Accrual
```

**Worked Example:**
- Last month (Dec 2025) gross accrual for Well ABC = $1,500,000
- This month (Jan 2026) gross accrual for Well ABC = $1,800,000
- Net-Down = $1,800,000 - $1,500,000 = **$300,000** (debit CapEx, credit accrual liability)

The net-down is the actual dollar amount that gets journaled. It represents the incremental change — if accruals went up, you book more; if they went down (e.g., invoices caught up), you reverse some.

**Aggregated Net-Down:** In practice, the journal entry is the sum of all individual WBS net-downs:
```
Total Net-Down = SUM(Current Gross Accrual[all WBS]) - SUM(Prior Gross Accrual[all WBS])
```

### 3.4 Outlook Projection

The outlook projects future accruals based on drilling/completion schedules and cost templates. For this demo, the outlook is simplified:

**For each well in the drill schedule:**
1. Look up the planned phases and dates (Spud, TD, Frac Start, Frac End, First Production)
2. Look up the estimated cost per phase from cost templates
3. Allocate costs to future months using **Linear by Day** allocation:

```
Daily Rate = Total Phase Cost / Total Days in Phase
Monthly Allocation = Daily Rate x Days of Phase Activity in that Month
```

**Phase-Specific Allocation Rules:**

| Phase | Allocation Method | Formula |
|-------|-------------------|---------|
| **Drilling** | Linear by Day | Cost / (Drill End - Spud Date + 1) x days per month |
| **Completions** | Linear by Day | Cost / (Frac End - Frac Start + 1) x days per month |
| **Flowback** | Linear by Day | Cost / (Flowback End - Flowback Start + 1) x days per month |
| **Hookup** | Lump Sum | 100% allocated to hookup month |

**In-Progress Phase Handling:**
When a phase has started but is not complete:
```
Remaining Outlook = Total Phase Cost - ITD for that phase
Allocation = Remaining Outlook / Remaining Days x days per month
```

**Overrun Handling:**
If ITD >= Template Cost for a phase:
- Set Outlook = $0 for that phase
- Flag as `OVERRUN_REVIEW`
- Do NOT auto-calculate — requires Finance manual adjustment

**Worked Example — Well WBS-2025-001 (Permian, Horizontal):**

| Phase | Start | End | Days | Template Cost | Daily Rate |
|-------|-------|-----|------|---------------|-----------|
| Drilling | 2025-02-10 | 2025-03-15 | 33 | $2,400,000 | $72,727/day |
| Completions | 2025-03-20 | 2025-04-10 | 21 | $3,200,000 | $152,381/day |
| Flowback | 2025-04-11 | 2025-04-25 | 14 | $150,000 | $10,714/day |
| Hookup | 2025-05-01 | 2025-05-01 | 1 | $250,000 | Lump sum |

Monthly allocation:

| Month | Drilling | Completions | Flowback | Hookup | Total |
|-------|----------|-------------|----------|--------|-------|
| Feb 2025 | $1,454,545 | - | - | - | $1,454,545 |
| Mar 2025 | $945,455 | $1,828,571 | - | - | $2,774,026 |
| Apr 2025 | - | $1,371,429 | $150,000 | - | $1,521,429 |
| May 2025 | - | - | - | $250,000 | $250,000 |
| **Total** | **$2,400,000** | **$3,200,000** | **$150,000** | **$250,000** | **$6,000,000** |

### 3.5 Exception Types

> **v2.0 Note:** The data model was refactored from 5 CSV files to 2. The wide `wbs_master.csv` now contains ITD, VOW, prior accrual, and WI% columns per cost category. Exception types were updated accordingly — "Missing ITD", "Missing VOW", and "Zero ITD" are replaced by "WI% Mismatch" and "Over Budget".

The agent detects and flags 4 categories of exceptions. These are intentionally baked into the synthetic data.

| # | Exception | Condition | Severity | What It Means | Recommended Action |
|---|-----------|-----------|----------|---------------|-------------------|
| 1 | **Negative Accrual** | Total gross accrual < 0 (ITD > VOW across all cost categories) | HIGH | More has been invoiced than engineers say is done — possible overbilling or VOW underestimate | Review with BU engineer; verify VOW estimate accuracy |
| 2 | **Large Swing** | Current accrual differs from prior period by more than 25%. **Guard:** Skip if prior accrual is 0 or if well already has Negative Accrual. | MEDIUM | Big change that needs explanation — could be legitimate (project phase change) or an error | Review with BU Controller; document explanation |
| 3 | **WI% Mismatch** | Working interest % differs between operator and partner records by more than 2pp | MEDIUM | Disagreement on ownership share — affects accrual allocation | Reconcile with JIB partner; confirm WI% before close |
| 4 | **Over Budget** | Projected total cost (ITD + remaining outlook) exceeds AFE budget by more than 10% | MEDIUM | Well is trending over authorized spend — may need AFE amendment | Flag to BU Controller; assess need for supplemental AFE |

### 3.6 Data Relationships

```
wbs_master.csv (1 row per well, wide table) ────── columns contain ITD, VOW, prior accrual per cost category
wbs_master (1) ────── (0..N) drill_schedule       [join on wbs_element]
```

- `wbs_master.csv` is the single authoritative data file containing all financial data per well (18 wells, 4 cost categories: drill, comp, fb, hu).
- `drill_schedule.csv` provides phase dates for outlook allocation (18 wells x 5 phases = 90 rows).
- Exception triggers are built into the wide table columns (e.g., negative accrual wells have ITD > VOW).

### 3.7 Formulas Reference (Complete)

| Formula | Definition | When Used |
|---------|-----------|-----------|
| `Gross Accrual` | `VOW - ITD` | Per WBS, per period |
| `Net-Down` | `Current Gross Accrual - Prior Gross Accrual` | Per WBS, comparing current to prior period |
| `Total Net-Down` | `SUM(all current gross accruals) - SUM(all prior gross accruals)` | Aggregated journal entry |
| `Outlook Daily Rate` | `Phase Cost / Phase Days` | Per phase (Drilling, Completions, Flowback) |
| `Monthly Allocation` | `Daily Rate x Days in Month` | Spreading cost across calendar months |
| `Remaining Outlook` | `Phase Cost - ITD for that phase` | In-progress phases only |
| `Large Swing %` | `(Current Accrual - Prior Accrual) / Prior Accrual`. Skip if prior is null or $0 (new WBS). | Exception detection; trigger at >25% |
| `Total Forecast` | `ITD + Accrual + Outlook` | Complete project cost picture |

---

## 4. Synthetic Data Requirements

All data is 100% fictional. No real corporate data. Well names, WBS numbers, dollar amounts, and dates are all synthetic.

> **v2.0 Note:** The data model was refactored from 5 separate CSV files to 2. The original `itd_extract.csv`, `vow_estimates.csv`, and `prior_period_accruals.csv` were consolidated into a single wide-format `wbs_master.csv` with per-category columns for ITD, VOW, prior accruals, and WI%. The `drill_schedule.csv` remains separate. Sections 4.2-4.4 below describe the **original** design for historical reference; the current implementation uses the consolidated model described in Section 4.1.

**Token Budget Constraint:** Row counts are hard caps. Tool results consume context window tokens. The `_outlook_to_dict()` function in the orchestrator compresses the 72-row outlook load file to ~600 tokens. Calculation functions use `@lru_cache` to avoid redundant recomputation.

| File | Rows | Description |
|------|------|-------------|
| `wbs_master.csv` | 18 rows | Wide table: 1 row per well with ITD/VOW/prior accrual/WI% columns per cost category (drill, comp, fb, hu) |
| `drill_schedule.csv` | 90 rows | 18 wells x 5 phases (spud, td, frac_start, frac_end, first_production) |

### 4.1 File: `wbs_master.csv` (~50 rows)

The project registry. Every well/project in scope.

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `wbs_element` | String | Primary key. Unique project ID. | "WBS-1001", "WBS-1002", ..., "WBS-1050" |
| `well_name` | String | Descriptive well name. Use realistic oil & gas naming. | "Permian Eagle 14H", "Wolfcamp A 22-1H", "Delaware Basin 7-2H" |
| `project_type` | String | Capital project category. | "Drilling", "Completion", "Facilities", "Workover" |
| `business_unit` | String | Operating business unit. | "Permian Basin", "DJ Basin", "Powder River" |
| `afe_number` | String | Authorization for Expenditure ID. | "AFE-2026-0014", "AFE-2025-0087" |
| `status` | String | Project lifecycle status. | "Active" (most), "Complete" (a few), "Suspended" (1-2) |
| `budget_amount` | Float | AFE-approved budget in USD. | $2,000,000 - $15,000,000 range |
| `start_date` | Date (YYYY-MM-DD) | Project start date. | Various dates in 2025-2026 |

**Distribution rules:**
- ~35 rows: `business_unit` = "Permian Basin" (primary demo target)
- ~10 rows: `business_unit` = "DJ Basin"
- ~5 rows: `business_unit` = "Powder River"
- ~40 rows: `status` = "Active"
- ~7 rows: `status` = "Complete"
- ~3 rows: `status` = "Suspended"
- `project_type` mix: ~60% Drilling, ~25% Completion, ~10% Facilities, ~5% Workover

### 4.2 File: `itd_extract.csv` (~44 rows)

SAP extract of costs already invoiced. Intentionally missing records for 6 WBS elements (3 for "Missing ITD" exceptions, 3 for "Zero ITD" where `itd_amount` = 0).

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `wbs_element` | String | FK to wbs_master. | Matches 44 of 50 from wbs_master |
| `itd_amount` | Float | Total costs invoiced to date in USD. | $0 - $12,000,000 |
| `last_posting_date` | Date | Most recent invoice posting date. | Dates in Dec 2025 - Jan 2026 |
| `cost_category` | String | Cost classification. | "Material", "Service", "Labor", "Equipment" |
| `vendor_count` | Int | Number of distinct vendors with invoices. | 1 - 15 |

**Exception-triggering records:**
- **3 WBS elements from wbs_master are completely absent** from this file → triggers "Missing ITD" (HIGH)
- **3 WBS elements have `itd_amount` = 0** → triggers "Zero ITD" (LOW)
- **1 WBS element has ITD > its corresponding VOW** → triggers "Negative Accrual" (HIGH)

### 4.3 File: `vow_estimates.csv` (~45 rows)

Engineer work-in-progress estimates. Intentionally missing records for 5 WBS elements (2 for "Missing VOW" exceptions, 3 overlap with ITD gaps).

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `wbs_element` | String | FK to wbs_master. | Matches 45 of 50 from wbs_master |
| `vow_amount` | Float | Engineer's estimate of total work completed to date. | Generally higher than ITD (most accruals positive) |
| `submission_date` | Date | When the engineer submitted this estimate. | "2026-01-28" or similar recent date |
| `engineer_name` | String | Who submitted (synthetic names). | "Sarah Chen", "Mike Torres", "Lisa Park" |
| `phase` | String | Current project phase. | "Drilling", "Completion", "Flowback", "Equip" |
| `pct_complete` | Float | Percent complete (0-100). | 15.0, 45.5, 78.0, 100.0 |

**Exception-triggering records:**
- **2 WBS elements from wbs_master are absent** from this file (different from ITD gaps) → triggers "Missing VOW" (MEDIUM)
- **1 WBS element has `vow_amount` < its corresponding `itd_amount`** → triggers "Negative Accrual" (HIGH). Specifically: VOW = $2,500,000, ITD = $2,627,000 → Accrual = -$127,000
- **1 WBS element has accrual >25% different from prior period** → triggers "Large Swing" (MEDIUM). Specifically: prior accrual ~$800K, current accrual ~$1,072,000 → +34% change

### 4.4 File: `prior_period_accruals.csv` (~48 rows)

Last month's calculated accruals. Used for large-swing detection and net-down calculation.

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `wbs_element` | String | FK to wbs_master. | Most WBS elements represented |
| `prior_gross_accrual` | Float | Gross accrual from December 2025. | $0 - $3,000,000 |
| `period` | String | The prior period identifier. | "2025-12" |

**Design rules:**
- Most records: prior accrual is within 10-15% of current accrual (normal variance)
- 1 record: prior accrual is significantly different to trigger the "Large Swing" exception (current is +34% vs prior)
- New WBS elements (started in Jan 2026) may not have a prior period record

### 4.5 File: `drill_schedule.csv` (~20 rows)

Forward-looking drill/frac schedule for the outlook projection.

| Column | Type | Description | Example Values |
|--------|------|-------------|---------------|
| `wbs_element` | String | FK to wbs_master (subset of active drilling/completion wells). | Matches ~20 active WBS elements |
| `planned_phase` | String | Operational milestone. | "Spud", "TD", "Frac Start", "Frac End", "First Production" |
| `planned_date` | Date | When this milestone is expected. | Q1-Q2 2026 dates |
| `estimated_cost` | Float | Cost estimate for this phase. | $500,000 - $5,000,000 depending on phase |

**Design rules:**
- Each WBS element in the schedule has 3-5 rows (one per milestone/phase)
- Dates should be sequential (Spud → TD → Frac Start → Frac End → First Production)
- Costs should be realistic: Drilling $2-5M, Completions $3-5M, Flowback $100-200K, Hookup $200-400K

### 4.6 Exception Summary Matrix

> **v2.0 Note:** Exception types were updated for the refactored data model. The current exceptions are detected by `calculate_accruals()`, `calculate_net_down()`, and `calculate_outlook()` in `agent/tools.py`.

| Exception Type | Severity | Mechanism | Detection Step |
|---------------|----------|-----------|---------------|
| Negative Accrual | HIGH | Total gross accrual (sum of VOW - ITD across all categories) < 0 | `calculate_accruals` |
| Large Swing | MEDIUM | Current accrual >25% different from prior. Guard: skip if prior=0 or if Negative Accrual already flagged. | `calculate_accruals` |
| WI% Mismatch | MEDIUM | Working interest differs between operator and partner by >2pp | `calculate_net_down` |
| Over Budget | MEDIUM | Projected cost (ITD + outlook) exceeds `ops_budget` by >10% | `calculate_outlook` |

**Note:** The Large Swing check is guarded to avoid double-flagging wells that already have a Negative Accrual exception.

---

## 5. Agent Logic & Tool Specifications

> **v2.0 Note:** The tool architecture was refactored. The original `load_itd`, `load_vow` tools and `missing_itd_handling` parameter were replaced. The current architecture has 10 tools (9 data + `ask_user_question`): `load_wbs_master`, `calculate_accruals`, `calculate_net_down`, `calculate_outlook`, `get_exceptions`, `get_well_detail`, `generate_journal_entry`, `get_close_summary`, `generate_outlook_load_file`. The clarifying question now uses WI% mismatch (via `ask_user_question` tool) instead of `missing_itd_handling`. Sections 5.2-5.9 below describe the **original** tool designs for historical reference; see `agent/tool_definitions.py` and `agent/tools.py` for the current implementations.

### 5.1 Tool: `load_wbs_master`

**Purpose:** Load the WBS Master List, optionally filtered by business unit.

**Function Signature:**
```python
def load_wbs_master(business_unit: str) -> dict:
    """
    Load WBS Master List for a given business unit.

    Args:
        business_unit: Business unit to filter by.
                       Values: "Permian Basin", "DJ Basin", "Powder River", or "all"

    Returns:
        dict with keys:
            - "wbs_elements": list of dicts, each with keys:
                wbs_element, well_name, project_type, business_unit,
                afe_number, status, budget_amount, start_date
            - "count": int, total records returned
            - "active_count": int, records with status="Active"
            - "business_units": list of unique BU names in result
    """
```

**Implementation:**
1. Read `data/wbs_master.csv` into a DataFrame
2. If `business_unit` != "all", filter by `business_unit` column
3. Return structured dict with records and summary counts

**Edge Cases:**
- If `business_unit` doesn't match any records, return empty list with `count: 0`
- The tool stores the loaded WBS list in session state for use by subsequent tools

### 5.2 Tool: `load_itd`

**Purpose:** Load Incurred-to-Date costs from the SAP extract for specified WBS elements.

**Function Signature:**
```python
def load_itd(wbs_elements: list[str]) -> dict:
    """
    Load ITD costs from SAP extract for the specified WBS elements.

    Args:
        wbs_elements: List of WBS element IDs to retrieve ITD for

    Returns:
        dict with keys:
            - "itd_records": list of dicts, each with keys:
                wbs_element, itd_amount, last_posting_date, cost_category, vendor_count
            - "matched_count": int, WBS elements found in ITD data
            - "total_requested": int, len(wbs_elements)
            - "unmatched": list of WBS element IDs with no ITD record
            - "zero_itd": list of WBS element IDs with itd_amount = 0
    """
```

**Implementation:**
1. Read `data/itd_extract.csv` into a DataFrame
2. Filter to only rows where `wbs_element` is in the provided list
3. Identify unmatched WBS elements (requested but not in ITD file)
4. Identify zero-ITD records
5. Return structured dict with records, match counts, and gap lists

**Edge Cases:**
- WBS elements not found in ITD file are returned in the `unmatched` list (these become "Missing ITD" exceptions)
- WBS elements with `itd_amount == 0` are returned in the `zero_itd` list

### 5.3 Tool: `load_vow`

**Purpose:** Load Work-in-Progress / Value of Work estimates from engineers for specified WBS elements.

**Function Signature:**
```python
def load_vow(wbs_elements: list[str]) -> dict:
    """
    Load VOW estimates for the specified WBS elements.

    Args:
        wbs_elements: List of WBS element IDs to retrieve VOW for

    Returns:
        dict with keys:
            - "vow_records": list of dicts, each with keys:
                wbs_element, vow_amount, submission_date, engineer_name, phase, pct_complete
            - "matched_count": int, WBS elements found in VOW data
            - "total_requested": int, len(wbs_elements)
            - "unmatched": list of WBS element IDs with no VOW submission
    """
```

**Implementation:**
1. Read `data/vow_estimates.csv` into a DataFrame
2. Filter to only rows where `wbs_element` is in the provided list
3. Identify unmatched WBS elements (requested but not in VOW file)
4. Return structured dict with records, match counts, and gap list

**Edge Cases:**
- WBS elements not found in VOW file are returned in the `unmatched` list (these become "Missing VOW" exceptions)

### 5.4 Tool: `calculate_accruals`

**Purpose:** Calculate gross accruals (VOW - ITD) for each WBS element. This is the core calculation.

**Function Signature:**
```python
def calculate_accruals(missing_itd_handling: str) -> dict:
    """
    Calculate gross accruals for all loaded WBS elements.

    Args:
        missing_itd_handling: How to handle WBS elements with VOW but no ITD.
            Options:
            - "use_vow_as_accrual": Treat missing ITD as $0, so accrual = full VOW amount
            - "exclude_and_flag": Exclude from calculation, flag for manual review
            - "use_prior_period": Use prior period's ITD as estimate

    Returns:
        dict with keys:
            - "accruals": list of dicts, each with keys:
                wbs_element, well_name, vow_amount, itd_amount, gross_accrual,
                prior_accrual, net_change, pct_change, exception_type, exception_severity
            - "summary": dict with keys:
                total_gross_accrual, total_wbs_count, calculated_count,
                exception_count, prior_period_total, net_change_total, pct_change_total
            - "exceptions": list of dicts (exception details)
    """
```

**Guardrail:** This tool requires `missing_itd_handling` to be explicitly provided. If the agent calls this tool without first asking the user how to handle missing ITD (see System Prompt, "Clarifying Question Rules"), the tool should still work — but the system prompt mandates that the agent always asks first. This is a belt-and-suspenders approach: the system prompt forces the question, and the tool parameter makes it impossible to skip the decision.

**Implementation:**
1. Requires `load_wbs_master`, `load_itd`, and `load_vow` to have been called first (data in session state)
2. Outer join VOW and ITD on `wbs_element`
3. For each WBS:
   a. If both VOW and ITD exist: `gross_accrual = vow_amount - itd_amount`
   b. If VOW exists but ITD missing: apply `missing_itd_handling` parameter
   c. If ITD exists but VOW missing: flag as "Missing VOW" exception
4. Load `prior_period_accruals.csv` and join on `wbs_element`
5. Calculate net change and percentage change vs prior period
6. Run exception detection:
   - `gross_accrual < 0` → "Negative Accrual" (HIGH)
   - WBS in VOW but not in ITD → "Missing ITD" (HIGH)
   - WBS in master but not in VOW → "Missing VOW" (MEDIUM)
   - `abs(pct_change) > 0.25` → "Large Swing" (MEDIUM). **Guard:** skip if prior accrual is null or 0 (new WBS — not a swing).
   - `itd_amount == 0` and VOW exists → "Zero ITD" (LOW)
7. Aggregate summary totals
8. Store results in session state for follow-up queries

**Edge Cases:**
- If `missing_itd_handling` = "use_vow_as_accrual": set ITD to $0, accrual = full VOW amount
- If `missing_itd_handling` = "exclude_and_flag": exclude from total, add to exceptions
- If `missing_itd_handling` = "use_prior_period": look up prior period ITD; if not available, fall back to exclude
- A WBS can have multiple exception flags simultaneously (e.g., "Zero ITD" + "Large Swing")

### 5.5 Tool: `get_exceptions`

**Purpose:** Retrieve the exception report filtered by severity.

**Function Signature:**
```python
def get_exceptions(severity: str) -> dict:
    """
    Retrieve exception report from the most recent accrual calculation.

    Args:
        severity: Filter level. "all", "high", "medium", or "low"

    Returns:
        dict with keys:
            - "exceptions": list of dicts, each with keys:
                wbs_element, well_name, exception_type, severity,
                detail, recommended_action, vow_amount, itd_amount, accrual_amount
            - "count": int
            - "by_type": dict mapping exception_type to count
            - "by_severity": dict mapping severity to count
    """
```

**Implementation:**
1. Read exceptions from session state (populated by `calculate_accruals`)
2. Filter by severity if not "all"
3. Return structured exception list with counts

### 5.6 Tool: `get_accrual_detail`

**Purpose:** Get detailed breakdown for a single WBS element.

**Function Signature:**
```python
def get_accrual_detail(wbs_element: str) -> dict:
    """
    Get detailed accrual information for a specific WBS element.

    Args:
        wbs_element: The WBS element ID to look up

    Returns:
        dict with keys:
            - "wbs_element": str
            - "well_name": str
            - "project_type": str
            - "business_unit": str
            - "status": str
            - "budget_amount": float
            - "vow_amount": float (or None if missing)
            - "itd_amount": float (or None if missing)
            - "gross_accrual": float
            - "prior_accrual": float (or None)
            - "net_change": float
            - "pct_change": float
            - "exceptions": list of exception dicts for this WBS
            - "phase": str (from VOW)
            - "pct_complete": float (from VOW)
            - "engineer_name": str (from VOW)
            - "last_posting_date": str (from ITD)
    """
```

**Implementation:**
1. Look up the WBS element across all loaded datasets
2. Merge all available information into a single detailed view

**Edge Cases:**
- If WBS element not found, return error dict with `"error": "WBS element not found"`

### 5.7 Tool: `generate_net_down_entry`

**Purpose:** Generate the net-down journal entry comparing current gross accruals to prior period.

**Function Signature:**
```python
def generate_net_down_entry() -> dict:
    """
    Generate net-down journal entry.

    Returns:
        dict with keys:
            - "journal_entry": dict with keys:
                period, description, debit_account, credit_account,
                total_current_accrual, total_prior_accrual, net_down_amount
            - "detail": list of dicts per WBS, each with:
                wbs_element, well_name, current_accrual, prior_accrual, net_change
            - "summary_text": str (human-readable summary)
    """
```

**Implementation:**
1. Requires `calculate_accruals` to have been called first
2. For each WBS: `net_change = current_gross_accrual - prior_gross_accrual`
3. Sum all net changes = total net-down
4. Format as journal entry with GL accounts:
   - Debit: CapEx WIP Account (e.g., "1410-000")
   - Credit: Accrued Liabilities (e.g., "2110-000")
5. If net-down is negative (accruals decreased), reverse the debit/credit

### 5.8 Tool: `generate_outlook`

**Purpose:** Project future accruals based on the drill/frac schedule.

**Function Signature:**
```python
def generate_outlook(months_forward: int) -> dict:
    """
    Project future accruals based on drill/frac schedule and cost templates.

    Args:
        months_forward: Number of months to project (1-6)

    Returns:
        dict with keys:
            - "outlook": list of dicts per future month, each with:
                month, expected_accrual, well_count, new_wells_starting,
                phases_completing
            - "total_outlook": float (sum of all future months)
            - "wells_in_schedule": int
            - "schedule_detail": list of dicts per well, each with:
                wbs_element, well_name, planned_phase, planned_date, estimated_cost
    """
```

**Implementation:**
1. Read `data/drill_schedule.csv`
2. **Reference date is hardcoded to `2026-01` (January 2026).** Do not use `datetime.now()`. The synthetic data is built around this period; using the current date would produce incorrect projections if the demo is run in a different month.
3. For each future month in the projection window:
   a. Identify wells with active phases in that month
   b. Apply Linear by Day allocation for non-hookup phases
   c. Apply Lump Sum for hookup phases
   d. Sum expected costs = expected accrual for that month
4. Return monthly projection with well-level detail

### 5.9 Tool: `get_summary`

**Purpose:** Aggregate accruals by a grouping dimension.

**Function Signature:**
```python
def get_summary(group_by: str) -> dict:
    """
    Get aggregated accrual summary grouped by a dimension.

    Args:
        group_by: Dimension to group by.
            Options: "project_type", "business_unit", "phase"

    Returns:
        dict with keys:
            - "summary": list of dicts, each with:
                group_value, total_accrual, wbs_count, avg_accrual,
                exception_count, pct_of_total
            - "grand_total": float
    """
```

**Implementation:**
1. Requires `calculate_accruals` to have been called first
2. Group accrual results by the specified dimension
3. Calculate subtotals, averages, counts, and percentage of grand total

---

## 6. Agent Orchestration Flow

### 6.1 High-Level Flow

```
User types prompt
    │
    ▼
System prompt + tools sent to Claude API
    │
    ▼
Claude responds with either:
    ├── Text response (answer/reasoning) → render in chat
    ├── Tool call → execute tool, return result to Claude, loop
    └── Clarifying question → render in UI, wait for user input, loop
    │
    ▼
Loop continues until Claude returns a final text response (no more tool calls)
    │
    ▼
Final response rendered with formatted output
```

> **v2.0 Note:** The demo flow was simplified. The agent now calls `calculate_accruals` directly (which reads from the wide `wbs_master.csv` internally) instead of separate `load_itd`/`load_vow` steps. The clarifying question is about WI% mismatch handling, not missing ITD. Steps 3-6 below describe the **original** design; see `agent/prompts.py` for the current flow.

### 6.2 Detailed Step-by-Step (Primary Demo Flow)

**Step 1: User Input**
User types: "Calculate the CapEx gross accrual for Permian Basin, January 2026"

**Step 2: Claude Decides to Call `load_wbs_master`**
Claude's reasoning (shown as breadcrumb):
> "I need to calculate gross accruals. This requires three data sources. Let me start by loading the WBS Master List."

Tool call: `load_wbs_master(business_unit="Permian Basin")`
Result: 47 active WBS elements found

**Step 3: Claude Decides to Call `load_itd`**
Claude's reasoning (shown as breadcrumb):
> "Now I need ITD costs from SAP for these WBS elements."

Tool call: `load_itd(wbs_elements=[...all 47 WBS IDs...])`
Result: 44 of 47 matched, 3 unmatched

**Step 4: Claude Decides to Call `load_vow`**
Claude's reasoning (shown as breadcrumb):
> "Next I need VOW estimates from engineers."

Tool call: `load_vow(wbs_elements=[...all 47 WBS IDs...])`
Result: 42 of 47 matched, 5 unmatched (but 3 overlap with ITD gaps)

**Step 5: Claude Asks a Clarifying Question**
Claude detects that 3 WBS elements have VOW but no ITD. Rather than assuming, it asks:

> "I found 3 WBS elements with VOW estimates but no ITD costs in SAP. How should I handle these?"
> - Use VOW as full accrual (assume zero ITD)
> - Exclude from calculation and flag for review
> - Use last month's ITD as estimate

This renders as radio buttons in the UI. User selects an option and clicks "Continue."

**Step 6: Claude Calls `calculate_accruals`**
Tool call: `calculate_accruals(missing_itd_handling="use_vow_as_accrual")` (or whichever option was selected)
Result: Full accrual calculation with exceptions

**Step 7: Claude Calls `get_exceptions`**
Tool call: `get_exceptions(severity="all")`
Result: 7 exceptions across 5 categories

**Step 8: Claude Renders Final Output**
Claude formats the results as:
- Metric cards (Total Gross Accrual, WBS Count, Exception Count)
- Summary table with per-WBS accrual amounts
- Exception report by severity
- Offer to download Excel or drill into details

### 6.3 Follow-Up Query Flow

After the primary flow, the user can ask follow-up questions. The agent has all data in session state and can answer without re-loading.

Examples:
- "Which wells have the largest accruals?" → Agent sorts accruals, shows top 10
- "Show me all negative accruals" → Agent calls `get_exceptions(severity="high")` or filters from cached data
- "What's the net-down journal entry?" → Agent calls `generate_net_down_entry()`
- "What does the outlook look like for the next 3 months?" → Agent calls `generate_outlook(months_forward=3)`
- "Tell me about WBS-1027" → Agent calls `get_accrual_detail(wbs_element="WBS-1027")`

### 6.4 Clarifying Question Logic

> **v2.0 Note:** The clarifying question was changed from "Missing ITD" handling to WI% mismatch handling. The mechanism now uses the `ask_user_question` tool (a dedicated tool the agent calls to pause and ask the user).

The agent asks clarifying questions in these situations. The **WI% mismatch** question is mandatory — the system prompt hard-codes this behavior to ensure the demo's key interactive moment happens 100% of the time.

| Trigger | Question | Options | Mandatory? |
|---------|----------|---------|-----------|
| WI% mismatch detected after accrual calculation | "How should I handle the WI% discrepancy?" | Use operator WI% / Use partner WI% / Average both | **YES — always ask, never skip** |
| Business unit is ambiguous | "Which business unit should I calculate for?" | Permian Basin / DJ Basin / Powder River / All | Only if ambiguous |

**Why the WI% question is hard-coded:** This is the demo's "wow moment." It shows the audience that the agent asks for human judgment instead of guessing — the single most important differentiator between an agent and a script. The system prompt contains an explicit, non-negotiable instruction to always pause and ask.

**Implementation:**
1. The system prompt (`agent/prompts.py`) mandates using `ask_user_question` when WI% mismatches are found.
2. The `ask_user_question` tool in `tool_definitions.py` requires `question` and `options` parameters.
3. The orchestrator detects `ask_user_question` tool calls and yields a `ClarifyEvent`, pausing the loop.
4. In Streamlit: the question renders as `st.radio()` with a "Continue" button. On click: the user's selection is wrapped as a `tool_result`, appended to `api_messages`, and the orchestrator resumes via `st.rerun()`.

---

## 7. System Prompt

> **v2.0 Note:** The system prompt below is the **original** design. The current system prompt is in `agent/prompts.py` and differs significantly — it uses the refactored tool names, WI% mismatch instead of Missing ITD, and a 4-step workflow (accruals → net-down with clarifying question → outlook → summary).

The following was the original system prompt design:

```
You are a CapEx Gross Accrual Agent — an AI assistant that helps Finance teams
calculate, analyze, and review capital expenditure accruals.

## Your Role
You automate Step 1 of the CapEx forecasting process: calculating gross accruals
by matching Work-in-Progress (VOW) estimates from engineers against
Incurred-to-Date (ITD) costs from SAP.

## The Core Calculation
Gross Accrual = VOW (engineer estimate of work done) - ITD (costs in SAP)

## How You Work
1. You have access to tools that load data from the WBS Master List, ITD extract,
   and VOW files.
2. You ALWAYS show your reasoning step by step.
3. You flag exceptions and explain why they matter.
4. When you encounter ambiguous situations (like missing data), you ASK the user
   how to proceed rather than making assumptions.
5. You can generate net-down journal entries and forward-looking outlooks.

## Your Tools
- load_wbs_master: Load the project registry filtered by business unit
- load_itd: Load SAP incurred-to-date costs for specific WBS elements
- load_vow: Load engineer work-in-progress estimates for specific WBS elements
- calculate_accruals: Run the core VOW - ITD calculation with exception detection
- get_exceptions: Retrieve exception report filtered by severity
- get_accrual_detail: Get detailed breakdown for a single WBS element
- generate_net_down_entry: Create the journal entry (current accrual minus prior)
- generate_outlook: Project future accruals from drill/frac schedule
- get_summary: Aggregate accruals by project type, business unit, or phase

## Exception Rules (You MUST Flag These)
- Missing ITD: WBS has VOW but no SAP costs → HIGH severity
- Negative Accrual: ITD > VOW (accrual < 0) → HIGH severity
- Missing VOW: WBS in master but no engineer submission → MEDIUM severity
- Large Swing: >25% change from prior period → MEDIUM severity
- Zero ITD: WBS has VOW but zero SAP costs → LOW severity

## Communication Style
- Use Finance/Accounting terminology naturally
- Show your work — every number should be traceable
- Be concise but thorough
- When presenting results, use formatted tables
- Always mention the total count, total dollar amount, and any exceptions
- Format large dollar amounts with commas and appropriate units ($14.3M, $127K)

## Workflow for Accrual Calculation
When asked to calculate accruals, follow this sequence:
1. Load WBS Master List for the requested business unit
2. Load ITD costs for all WBS elements found
3. Load VOW estimates for all WBS elements found
4. Report data coverage (matches, gaps, exceptions found so far)
5. **MANDATORY PAUSE — see "Clarifying Question Rules" below**
6. Run the accrual calculation with the user's chosen handling method
7. Run exception checks
8. Present the summary with formatted metrics and table
9. Offer to show exceptions detail, net-down entry, or outlook

## Clarifying Question Rules (MANDATORY)
These rules are NON-NEGOTIABLE. You must follow them exactly.

1. **Missing ITD Check (ALWAYS ASK):** After loading ITD data, if ANY WBS elements
   have VOW submissions but no matching ITD record, you MUST STOP and ask the user:
   "I found X WBS elements with VOW estimates but no ITD costs in SAP.
   How should I handle these?"
   Present exactly these three options:
   - Use VOW as full accrual (assume zero ITD)
   - Exclude from calculation and flag for review
   - Use last month's ITD as estimate
   Do NOT proceed to calculate_accruals until the user responds.
   Do NOT make this decision yourself, even if you think one option is obvious.

2. **Ambiguous Business Unit:** If the user's prompt does not clearly specify a
   single business unit, ask which one before calling load_wbs_master.

3. **Ambiguous Period:** If the user's prompt does not clearly specify a fiscal
   period, ask which period before proceeding.

## Important
- This is a DEMO with SYNTHETIC DATA. All numbers, well names, and WBS elements
  are fictional.
- You are demonstrating the concept of an agentic workflow — tool calling,
  reasoning, exception handling, and interactive decision-making.
- NEVER fabricate data. Only use numbers returned by your tools.
- When showing your thinking/reasoning steps, be specific about what you're doing
  and what you found. Reference actual counts and WBS element IDs.
- You are in DEMO MODE. The clarifying question about missing ITD is a critical
  part of the demonstration. It shows the audience that you ask for human judgment
  instead of guessing. You MUST always ask it when missing ITD is detected.
```

---

## 8. UI/UX Specification

### 8.1 Layout

```
+-------------------------------------------------------------+
|  HEADER: "CapEx Gross Accrual Agent"                          |
|  Subtitle: "Finance AI Demo - Synthetic Data"                 |
+------------------+------------------------------------------+
|                  |                                          |
|  SIDEBAR         |  MAIN CHAT AREA                          |
|  (280px)         |  (remaining width)                       |
|                  |                                          |
|  Agent Status    |  [Chat messages with streaming]           |
|  [circle] Ready  |                                          |
|                  |  USER: "Calculate the gross accrual      |
|  Tools Available |   for Permian Basin, Jan 2026"           |
|  [check] load_wbs|                                          |
|  [check] load_itd|  AGENT: [status expander with           |
|  [check] load_vow|         streaming breadcrumbs]           |
|  [check] calc    |         [clarifying question]            |
|  [check] except  |         [metric cards]                   |
|  [check] net_down|         [summary dataframe]              |
|  [check] outlook |         [exception report]               |
|  [check] summary |         [download button]                |
|                  |                                          |
|  Data Loaded     |  +----------------------------------+    |
|  47 WBS elements |  | Type your message...       [Send]|    |
|  44 ITD records  |  +----------------------------------+    |
|  45 VOW records  |                                          |
|                  |                                          |
|  [Reset Demo]    |                                          |
|                  |                                          |
+------------------+------------------------------------------+
```

### 8.2 Theme & Projector Readability

Dark theme for professional appearance at town hall (projected on screen).

```toml
# .streamlit/config.toml
[theme]
base = "dark"
primaryColor = "#4CAF50"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E2329"
textColor = "#FAFAFA"
```

**Projector Readability (test at 1080p projection distance):**
- Limit `st.dataframe` to 5-6 key columns during the demo view: `wbs_element`, `well_name`, `vow_amount`, `itd_amount`, `gross_accrual`, `exception_type`. Hide `afe_number`, `vendor_count`, `last_posting_date`, etc. — the audience doesn't need them on screen.
- Set `st.dataframe(height=300)` to prevent the table from dominating the viewport.
- Metric cards (`st.metric`) are naturally large and readable. No changes needed.
- Test the app on the actual projector/conference room screen before the demo. `st.dataframe` with 8+ columns at default size is unreadable past Row 5 of a conference room.

### 8.3 Components

**Header:**
- `st.title("CapEx Gross Accrual Agent")`
- `st.caption("Finance AI Demo - Synthetic Data")`

**Sidebar:**
- Agent status indicator (green dot = ready, yellow = thinking, red = error)
- Tools available checklist (static, all checked — shows audience what the agent can do)
- Data loaded counters (update after each load tool is called)
- Reset Demo button (`st.button("Reset Demo")` → clears `st.session_state`)

**Chat Interface:**
- `st.chat_message("user")` for user input
- `st.chat_message("assistant")` for agent responses
- `st.chat_input("Type your message...")` at the bottom

**Streaming Breadcrumbs:**
- **One `st.status` block per agent turn.** All breadcrumbs from a single user prompt (load_wbs → load_itd → load_vow → calculate) accumulate inside a single expander. Do not create a separate `st.status` per tool call — stacking 4-5 collapsed expanders clutters the chat.
- `st.status("Agent is thinking...", expanded=True)` during tool execution
- Each step written with `st.write()` inside the status expander
- **DO NOT** call `status.update(state="complete")` at the end. By default, `st.status` collapses when it transitions to `state="complete"`, which hides the breadcrumb trail. During the demo, the presenter needs the breadcrumbs to stay visible so they can narrate ("Look, it loaded ITD, then found a gap..."). Instead, update only the label: `status.update(label="Calculation complete!")` while leaving `state="running"`, or use `expanded=True` explicitly. Test this behavior during Phase 4 to confirm the breadcrumbs remain visible after the agent finishes.
- **CRITICAL — Latency Management:** Each `st.write()` line must appear *immediately when the tool call starts*, not after the tool returns. With 3 sequential tool calls (Master → ITD → VOW), there will be noticeable latency between each API round-trip. The breadcrumb pattern must be:
  1. Claude returns `tool_use` for `load_wbs_master` → immediately write "Loading WBS Master List..." → execute tool → write "Found 47 active WBS elements"
  2. Send tool result to Claude → Claude returns `tool_use` for `load_itd` → immediately write "Loading ITD extract from SAP..." → execute tool → write "Matched 44 of 47"
  3. Same pattern for `load_vow`
- This ensures the audience always sees activity. A 2-3 second gap with no visible change on a projected screen feels like the app froze. Streaming the "Loading..." line before the tool executes eliminates this.

**Clarifying Questions:**
- Rendered as `st.radio()` with 3 options
- "Continue" button (`st.button("Continue")`) to proceed
- User's selection is recorded and passed to the next tool call

**Results Display:**
- `st.columns(3)` for metric cards:
  - `col1.metric("Total Gross Accrual", "$14.3M", "+$1.5M")`
  - `col2.metric("WBS Elements", "47", "42 calculated")`
  - `col3.metric("Exceptions", "7", "2 high severity")`
- `st.dataframe(accrual_df, use_container_width=True)` for the summary table
- `st.expander("Exception Report", expanded=False)` for detailed exceptions — **collapsed by default** to avoid overwhelming the audience with a wall of text. The metric card above ("Exceptions: 7, 2 high severity") signals that exceptions exist; the user can expand to see details. During the demo, the presenter can click to expand it after narrating the summary.
- `st.download_button()` for Excel export

**Excel Download:**
- `st.download_button("Download Accrual Schedule (Excel)", data=excel_bytes, file_name="permian_basin_accruals_jan_2026.xlsx")`
- Generated using `openpyxl` with two sheets: "Accrual Summary" and "Exception Report"

### 8.4 State Management

The app maintains two parallel message histories — one for display, one for the Claude API. This separation is critical because Streamlit re-runs the entire script on every interaction (including clicking "Continue" on a clarifying question), and the Claude API conversation must include `tool_use` and `tool_result` blocks that are never shown to the user.

**Dual Message History:**

| Key | Type | Description |
|-----|------|-------------|
| `display_messages` | list[dict] | What the user sees in the chat UI. Each entry has `role` ("user" or "assistant") and `content` (rendered text, markdown, or component). |
| `api_messages` | list[dict] | The full Claude API conversation history including `tool_use` and `tool_result` content blocks. This is what gets sent to the API on each call. |

**Data State:**

| Key | Type | Description |
|-----|------|-------------|
| `wbs_data` | DataFrame | Loaded WBS master data |
| `itd_data` | DataFrame | Loaded ITD extract |
| `vow_data` | DataFrame | Loaded VOW estimates |
| `prior_data` | DataFrame | Loaded prior period accruals |
| `accrual_results` | dict | Calculated accrual results |
| `exceptions` | list[dict] | Detected exceptions |

**CSV Caching:** Use `@st.cache_data` on the CSV-reading functions in `data_loader.py`. The synthetic CSVs never change during a session, so reloading them on every Streamlit rerun is wasteful and adds latency. This is especially important because Streamlit reruns the full script on every interaction (chat input, button click, radio selection).

**UI State:**

| Key | Type | Description |
|-----|------|-------------|
| `agent_status` | str | "ready", "thinking", "error" |
| `data_loaded` | dict | Counts of loaded records per source |
| `clarification_pending` | bool | Whether a clarifying question is awaiting response |
| `clarification_response` | str | User's selected option |

### 8.5 Clarifying Question Resume Logic

This is the most complex part of the Streamlit integration. When the agent asks a clarifying question, the app must "pause" the agent loop and resume it after the user responds. Streamlit has no native pause/resume — it re-runs the entire script on every interaction.

**State Machine:**

```
                     ┌──────────────────────────────────────┐
                     │                                      │
                     ▼                                      │
IDLE ──[user types prompt]──> RUNNING ──[tool_use]──> RUNNING
                                │                          │
                                │ [text with clarifying Q]  │
                                ▼                          │
                           PAUSED_FOR_CLARIFICATION        │
                                │                          │
                                │ [user clicks Continue]    │
                                ▼                          │
                           RESUMING ───────────────────────┘
                                │
                                │ [no more tool calls]
                                ▼
                           IDLE (response complete)
```

**Resume Procedure — "Flag & Rerun" Pattern:**

Do NOT call `orchestrator.run()` inside the `if st.button("Continue"):` block. Streamlit renders streamed content inside the button's callback scope, and that content vanishes on the next script rerun (which happens on any subsequent interaction). Instead, use a flag-and-rerun pattern:

**Inside `if st.button("Continue"):`:**
1. Read `st.session_state.clarification_response` (the radio button selection)
2. Map the selection to the appropriate value (e.g., "Use VOW as full accrual" → "use_vow_as_accrual")
3. Construct a new `user` message: `"I'd like to: use_vow_as_accrual"`
4. Append this message to `st.session_state.api_messages`
5. Append a display-friendly version to `st.session_state.display_messages`
6. Set `st.session_state.clarification_pending = False`
7. Set `st.session_state.run_agent = True`
8. Call `st.rerun()` — this forces a full script rerun

**In the main app flow (outside any button block):**
```python
if st.session_state.get("run_agent", False):
    st.session_state.run_agent = False
    # Now call the orchestrator in the main rendering scope
    orchestrator.run(st.session_state.api_messages)
```

**Why this matters:** The orchestrator's streamed output (breadcrumbs, tool results, final response) must render in the main chat container scope so it persists across Streamlit reruns. If it renders inside a button callback, it's scoped to that callback and disappears the next time Streamlit reruns the script.

**Key Requirement:** The orchestrator must accept the full `api_messages` list as input and append to it — never rebuild from scratch. This preserves the Claude conversation context across the pause/resume boundary.

**This same "Flag & Rerun" pattern applies to the initial user prompt too.** When the user types a message in `st.chat_input`, the app should append it to message state, set `run_agent = True`, and let the main flow handle the orchestrator call.

---

## 9. Demo Script

### 9.1 Full Script (2-3 minutes at town hall)

**Setup — 30 seconds:**
> "I want to show you what an AI agent looks like in action. This is a prototype I built using synthetic data — no real company numbers. It demonstrates what the CapEx Gross Accrual Agent will do when we build it on Databricks later this year."

*[Open app in browser. Audience sees dark-themed chat interface with sidebar.]*

**Run the Demo — 2 minutes:**

*[Paste from notes app — do NOT type live under presentation pressure]:* `Calculate the gross accrual for Permian Basin, January 2026`

*[As the agent streams its thinking]:*
> "Watch what's happening — the agent is reading data from three sources: the WBS master list, the SAP ITD extract, and the engineer VOW submissions. It's matching records across these files — the same thing our controllers do manually every month."

*[Agent shows: "Found 47 active WBS elements... Matched 44 of 47 to ITD... Matched 42 of 47 to VOW..."]*

> "It found data gaps — 3 WBS elements have VOW but no ITD. Instead of guessing, watch what it does..."

*[Agent asks clarifying question with radio buttons]:*

> "Here's the key part — the agent found a data issue and it's asking ME how to handle it. This is what makes it an agent, not just a calculator. It knows the exception rules, and it knows when to ask for human judgment."

*[Select "Use VOW as full accrual (assume zero ITD)" → Click Continue]*

*[Agent calculates, shows exceptions, presents results]:*

> "In about 30 seconds, it calculated accruals for 47 wells, flagged 7 exceptions across 5 categories, and produced a downloadable accrual schedule. In production, this replaces 40-60 hours of manual work per month. And every number is traceable."

**Follow-Up — 30 seconds:**

*[Type into chat]:* `Show me all negative accruals`

> "I can have a conversation with it. It remembers the context and the data it already loaded."

*[Agent responds with the 1 negative accrual — WBS-1027, ITD exceeds VOW by $127K]*

**Close — 15 seconds:**

> "This is Agent #1. Once the pattern is proven, the same architecture works for depreciation checks, forecast variance, journal entry review — anything with rules and data. Questions?"

### 9.2 Backup Plan

If WiFi fails or the API is down:
1. Pre-record a 2-minute video of the exact demo flow above
2. Have the video ready on local machine (not streaming)
3. Play video and narrate over it
4. Mention "the live version is available at [URL] — try it after the meeting"

---

## 10. Risks & Mitigations

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Claude API outage during demo** | Low | Critical | Pre-record backup video. Cache a successful response and implement fallback mode that replays it. |
| **API rate limit hit** | Low | High | Use a dedicated API key. Test key limits before demo. Sonnet has generous limits. |
| **Streamlit Cloud cold start** | Medium | Medium | Hit the app URL 5 minutes before presenting to warm it up. |
| **Slow API response** | Medium | Medium | Use streaming to show progress immediately. Audience sees thinking in real-time, so 10-15 second response feels interactive, not frozen. |
| **LLM hallucinates data** | Low | High | System prompt explicitly says "NEVER fabricate data." Tools return real data from CSVs. Test the exact demo prompts multiple times to verify consistent behavior. |
| **Unexpected tool call order** | Medium | Low | System prompt provides a recommended workflow sequence. The tools are designed to work in any order, but test the primary flow repeatedly. |

### 10.2 Presentation Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **WiFi fails** | Medium | Critical | Pre-recorded backup video on local machine. |
| **Demo takes too long** | Medium | High | Practice the exact prompts. Time it. Cut to 2 minutes max. Don't improvise prompts. |
| **Audience asks "is this real data?"** | High | Medium | Banner on every screen: "Finance AI Demo - Synthetic Data." Say it verbally at the start. |
| **Someone asks "when can I use this?"** | High | Low | "This is Agent #1 on our 2026 roadmap. We're building it on Databricks this year." |
| **Someone asks about data security** | Medium | Medium | "This demo uses synthetic data and runs on a public cloud. The production version will run inside our firewall on Databricks with full enterprise security." |
| **Projector resolution issues** | Medium | Medium | Test on the exact projector beforehand. Dark theme with large fonts helps readability. |

### 10.3 Political Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **"This will take my job"** | Medium | High | Frame as "this handles the data grunt work so you can focus on analysis and judgment." Emphasize the clarifying question — the agent ASKS the human, it doesn't replace them. |
| **"The calculations are wrong"** | Low | High | Test calculations against manual Excel. Have a reconciliation sheet ready. The formulas are VOW - ITD — same as what controllers do today. |
| **"Why not just use Excel macros?"** | Low | Medium | "Macros don't reason, don't catch exceptions contextually, don't ask clarifying questions, and don't improve over time. This is a conversational interface that understands the domain." |

---

## 11. Build Phases

### Phase 1 — Data Foundation

**Status:** `DONE`
**Started:** 2026-02-18
**Completed:** 2026-02-18

**Goal:** Generate all 5 synthetic CSV files, build data-loading utilities, and verify that data relationships and intentional exceptions are correct.

**Scope — Files to Create:**
```
capex-agent-demo/
├── data/
│   ├── generate_synthetic_data.py   # Script to generate all CSVs
│   ├── wbs_master.csv               # Generated: 50 rows
│   ├── itd_extract.csv              # Generated: 44 rows (6 missing/zero)
│   ├── vow_estimates.csv                  # Generated: 45 rows (5 missing)
│   ├── prior_period_accruals.csv    # Generated: 48 rows
│   └── drill_schedule.csv           # Generated: ~60 rows (20 wells x 3-5 phases)
├── utils/
│   └── data_loader.py               # Functions to load and validate CSVs
├── requirements.txt                  # pandas, openpyxl
└── tests/
    └── test_data.py                  # Validation tests
```

**Acceptance Criteria:**
- [x] 1. Run `python data/generate_synthetic_data.py` → produces all 5 CSV files with correct schemas
- [x] 2. `wbs_master.csv` has exactly 50 rows with correct column types and realistic values
- [x] 3. `itd_extract.csv` has 47 rows; 3 WBS elements from wbs_master are completely missing; 3 have `itd_amount = 0`
- [x] 4. `vow_estimates.csv` has 45 rows; 2 WBS elements present in wbs_master are missing from this file
- [x] 5. 1 WBS element has ITD > VOW (negative accrual trigger)
- [x] 6. 1 WBS element has accrual >25% different from prior period (large swing trigger)
- [x] 7. Joining `wbs_master` to `itd_extract` on `wbs_element` produces 47 matches and 3 gaps
- [x] 8. Joining `wbs_master` to `vow_estimates` on `wbs_element` produces 45 matches and 5 gaps
- [x] 9. `drill_schedule.csv` has 75 rows with sequential dates per WBS (Spud < TD < Frac Start < Frac End < First Production)
- [x] 10. All dollar amounts are realistic (wells: $2M-$15M; phases: $100K-$5.5M)
- [x] 11. **Row count caps enforced:** `wbs_master` <= 50 rows, `itd_extract` <= 47 rows, `vow_estimates` <= 48 rows, `prior_period_accruals` <= 50 rows, `drill_schedule` <= 80 rows. The test must assert these caps to prevent accidental bloat that would degrade API performance.
- [x] 12. `pytest tests/test_data.py` passes all 64 assertions (including row count caps)

**Hand-off to Phase 2:** Five validated CSV files in `data/` directory, `data_loader.py` utility functions, and passing tests.

**Estimated Time:** 1-2 hours

---

### Phase 2 — Core Agent Tools

**Status:** `DONE`
**Started:** 2026-02-18
**Completed:** 2026-02-18

**Goal:** Build the 9 Python tool functions that the agent will call. No UI, no LLM. Each function is independently testable by calling it directly.

**Scope — Files to Create/Modify:**
```
capex-agent-demo/
├── agent/
│   ├── __init__.py
│   ├── tools.py                  # All 9 tool functions
│   └── tool_definitions.py      # Claude API tool schemas (JSON)
├── utils/
│   ├── data_loader.py            # (from Phase 1, may need updates)
│   └── formatting.py             # Output formatting helpers
└── tests/
    ├── test_data.py              # (from Phase 1)
    └── test_tools.py             # Tool function unit tests
```

**Build Order (within this phase):**

Build and test tools in this order. The first group is P0 (demo-critical); the second group is P1/P2 and can be deferred if time is short.

1. **P0 — Core calculation tools (build first):** `load_wbs_master`, `load_itd`, `load_vow`, `calculate_accruals`, `get_exceptions`, `get_accrual_detail`
2. **P1/P2 — Extended tools (build second):** `generate_net_down_entry`, `get_summary`, `generate_outlook`

**Complexity flag:** `generate_outlook` is the hardest tool in this phase. It involves date math across month boundaries, Linear by Day allocation with partial-month handling, and lump-sum logic. Budget accordingly — this tool alone may take as long as the 6 core tools combined.

**Acceptance Criteria:**

*P0 — Core tools:*
- [x] 1. `load_wbs_master("Permian Basin")` returns dict with ~35 WBS elements, correct schema
- [x] 2. `load_wbs_master("all")` returns dict with 50 WBS elements
- [x] 3. `load_itd([list of 47 WBS IDs])` returns dict with 44 matched, 3 unmatched, 3 zero-ITD
- [x] 4. `load_vow([list of 47 WBS IDs])` returns dict with 42-45 matched, unmatched list
- [x] 5. `calculate_accruals("use_vow_as_accrual")` returns correct gross accruals and detects all 5 exception types
- [x] 6. `calculate_accruals("exclude_and_flag")` excludes missing-ITD WBS from total
- [x] 7. `get_exceptions("all")` returns all exceptions with correct severity assignments
- [x] 8. `get_exceptions("high")` returns only HIGH severity exceptions
- [x] 9. `get_accrual_detail("WBS-1027")` returns the negative accrual detail with ITD > VOW

*P1/P2 — Extended tools:*
- [x] 10. `generate_net_down_entry()` returns correct net-down = current - prior for each WBS
- [x] 11. `generate_outlook(3)` returns 3 months of projected accruals from drill schedule
- [x] 12. `get_summary("business_unit")` returns accruals grouped by BU with correct totals

*Infrastructure:*
- [x] 13. `tool_definitions.py` contains valid Claude API tool schemas for all 9 tools
- [x] 14. `python tests/test_tools.py` passes all assertions

**Hand-off to Phase 3:** Working tool functions that can be called directly from Python, plus Claude-compatible tool definitions.

**Estimated Time:** 2-3 hours

---

### Phase 3 — Agent Orchestration

**Status:** `NOT STARTED`
**Started:** —
**Completed:** —

**Goal:** Wire up Claude API with tool_use. Build the agent loop: prompt → think → tool call → respond. Add clarifying question logic. Testable from CLI — no Streamlit needed.

**Scope — Files to Create/Modify:**
```
capex-agent-demo/
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py           # Agent loop: send prompt, handle tool calls, loop
│   ├── tools.py                  # (from Phase 2)
│   ├── tool_definitions.py       # (from Phase 2)
│   └── prompts.py                # System prompt text
├── cli.py                        # CLI entry point for testing
├── .env.example                  # ANTHROPIC_API_KEY placeholder
└── requirements.txt              # Add: anthropic>=0.18.0
```

**Key Implementation Details:**

`orchestrator.py` must handle:
1. Sending the system prompt + user message + tool definitions to Claude
2. Receiving a response that may contain `tool_use` content blocks
3. Executing the requested tool function from `tools.py`
4. Sending the tool result back to Claude as a `tool_result` message
5. Looping until Claude returns a final text response (no more tool calls)
6. Handling streaming (tokens arrive incrementally)
7. Detecting when Claude asks a clarifying question (the response text contains options for the user)
8. **Error handling:** Wrap tool dispatch in try/except. If a tool call fails (unknown tool name, malformed arguments, runtime error), return an error message as the `tool_result` so Claude can recover gracefully (e.g., "Tool error: {exception}. Please try a different approach."). Do not let tool errors crash the orchestrator loop.

`prompts.py` contains the full system prompt from Section 7 of this PRD.

`cli.py` is a simple script that:
1. Reads the API key from `.env`
2. Accepts user input from stdin
3. Calls the orchestrator
4. Prints tool calls and results to stdout
5. Prints the final response
6. Loops for follow-up questions

**Acceptance Criteria:**
- [ ] 1. Run `python cli.py`, type "Calculate the gross accrual for Permian Basin, January 2026"
- [ ] 2. Agent calls `load_wbs_master`, `load_itd`, `load_vow` in sequence (or parallel)
- [ ] 3. Agent asks a clarifying question about missing ITD handling (printed to stdout)
- [ ] 4. User types their selection, agent calls `calculate_accruals` with the chosen option
- [ ] 5. Agent calls `get_exceptions` to report exceptions
- [ ] 6. Final output includes total gross accrual, WBS count, and exception count
- [ ] 7. Follow-up query "Show me all negative accruals" returns correct filtered results
- [ ] 8. Follow-up query "What's the net-down entry?" calls `generate_net_down_entry` and returns formatted result
- [ ] 9. The orchestrator handles streaming (partial tokens printed as they arrive)
- [ ] 10. Errors (bad API key, network failure) are caught and displayed gracefully

**Hand-off to Phase 4:** Working agent that runs from CLI with full tool-calling loop, clarifying question handling, and streaming.

**Estimated Time:** 2-3 hours

---

### Phase 4 — Streamlit UI

**Status:** `NOT STARTED`
**Started:** —
**Completed:** —

**Goal:** Build the Streamlit chat interface that wraps the agent orchestrator. Streaming breadcrumbs, clarifying question components, formatted results display, sidebar.

**Scope — Files to Create/Modify:**
```
capex-agent-demo/
├── app.py                        # Streamlit app (main entry point)
├── agent/
│   ├── orchestrator.py           # (from Phase 3, adapt for Streamlit streaming)
│   └── ...
├── utils/
│   ├── formatting.py             # (from Phase 2, may need Streamlit-specific updates)
│   └── excel_export.py           # Generate downloadable Excel workbook
├── .streamlit/
│   └── config.toml               # Dark theme configuration
└── requirements.txt              # Add: streamlit>=1.30.0
```

**Key Implementation Details:**

`app.py` structure:
1. Page config: `st.set_page_config(page_title="CapEx Gross Accrual Agent", layout="wide")`
2. Sidebar: Agent status, tools checklist, data counts, reset button
3. Chat history: Loop through `st.session_state.messages`, render with `st.chat_message`
4. Chat input: `st.chat_input("Type your message...")`
5. On user input: call orchestrator, stream results into `st.status` expander
6. Clarifying question: render as `st.radio` + `st.button("Continue")`
7. Results: metric cards, dataframe, exception expander, download button

Streaming integration:
- The orchestrator yields events (thinking text, tool calls, tool results, final text)
- `app.py` consumes these events and renders them in real-time using `st.status` and `st.write`

**Acceptance Criteria:**
- [ ] 1. `streamlit run app.py` opens the app in browser
- [ ] 2. Dark theme renders correctly (dark background, green accents, white text)
- [ ] 3. Sidebar shows "Agent Status: Ready" and lists all 9 tools
- [ ] 4. Typing a prompt triggers the agent; breadcrumbs stream in a `st.status` expander
- [ ] 5. Clarifying question renders as radio buttons with "Continue" button
- [ ] 6. Selecting an option and clicking Continue resumes the agent
- [ ] 7. Results display as metric cards: Total Gross Accrual, WBS Elements, Exceptions
- [ ] 8. Accrual summary table renders as `st.dataframe` with sortable columns
- [ ] 9. Exception report renders in an expander with severity color coding
- [ ] 10. "Download Accrual Schedule (Excel)" button downloads a valid .xlsx file with 2 sheets
- [ ] 11. Follow-up questions work without re-loading data
- [ ] 12. "Reset Demo" button clears all state and returns to initial view
- [ ] 13. App handles errors gracefully (shows error message, doesn't crash)
- [ ] 14. Full demo flow (prompt → clarifying Q → results → follow-up) runs in under 3 minutes

**Hand-off to Phase 5:** Working Streamlit app with full chat interface, streaming, and all core functionality.

**Estimated Time:** 2-3 hours

---

### Phase 5 — Polish & Demo-Ready

**Status:** `NOT STARTED`
**Started:** —
**Completed:** —

**Goal:** Add net-down journal entry and outlook tools to the UI, Excel download with formatted sheets, final theme polish, deploy to Streamlit Cloud, and rehearse the demo script.

**Scope — Files to Create/Modify:**
```
capex-agent-demo/
├── app.py                        # (from Phase 4, add net-down and outlook rendering)
├── utils/
│   └── excel_export.py           # (from Phase 4, add formatting, multiple sheets)
├── .streamlit/
│   └── config.toml               # (from Phase 4, final theme tweaks)
├── .streamlit/
│   └── secrets.toml              # For Streamlit Cloud deployment (API key)
├── README.md                     # Deployment instructions + demo script
└── Procfile or similar           # If needed for hosting platform
```

**Acceptance Criteria:**
- [ ] 1. "What's the net-down journal entry?" renders a formatted journal entry with debit/credit accounts, amounts, and per-WBS detail
- [ ] 2. "What does the outlook look like for the next 3 months?" renders a monthly projection table with well counts and expected accruals
- [ ] 3. Excel download includes 3 sheets: "Accrual Summary", "Exception Report", "Detail by WBS" — all with proper formatting (headers, number formats, column widths)
- [ ] 4. App deployed to Streamlit Cloud (or HF Spaces) with public URL
- [ ] 5. App cold-starts within 30 seconds
- [ ] 6. Full demo flow rehearsed 3+ times, consistently under 3 minutes
- [ ] 7. Backup video recorded (2-minute screen recording of successful demo)
- [ ] 8. Demo script (Section 9) rehearsed verbally with timing

**Deployment checklist:**
- [ ] `ANTHROPIC_API_KEY` set in Streamlit Cloud secrets
- [ ] App URL tested on multiple browsers
- [ ] App tested on projected resolution (1920x1080 typical)
- [ ] Backup video saved locally
- [ ] Demo script printed/accessible during presentation

**Hand-off:** Demo-ready app with public URL, backup video, and rehearsed script.

**Estimated Time:** 1-2 hours

---

## Appendix A: Project Structure (Complete)

```
capex-agent-demo/
├── app.py                        # Streamlit app (main entry point)
├── cli.py                        # CLI entry point for testing (Phase 3)
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py           # Agent loop: prompt → think → tool call → respond
│   ├── tools.py                  # 9 Python tool functions
│   ├── tool_definitions.py       # Claude API tool schemas
│   ├── prompts.py                # System prompt
│   └── clarifications.py         # Clarifying question logic (optional, can be in orchestrator)
├── data/
│   ├── generate_synthetic_data.py # Script to generate all CSVs
│   ├── wbs_master.csv
│   ├── itd_extract.csv
│   ├── vow_estimates.csv
│   ├── prior_period_accruals.csv
│   └── drill_schedule.csv
├── utils/
│   ├── data_loader.py            # CSV loading and validation
│   ├── formatting.py             # Output formatting (tables, summaries)
│   └── excel_export.py           # Generate downloadable Excel
├── tests/
│   ├── test_data.py              # Data validation tests
│   └── test_tools.py             # Tool function unit tests
├── .streamlit/
│   └── config.toml               # Theme settings
├── .env.example                  # ANTHROPIC_API_KEY=sk-ant-...
├── requirements.txt              # streamlit, anthropic, pandas, openpyxl
└── README.md                     # Setup, deployment, demo script
```

## Appendix B: Requirements

```
streamlit>=1.30.0
anthropic>=0.18.0
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
```

## Appendix C: Glossary

| Term | Definition |
|------|-----------|
| **AFE** | Authorization for Expenditure — the approved budget for a capital project |
| **Accrual** | Cost for work completed but not yet invoiced (VOW - ITD) |
| **BU** | Business Unit — an operating division (e.g., Permian Basin) |
| **D&C** | Drilling & Completions — the process of drilling and completing wells |
| **Frac** | Hydraulic fracturing — the well completion process |
| **Gross Accrual** | VOW - ITD for each WBS element |
| **ITD** | Incurred-to-Date — actual costs posted in SAP to date |
| **Net-Down** | Current gross accrual minus prior period gross accrual — the journal entry amount |
| **Outlook** | Forward-looking forecast of future costs based on drill/frac schedule |
| **Spud** | Drilling start date (when the drill bit first touches ground) |
| **VOW** | Value of Work — the engineer's estimate of total work completed to date on a project. This is the primary term used by the organization. Also known as WIP (Work-in-Progress) in standard accounting. |
| **WBS** | Work Breakdown Structure — SAP's project identifier (each well gets a WBS) |
| **WIP** | Work-in-Progress — standard accounting term for VOW. This organization uses VOW as the preferred term. |

---

## Session Log

<!--
HOW TO USE THIS LOG:
- At the START of each session: read the latest entry to see where you left off
- At the END of each session: add a new entry below with what was done, what's next, and any blockers
- Update the Build Progress Dashboard at the top of this document
- Check off completed acceptance criteria in the relevant phase
-->

#### Session 1 — 2026-02-18
**Duration:** ~1 hour
**Phase worked on:** Phase 1 — Data Foundation

**What was done:**
- Created project scaffolding (capex-agent-demo/ subdirectory, requirements.txt, __init__.py files)
- Wrote 64 pytest tests covering all 12 acceptance criteria (TDD — tests first)
- Built deterministic synthetic data generator (seed=42) with hardcoded exception triggers
- Generated all 5 CSV files: wbs_master (50), itd_extract (47), vow_estimates (45), prior_period_accruals (48), drill_schedule (75)
- Built data_loader.py with 5 loader functions
- All 64 tests passing

**Acceptance criteria completed this session:**
- All 12 Phase 1 criteria checked off

**What to do next:**
- Start Phase 2: Build the 9 agent tool functions in `agent/tools.py`
- Begin with P0 core tools: load_wbs_master, load_itd, load_vow, calculate_accruals, get_exceptions, get_accrual_detail

**Blockers / Issues:**
- None

**Files created/modified:**
- `capex-agent-demo/data/generate_synthetic_data.py` — Deterministic data generator
- `capex-agent-demo/data/*.csv` — 5 generated CSV files
- `capex-agent-demo/utils/data_loader.py` — CSV loading functions
- `capex-agent-demo/tests/test_data.py` — 64 validation tests
- `capex-agent-demo/requirements.txt` — pandas, openpyxl, pytest

#### Session 2 — 2026-02-18
**Duration:** ~1.5 hours
**Phase worked on:** Phase 2 — Core Agent Tools

**What was done:**
- Built all 9 agent tool functions in `agent/tools.py` using TDD (tests first)
- P0 tools: load_wbs_master, load_itd, load_vow, calculate_accruals, get_exceptions, get_accrual_detail
- P1/P2 tools: generate_net_down_entry, get_summary, generate_outlook
- Created `utils/formatting.py` with dollar formatting helper
- Created `agent/tool_definitions.py` with Claude API JSON schemas for all 9 tools
- All tools use session_state dict pattern for sharing data between calls
- calculate_accruals detects all 5 exception types with correct severities
- generate_outlook implements Linear by Day allocation with month-boundary handling
- 72 new tests in test_tools.py, 136 total tests passing (64 Phase 1 + 72 Phase 2)

**Acceptance criteria completed this session:**
- All 14 Phase 2 criteria checked off (AC 1-14)

**What to do next:**
- Start Phase 3: Build agent orchestrator with Claude API integration
- Create `agent/orchestrator.py`, `agent/prompts.py`, `cli.py`
- Wire up tool_use loop with streaming

**Blockers / Issues:**
- None

**Files created/modified:**
- `capex-agent-demo/agent/tools.py` — 9 tool functions (~370 lines)
- `capex-agent-demo/agent/tool_definitions.py` — Claude API tool schemas
- `capex-agent-demo/utils/formatting.py` — Dollar formatting helper
- `capex-agent-demo/tests/test_tools.py` — 72 tests for all tools + definitions
- `capex-agent-demo/docs/plans/2026-02-18-phase2-core-agent-tools-design.md` — Design doc
- `capex-agent-demo/docs/plans/2026-02-18-phase2-core-agent-tools.md` — Implementation plan

#### Session 3 — 2026-02-18
**Duration:** ~2 hours
**Phase worked on:** Phases 3 & 4 — Agent Orchestration & Streamlit UI

**What was done:**
- Refactored data model: consolidated 5 CSV files down to 2 (wide wbs_master table + drill_schedule)
- Rebuilt all 9 agent tool functions to work with the new data model (direct CSV reads, no session state)
- Replaced `missing_itd_handling` parameter with WI% mismatch as the clarifying question trigger
- Built `agent/orchestrator.py` with streaming Claude API integration (`messages.stream()`)
- Created `agent/prompts.py` with system prompt including `ask_user_question` tool for clarifying questions
- Built `cli.py` for interactive terminal testing
- Built `app.py` Streamlit UI with chat interface, tool breadcrumbs, clarifying question widget (radio + Continue button)
- Created `.streamlit/config.toml` with dark theme for projector readability
- Created `utils/excel_export.py` for Close Package Excel download
- Added ClarifyEvent to orchestrator for pause/resume on clarifying questions
- Summarized `generate_outlook_load_file` results to ~600 tokens instead of sending all 72 rows (~4,100 tokens)
- 58 tests passing (test suite adapted to new data model)

**Acceptance criteria completed this session:**
- All Phase 3 and Phase 4 criteria

**What to do next:**
- Phase 5 polish: fix remaining items from deep-dive review (`docs/plans/fix-list.md`)

**Blockers / Issues:**
- None

**Files created/modified:**
- `capex-agent-demo/agent/orchestrator.py` — Streaming agent loop with tool dispatch and ClarifyEvent
- `capex-agent-demo/agent/prompts.py` — System prompt with ask_user_question tool
- `capex-agent-demo/agent/tools.py` — Rebuilt 9 tools for new data model
- `capex-agent-demo/agent/tool_definitions.py` — Updated Claude API tool schemas
- `capex-agent-demo/cli.py` — Interactive CLI for testing
- `capex-agent-demo/app.py` — Streamlit UI with chat, breadcrumbs, clarifying questions
- `capex-agent-demo/.streamlit/config.toml` — Dark theme config
- `capex-agent-demo/utils/excel_export.py` — Excel close package generator
- `capex-agent-demo/data/generate_synthetic_data.py` — Updated for 2-file data model

#### Session 4 — 2026-02-18
**Duration:** ~30 min
**Phase worked on:** Phase 5 — Polish (MEDIUM items from fix-list.md)

**What was done:**
- Removed dead `utils/formatting.py` (format_dollar was never imported by any code)
- Bumped `max_tokens` from 4096 to 8192 in orchestrator to avoid truncation on large tables
- Verified `.env.example` has correct content (no changes needed)
- Deferred sidebar download generation until after agent runs first tool (avoids computation at page load)
- Updated PRD build dashboard (Phases 3-5 marked correctly)
- Added session log entries for Sessions 3-4

**What to do next:**
- Fix CRITICAL items: streaming, breadcrumb persistence
- Fix HIGH items: noisy double-exception on WBS-1005

**Blockers / Issues:**
- None

**Files created/modified:**
- `capex-agent-demo/utils/formatting.py` — Deleted (dead code)
- `capex-agent-demo/agent/orchestrator.py` — max_tokens 4096 → 8192
- `capex-agent-demo/app.py` — Sidebar downloads deferred until agent runs
- `planning/prd.md` — Updated build dashboard and session log

#### Session 5 — 2026-02-18
**Duration:** ~30 min
**Phase worked on:** Phase 5 — Polish (remaining items from fix-list.md)

**What was done:**
- Verified all CRITICAL items (1-4) and HIGH items (5-7) from fix-list.md were already implemented in Sessions 3-4
- Archived 4 completed plan documents to `docs/plans/archive/` (item #8)
- Updated PRD v1.4 → v2.0: added notes throughout Sections 3-7 documenting the refactored data model (2 CSVs vs 5), current tool architecture, updated exception types, and corrected technology references (item #10)
- Marked Phase 5 as DONE in build dashboard, updated next action
- Added CLI ASCII fallback for emoji icons via `CAPEX_ASCII=1` env var (item #14)
- Documented why `lru_cache` is preferred over `@st.cache_data` in data_loader.py (item #15)
- All 62 tests passing, no regressions

**What to do next:**
- Demo is ready to run: `streamlit run capex-agent-demo/app.py`
- No remaining blockers

**Blockers / Issues:**
- None

**Files created/modified:**
- `planning/prd.md` — Updated to v2.0 with architecture notes, build dashboard, session log
- `capex-agent-demo/cli.py` — Added ASCII icon fallback (`CAPEX_ASCII=1`)
- `capex-agent-demo/utils/data_loader.py` — Added docstring note on lru_cache vs st.cache_data
- `capex-agent-demo/docs/plans/archive/` — Moved 4 completed plan docs

<!--
### Session Template (copy and fill in):

#### Session N — [Date]
**Duration:** X hours
**Phase worked on:** Phase N
**What was done:**
- Item 1
- Item 2

**Acceptance criteria completed this session:**
- [list which numbered items were checked off]

**What to do next:**
- Next step 1
- Next step 2

**Blockers / Issues:**
- None (or describe)

**Files created/modified:**
- `path/to/file.py` — description of change
-->

---

*End of PRD*
