# Capex Close Enhancements Design

**Date:** 2026-02-18
**Status:** Approved
**Approach:** Step-by-step close process (Approach 2)

## Overview

Enhance the capex agent demo to demonstrate a complete monthly close process: gross/net accrual calculation, WI% net-down adjustments, future outlook allocation, and a OneStream-ready monthly load file. This transforms the demo from a simple accrual calculator into a full capex close solution.

## Data Model

### Revised WBS Master (wide table, one row per well)

The WBS master becomes the single source of truth. ~15-20 wells.

**Core identifiers:**
- `wbs_element` — unique WBS code
- `well_name` — human-readable well name
- `afe_number` — authorization for expenditure
- `business_unit` — Permian Basin, DJ Basin, Powder River
- `status` — Active, Complete, Suspended
- `start_date` — well start date

**Working interest:**
- `wi_pct` — actual/correct WI% (e.g., 0.75)
- `system_wi_pct` — what's currently in the ERP system (e.g., 0.80)

**Per cost category (×4: drill, comp, fb, hu):**
- `{cat}_budget` — AFE/system budget
- `{cat}_itd` — inception-to-date actuals
- `{cat}_vow` — value of work estimate
- `{cat}_ops_budget` — operations budget (well-type cost from ops)

**Prior period:**
- `prior_gross_accrual` — total prior period gross accrual

### Drill Schedule (separate CSV, unchanged)

Retains phase dates for time-based outlook allocation:
- `wbs_element`, `planned_phase`, `planned_date`, `estimated_cost`
- Phases: Spud, TD, Frac Start, Frac End, First Production

## Three-Step Calculation Chain

### Step 1: Accruals (Gross & Net)

Per well, per category (drill/comp/fb/hu):

```
Gross Accrual = VOW - ITD
Net Accrual   = Gross Accrual × WI%
```

Totals summed across all categories per well.

**Exceptions flagged:**
- Negative accruals (ITD > VOW)
- Missing VOW or ITD
- Large swings vs. prior period (>25% change)

### Step 2: Net-Down WI% Adjustment

Per well (applied to total cost across all categories):

```
Total System Cost  = SUM(ITD + Gross Accrual) across all categories
WI% Discrepancy    = System WI% - Actual WI%
Net-Down Adjustment = Total System Cost × WI% Discrepancy
Adjusted Net Cost   = Total System Cost × Actual WI%
```

**Exceptions flagged:**
- Any well with WI% mismatch (the adjustment itself is the finding)
- Large dollar-impact adjustments (>$500K)

### Step 3: Future Outlook Allocation

Per well, per category:

```
Total In System = (ITD + Accrual) × Actual WI%
Future Outlook  = Ops Budget - Total In System
```

Allocation logic by category:
- **Drilling:** Linear by day (spud → TD)
- **Completions:** Linear by day (frac start → frac end)
- **Flowback:** Linear by day (flowback start → end)
- **Hookup:** Lump sum (100% in hookup month)

**Exceptions flagged:**
- Outlook > 40% of ops budget remaining (behind schedule?)
- Negative outlook (over budget)

## Agent Tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | `load_wbs_master` | Load WBS master, optional BU filter |
| 2 | `calculate_accruals` | Step 1: gross & net accruals per well per category |
| 3 | `calculate_net_down` | Step 2: WI% discrepancy, net-down adjustments |
| 4 | `calculate_outlook` | Step 3: future outlook per category with time allocation |
| 5 | `get_exceptions` | All exceptions across all 3 steps |
| 6 | `get_well_detail` | Single-well drilldown: full waterfall |
| 7 | `generate_journal_entry` | Net-down + accrual as GL journal entry |
| 8 | `get_close_summary` | Final summary: totals by BU |
| 9 | `generate_outlook_load_file` | Monthly grid (well × category × month) for OneStream |

## Key Outputs

1. **Accrual summary** — gross and net accruals per well with exceptions
2. **Net-down adjustment report** — WI% discrepancies with dollar impact
3. **Future outlook summary** — remaining spend per well per category
4. **Monthly outlook load file** — well × cost category × month grid, OneStream-ready
5. **Journal entry** — GL debit/credit for posting
6. **Excel close package** — downloadable workbook with all of the above

### Monthly Outlook Load File Format

```
well_name | wbs_element | cost_category | Feb-26 | Mar-26 | Apr-26 | May-26 | ...
Smith 1H  | WBS-1001    | Drilling      | 275,000| 275,000| 275,000| 275,000|
Smith 1H  | WBS-1001    | Completions   |      0 |      0 | 450,000| 450,000|
Smith 1H  | WBS-1001    | Flowback      |      0 |      0 |      0 | 120,000|
Smith 1H  | WBS-1001    | Hookup        |      0 |      0 |      0 |      0 |
```

## Exception Wells (Hardcoded for Demo)

- **2-3 wells with WI% mismatch** — system_wi_pct != wi_pct, including 1 large gap (e.g., system=85%, actual=60%)
- **1 negative accrual well** — ITD > VOW in at least one category
- **1 large swing well** — >25% change vs prior period
- **1 over-budget well** — total in system exceeds ops budget (negative outlook)
- **Most wells (~12-15):** clean data, matching WI%, normal accruals

## Demo Script

1. User: *"Run the monthly close for Permian Basin"*
2. Agent loads WBS master → runs Step 1 → presents accrual table, flags exceptions
3. Agent runs Step 2 → *"I found 3 wells with WI% discrepancies. Smith 1H has system WI at 85% but should be 60%, creating a $1.2M net-down."*
4. Agent runs Step 3 → presents future outlook, flags over-budget well
5. Agent presents close summary with journal entry
6. Agent generates monthly outlook load file → *"Here's the outlook ready for OneStream"*
7. User downloads Excel close package
