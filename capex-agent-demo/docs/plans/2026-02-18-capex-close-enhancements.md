# Capex Close Enhancements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the capex agent demo with net accruals (WI%), net-down WI% adjustments, future outlook allocation, and a OneStream-ready monthly load file — demonstrating a complete monthly close process.

**Architecture:** Rebuild the data foundation around a single wide-table WBS master (~18 wells) with per-category columns (drill/comp/fb/hu) for budget, ITD, VOW, and ops budget, plus WI% fields. Build 9 agent tools that implement a 3-step close: (1) gross/net accruals, (2) WI% net-down adjustments, (3) future outlook allocation with monthly grid output. Wire into Claude API orchestrator and Streamlit UI.

**Tech Stack:** Python 3.11+, pandas, pytest, anthropic SDK, streamlit, openpyxl

**Design Doc:** `docs/plans/2026-02-18-capex-close-enhancements-design.md`

---

## Task 1: Write Failing Tests for Revised WBS Master Schema

**Files:**
- Create: `capex-agent-demo/tests/test_data_v2.py`
- Reference: `capex-agent-demo/data/wbs_master.csv` (will be regenerated)

**Step 1: Write the failing tests**

```python
"""Tests for revised wide-table WBS master with per-category columns and WI%."""

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WBS_MASTER_PATH = DATA_DIR / "wbs_master.csv"
DRILL_SCHEDULE_PATH = DATA_DIR / "drill_schedule.csv"

COST_CATEGORIES = ["drill", "comp", "fb", "hu"]

# Exception wells
WI_MISMATCH_WELLS = {"WBS-1003", "WBS-1007", "WBS-1011"}
LARGE_WI_GAP_WELL = "WBS-1007"  # system=85%, actual=60%
NEGATIVE_ACCRUAL_WELL = "WBS-1005"
LARGE_SWING_WELL = "WBS-1009"
OVER_BUDGET_WELL = "WBS-1015"


@pytest.fixture(scope="session")
def wbs_master() -> pd.DataFrame:
    return pd.read_csv(WBS_MASTER_PATH)


@pytest.fixture(scope="session")
def drill_schedule() -> pd.DataFrame:
    return pd.read_csv(DRILL_SCHEDULE_PATH, parse_dates=["planned_date"])


class TestWbsMasterSchema:
    """Verify the wide-table WBS master has all required columns."""

    CORE_COLUMNS = [
        "wbs_element", "well_name", "afe_number", "business_unit",
        "status", "start_date",
    ]
    WI_COLUMNS = ["wi_pct", "system_wi_pct"]
    PRIOR_COLUMNS = ["prior_gross_accrual"]

    def test_core_columns_present(self, wbs_master):
        for col in self.CORE_COLUMNS:
            assert col in wbs_master.columns, f"Missing column: {col}"

    def test_wi_columns_present(self, wbs_master):
        for col in self.WI_COLUMNS:
            assert col in wbs_master.columns, f"Missing column: {col}"

    def test_per_category_columns_present(self, wbs_master):
        for cat in COST_CATEGORIES:
            for suffix in ["_budget", "_itd", "_vow", "_ops_budget"]:
                col = f"{cat}{suffix}"
                assert col in wbs_master.columns, f"Missing column: {col}"

    def test_prior_gross_accrual_present(self, wbs_master):
        assert "prior_gross_accrual" in wbs_master.columns

    def test_row_count(self, wbs_master):
        assert 15 <= len(wbs_master) <= 20, f"Expected 15-20 rows, got {len(wbs_master)}"

    def test_wbs_element_uniqueness(self, wbs_master):
        assert wbs_master["wbs_element"].is_unique


class TestWorkingInterest:
    """Verify WI% fields and exception wells."""

    def test_wi_pct_range(self, wbs_master):
        assert (wbs_master["wi_pct"] > 0).all()
        assert (wbs_master["wi_pct"] <= 1.0).all()

    def test_system_wi_pct_range(self, wbs_master):
        assert (wbs_master["system_wi_pct"] > 0).all()
        assert (wbs_master["system_wi_pct"] <= 1.0).all()

    def test_wi_mismatch_wells_exist(self, wbs_master):
        for wbs in WI_MISMATCH_WELLS:
            row = wbs_master[wbs_master["wbs_element"] == wbs]
            assert len(row) == 1, f"{wbs} not found"
            assert row.iloc[0]["wi_pct"] != row.iloc[0]["system_wi_pct"], (
                f"{wbs} should have WI% mismatch"
            )

    def test_large_wi_gap(self, wbs_master):
        row = wbs_master[wbs_master["wbs_element"] == LARGE_WI_GAP_WELL].iloc[0]
        gap = abs(row["system_wi_pct"] - row["wi_pct"])
        assert gap >= 0.20, f"Expected large WI% gap (>=20pp), got {gap:.0%}"

    def test_most_wells_have_matching_wi(self, wbs_master):
        matching = wbs_master[wbs_master["wi_pct"] == wbs_master["system_wi_pct"]]
        assert len(matching) >= len(wbs_master) - 4, (
            "Most wells should have matching WI%"
        )


class TestPerCategoryData:
    """Verify per-category financial data is reasonable."""

    def test_itd_non_negative(self, wbs_master):
        for cat in COST_CATEGORIES:
            col = f"{cat}_itd"
            assert (wbs_master[col] >= 0).all(), f"Negative {col} found"

    def test_vow_non_negative(self, wbs_master):
        for cat in COST_CATEGORIES:
            col = f"{cat}_vow"
            assert (wbs_master[col] >= 0).all(), f"Negative {col} found"

    def test_budget_non_negative(self, wbs_master):
        for cat in COST_CATEGORIES:
            col = f"{cat}_budget"
            assert (wbs_master[col] >= 0).all(), f"Negative {col} found"

    def test_ops_budget_non_negative(self, wbs_master):
        for cat in COST_CATEGORIES:
            col = f"{cat}_ops_budget"
            assert (wbs_master[col] >= 0).all(), f"Negative {col} found"

    def test_negative_accrual_well(self, wbs_master):
        """At least one category on the negative accrual well has ITD > VOW."""
        row = wbs_master[wbs_master["wbs_element"] == NEGATIVE_ACCRUAL_WELL].iloc[0]
        has_negative = False
        for cat in COST_CATEGORIES:
            if row[f"{cat}_itd"] > row[f"{cat}_vow"]:
                has_negative = True
                break
        assert has_negative, f"{NEGATIVE_ACCRUAL_WELL} should have ITD > VOW in at least one category"


class TestLargeSwing:
    """Verify large swing exception well."""

    def test_large_swing_well_exists(self, wbs_master):
        row = wbs_master[wbs_master["wbs_element"] == LARGE_SWING_WELL].iloc[0]
        total_vow = sum(row[f"{cat}_vow"] for cat in COST_CATEGORIES)
        total_itd = sum(row[f"{cat}_itd"] for cat in COST_CATEGORIES)
        current_accrual = total_vow - total_itd
        prior = row["prior_gross_accrual"]
        assert prior > 0, "Prior accrual must be > 0 for swing calc"
        swing = abs(current_accrual - prior) / prior
        assert swing > 0.25, f"Expected >25% swing, got {swing:.0%}"


class TestOverBudget:
    """Verify over-budget exception well."""

    def test_over_budget_well(self, wbs_master):
        row = wbs_master[wbs_master["wbs_element"] == OVER_BUDGET_WELL].iloc[0]
        for cat in COST_CATEGORIES:
            total_in_system = row[f"{cat}_itd"] + (row[f"{cat}_vow"] - row[f"{cat}_itd"])
            ops = row[f"{cat}_ops_budget"]
            # At least one category should be over budget
        total_system = sum(row[f"{cat}_vow"] for cat in COST_CATEGORIES)
        total_ops = sum(row[f"{cat}_ops_budget"] for cat in COST_CATEGORIES)
        assert total_system > total_ops, (
            f"{OVER_BUDGET_WELL} total VOW should exceed total ops budget"
        )


class TestDrillSchedule:
    """Verify drill schedule still works with the new well set."""

    PHASE_ORDER = ["Spud", "TD", "Frac Start", "Frac End", "First Production"]

    def test_drill_schedule_references_master(self, wbs_master, drill_schedule):
        master_wbs = set(wbs_master["wbs_element"])
        drill_wbs = set(drill_schedule["wbs_element"])
        orphans = drill_wbs - master_wbs
        assert orphans == set(), f"Orphan WBS in drill_schedule: {orphans}"

    def test_dates_sequential(self, drill_schedule):
        phase_rank = {p: i for i, p in enumerate(self.PHASE_ORDER)}
        df = drill_schedule.copy()
        df["phase_rank"] = df["planned_phase"].map(phase_rank)
        for wbs, group in df.groupby("wbs_element"):
            g = group.sort_values("phase_rank")
            dates = g["planned_date"].tolist()
            for i in range(1, len(dates)):
                assert dates[i] > dates[i - 1], f"{wbs}: dates not sequential"

    def test_all_phases_present(self, drill_schedule):
        actual = set(drill_schedule["planned_phase"].unique())
        expected = set(self.PHASE_ORDER)
        assert actual == expected, f"Missing phases: {expected - actual}"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting/capex-agent-demo && python -m pytest tests/test_data_v2.py -v --tb=short 2>&1 | head -60`
Expected: FAIL — the current wbs_master.csv doesn't have the new columns

**Step 3: Commit**

```bash
git add tests/test_data_v2.py
git commit -m "test: add failing tests for revised wide-table WBS master schema"
```

---

## Task 2: Rewrite Data Generator for Wide-Table WBS Master

**Files:**
- Modify: `capex-agent-demo/data/generate_synthetic_data.py`
- Output: `capex-agent-demo/data/wbs_master.csv` (regenerated, ~18 rows)
- Output: `capex-agent-demo/data/drill_schedule.csv` (regenerated, matching new wells)
- Delete (no longer needed): `capex-agent-demo/data/itd_extract.csv`, `capex-agent-demo/data/vow_estimates.csv`, `capex-agent-demo/data/prior_period_accruals.csv`

**Step 1: Rewrite generate_synthetic_data.py**

Replace the entire generator. Key design decisions:
- 18 wells (WBS-1001 through WBS-1018)
- ~12 Permian Basin, ~4 DJ Basin, ~2 Powder River
- WI% defaults: most wells at matching wi_pct == system_wi_pct (e.g., 0.75)
- Exception wells hardcoded per design doc

The generator must produce:

**WBS Master columns:**
```
wbs_element, well_name, afe_number, business_unit, status, start_date,
wi_pct, system_wi_pct,
drill_budget, drill_itd, drill_vow, drill_ops_budget,
comp_budget, comp_itd, comp_vow, comp_ops_budget,
fb_budget, fb_itd, fb_vow, fb_ops_budget,
hu_budget, hu_itd, hu_vow, hu_ops_budget,
prior_gross_accrual
```

**Exception well wiring:**

| Well | Exception | Values |
|------|-----------|--------|
| WBS-1003 | WI% mismatch (moderate) | wi_pct=0.75, system_wi_pct=0.80 |
| WBS-1007 | WI% mismatch (large gap) | wi_pct=0.60, system_wi_pct=0.85 |
| WBS-1011 | WI% mismatch (small) | wi_pct=0.65, system_wi_pct=0.70 |
| WBS-1005 | Negative accrual | drill_itd > drill_vow (ITD=3.2M, VOW=2.8M) |
| WBS-1009 | Large swing | total current accrual ~$1.07M vs prior ~$800K (+34%) |
| WBS-1015 | Over budget | total VOW exceeds total ops_budget |

**Normal well generation logic:**
- For each category, budget = random $1M-$5M
- ops_budget = budget * random(0.95, 1.10) (ops estimate close to AFE budget)
- itd = budget * random(0.20, 0.70) (20-70% spent)
- vow = itd + random($50K, $500K) (positive accrual)
- prior_gross_accrual = sum(vow - itd across categories) * random(0.90, 1.10)

**Step 2: Run the generator**

Run: `cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting/capex-agent-demo && python data/generate_synthetic_data.py`
Expected: "All CSV files generated successfully!"

**Step 3: Run tests to verify they pass**

Run: `cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting/capex-agent-demo && python -m pytest tests/test_data_v2.py -v`
Expected: All PASS

**Step 4: Delete old test file and obsolete CSVs**

The old `tests/test_data.py` and the separate CSV files (`itd_extract.csv`, `vow_estimates.csv`, `prior_period_accruals.csv`) are no longer needed. Delete them.

**Step 5: Commit**

```bash
git add data/generate_synthetic_data.py data/wbs_master.csv data/drill_schedule.csv tests/test_data_v2.py
git rm data/itd_extract.csv data/vow_estimates.csv data/prior_period_accruals.csv tests/test_data.py
git commit -m "feat: rebuild data foundation with wide-table WBS master (WI%, per-category columns)"
```

---

## Task 3: Update Data Loader

**Files:**
- Modify: `capex-agent-demo/utils/data_loader.py`
- Test: `capex-agent-demo/tests/test_data_v2.py` (add loader tests)

**Step 1: Add loader tests to test_data_v2.py**

Append to `tests/test_data_v2.py`:

```python
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_wbs_master, load_drill_schedule


class TestDataLoader:
    def test_load_wbs_master_all(self):
        df = load_wbs_master()
        assert 15 <= len(df) <= 20
        assert "wi_pct" in df.columns
        assert "drill_budget" in df.columns

    def test_load_wbs_master_permian(self):
        df = load_wbs_master("Permian Basin")
        assert len(df) >= 10
        assert (df["business_unit"] == "Permian Basin").all()

    def test_load_wbs_master_invalid_bu(self):
        df = load_wbs_master("NonExistent Basin")
        assert len(df) == 0

    def test_load_drill_schedule(self):
        df = load_drill_schedule()
        assert "planned_date" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["planned_date"])
```

**Step 2: Run tests to verify loader tests fail**

Run: `python -m pytest tests/test_data_v2.py::TestDataLoader -v`
Expected: FAIL (loader still has old functions like load_itd, load_vow)

**Step 3: Update data_loader.py**

Simplify to two functions: `load_wbs_master()` and `load_drill_schedule()`. Remove `load_itd()`, `load_vow()`, `load_prior_accruals()`.

```python
"""Data Loader for CapEx Close Agent Demo.

Two data sources:
- wbs_master.csv: Wide table with all financial data per well
- drill_schedule.csv: Phase dates for time-based outlook allocation
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_wbs_master(business_unit: str = "all") -> pd.DataFrame:
    """Load WBS Master, optionally filtered by business unit."""
    df = pd.read_csv(DATA_DIR / "wbs_master.csv")
    if business_unit != "all":
        df = df[df["business_unit"] == business_unit]
    return df


def load_drill_schedule() -> pd.DataFrame:
    """Load drill/frac schedule with parsed dates."""
    return pd.read_csv(
        DATA_DIR / "drill_schedule.csv",
        parse_dates=["planned_date"],
    )
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_data_v2.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add utils/data_loader.py tests/test_data_v2.py
git commit -m "refactor: simplify data loader for wide-table WBS master"
```

---

## Task 4: Build Step 1 Tool — calculate_accruals

**Files:**
- Create: `capex-agent-demo/agent/tools.py`
- Create: `capex-agent-demo/tests/test_tools.py`

**Step 1: Write failing tests for calculate_accruals**

```python
"""Tests for agent tools — the 3-step close calculation chain."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.tools import calculate_accruals

COST_CATEGORIES = ["drill", "comp", "fb", "hu"]


class TestCalculateAccruals:
    """Step 1: Gross and net accrual calculation."""

    def test_returns_dict_with_required_keys(self):
        result = calculate_accruals()
        assert "accruals" in result
        assert "summary" in result
        assert "exceptions" in result

    def test_accrual_record_has_required_fields(self):
        result = calculate_accruals()
        record = result["accruals"][0]
        for field in ["wbs_element", "well_name", "total_gross_accrual",
                       "total_net_accrual", "wi_pct"]:
            assert field in record, f"Missing field: {field}"

    def test_accrual_record_has_per_category_fields(self):
        result = calculate_accruals()
        record = result["accruals"][0]
        for cat in COST_CATEGORIES:
            assert f"{cat}_gross_accrual" in record
            assert f"{cat}_net_accrual" in record

    def test_gross_accrual_equals_vow_minus_itd(self):
        result = calculate_accruals()
        for rec in result["accruals"]:
            # Verify at least total is consistent
            assert isinstance(rec["total_gross_accrual"], (int, float))

    def test_net_accrual_equals_gross_times_wi(self):
        result = calculate_accruals()
        for rec in result["accruals"]:
            expected_net = rec["total_gross_accrual"] * rec["wi_pct"]
            assert abs(rec["total_net_accrual"] - expected_net) < 1.0, (
                f"Net accrual mismatch for {rec['wbs_element']}"
            )

    def test_negative_accrual_exception_detected(self):
        result = calculate_accruals()
        neg_exceptions = [e for e in result["exceptions"]
                          if e["exception_type"] == "Negative Accrual"]
        assert len(neg_exceptions) >= 1

    def test_large_swing_exception_detected(self):
        result = calculate_accruals()
        swing_exceptions = [e for e in result["exceptions"]
                            if e["exception_type"] == "Large Swing"]
        assert len(swing_exceptions) >= 1

    def test_summary_totals(self):
        result = calculate_accruals()
        summary = result["summary"]
        assert "total_gross_accrual" in summary
        assert "total_net_accrual" in summary
        assert "well_count" in summary
        assert "exception_count" in summary

    def test_business_unit_filter(self):
        result = calculate_accruals(business_unit="Permian Basin")
        for rec in result["accruals"]:
            assert rec["business_unit"] == "Permian Basin"
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tools.py::TestCalculateAccruals -v --tb=short`
Expected: FAIL — agent/tools.py doesn't exist yet

**Step 3: Implement calculate_accruals in agent/tools.py**

```python
"""Agent tools for the 3-step capex close process."""

from utils.data_loader import load_wbs_master, load_drill_schedule

COST_CATEGORIES = ["drill", "comp", "fb", "hu"]


def calculate_accruals(business_unit: str = "all") -> dict:
    """Step 1: Calculate gross and net accruals per well per category.

    Gross Accrual = VOW - ITD (per category)
    Net Accrual = Gross Accrual * WI%

    Returns dict with accruals (list), summary (dict), exceptions (list).
    """
    df = load_wbs_master(business_unit)
    accruals = []
    exceptions = []

    for _, row in df.iterrows():
        rec = {
            "wbs_element": row["wbs_element"],
            "well_name": row["well_name"],
            "business_unit": row["business_unit"],
            "wi_pct": row["wi_pct"],
        }

        total_gross = 0
        total_net = 0

        for cat in COST_CATEGORIES:
            vow = row[f"{cat}_vow"]
            itd = row[f"{cat}_itd"]
            gross = vow - itd
            net = gross * row["wi_pct"]
            rec[f"{cat}_gross_accrual"] = gross
            rec[f"{cat}_net_accrual"] = net
            total_gross += gross
            total_net += net

        rec["total_gross_accrual"] = total_gross
        rec["total_net_accrual"] = total_net
        rec["prior_gross_accrual"] = row["prior_gross_accrual"]
        accruals.append(rec)

        # Exception detection
        if total_gross < 0:
            exceptions.append({
                "wbs_element": row["wbs_element"],
                "well_name": row["well_name"],
                "exception_type": "Negative Accrual",
                "severity": "HIGH",
                "detail": f"Total gross accrual is negative: ${total_gross:,.0f}",
            })

        prior = row["prior_gross_accrual"]
        if prior > 0:
            swing = abs(total_gross - prior) / prior
            if swing > 0.25:
                exceptions.append({
                    "wbs_element": row["wbs_element"],
                    "well_name": row["well_name"],
                    "exception_type": "Large Swing",
                    "severity": "MEDIUM",
                    "detail": f"Swing of {swing:.0%} vs prior (current=${total_gross:,.0f}, prior=${prior:,.0f})",
                })

    summary = {
        "total_gross_accrual": sum(r["total_gross_accrual"] for r in accruals),
        "total_net_accrual": sum(r["total_net_accrual"] for r in accruals),
        "well_count": len(accruals),
        "exception_count": len(exceptions),
    }

    return {"accruals": accruals, "summary": summary, "exceptions": exceptions}
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_tools.py::TestCalculateAccruals -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement calculate_accruals (Step 1 - gross & net accruals)"
```

---

## Task 5: Build Step 2 Tool — calculate_net_down

**Files:**
- Modify: `capex-agent-demo/agent/tools.py`
- Modify: `capex-agent-demo/tests/test_tools.py`

**Step 1: Write failing tests**

Add to `tests/test_tools.py`:

```python
from agent.tools import calculate_net_down


class TestCalculateNetDown:
    """Step 2: WI% net-down adjustment."""

    def test_returns_dict_with_required_keys(self):
        result = calculate_net_down()
        assert "adjustments" in result
        assert "summary" in result

    def test_adjustment_record_fields(self):
        result = calculate_net_down()
        if result["adjustments"]:
            rec = result["adjustments"][0]
            for field in ["wbs_element", "total_system_cost", "system_wi_pct",
                           "actual_wi_pct", "wi_discrepancy", "net_down_adjustment",
                           "adjusted_net_cost"]:
                assert field in rec, f"Missing field: {field}"

    def test_only_mismatched_wells_have_adjustments(self):
        result = calculate_net_down()
        for adj in result["adjustments"]:
            assert adj["system_wi_pct"] != adj["actual_wi_pct"], (
                f"{adj['wbs_element']} has no WI% mismatch but got adjustment"
            )

    def test_net_down_formula(self):
        result = calculate_net_down()
        for adj in result["adjustments"]:
            expected = adj["total_system_cost"] * (adj["system_wi_pct"] - adj["actual_wi_pct"])
            assert abs(adj["net_down_adjustment"] - expected) < 1.0

    def test_adjusted_net_cost_formula(self):
        result = calculate_net_down()
        for adj in result["adjustments"]:
            expected = adj["total_system_cost"] * adj["actual_wi_pct"]
            assert abs(adj["adjusted_net_cost"] - expected) < 1.0

    def test_large_wi_gap_produces_large_adjustment(self):
        result = calculate_net_down()
        large = [a for a in result["adjustments"]
                 if a["wbs_element"] == "WBS-1007"]
        assert len(large) == 1
        assert abs(large[0]["net_down_adjustment"]) > 500_000

    def test_summary_total_adjustment(self):
        result = calculate_net_down()
        expected_total = sum(a["net_down_adjustment"] for a in result["adjustments"])
        assert abs(result["summary"]["total_net_down_adjustment"] - expected_total) < 1.0
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tools.py::TestCalculateNetDown -v --tb=short`
Expected: FAIL

**Step 3: Implement calculate_net_down**

Add to `agent/tools.py`:

```python
def calculate_net_down(business_unit: str = "all") -> dict:
    """Step 2: Calculate WI% net-down adjustments.

    For wells where system_wi_pct != wi_pct:
    Net-Down Adjustment = Total System Cost * (System WI% - Actual WI%)
    Adjusted Net Cost = Total System Cost * Actual WI%
    """
    df = load_wbs_master(business_unit)
    adjustments = []

    for _, row in df.iterrows():
        if row["system_wi_pct"] == row["wi_pct"]:
            continue

        total_system_cost = 0
        for cat in COST_CATEGORIES:
            itd = row[f"{cat}_itd"]
            gross_accrual = row[f"{cat}_vow"] - row[f"{cat}_itd"]
            total_system_cost += itd + gross_accrual  # = vow for each category

        discrepancy = row["system_wi_pct"] - row["wi_pct"]
        adjustment = total_system_cost * discrepancy
        adjusted_net = total_system_cost * row["wi_pct"]

        adjustments.append({
            "wbs_element": row["wbs_element"],
            "well_name": row["well_name"],
            "total_system_cost": total_system_cost,
            "system_wi_pct": row["system_wi_pct"],
            "actual_wi_pct": row["wi_pct"],
            "wi_discrepancy": discrepancy,
            "net_down_adjustment": adjustment,
            "adjusted_net_cost": adjusted_net,
        })

    summary = {
        "wells_with_mismatch": len(adjustments),
        "total_net_down_adjustment": sum(a["net_down_adjustment"] for a in adjustments),
    }

    return {"adjustments": adjustments, "summary": summary}
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_tools.py::TestCalculateNetDown -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement calculate_net_down (Step 2 - WI% adjustments)"
```

---

## Task 6: Build Step 3 Tool — calculate_outlook

**Files:**
- Modify: `capex-agent-demo/agent/tools.py`
- Modify: `capex-agent-demo/tests/test_tools.py`

**Step 1: Write failing tests**

Add to `tests/test_tools.py`:

```python
from agent.tools import calculate_outlook


class TestCalculateOutlook:
    """Step 3: Future outlook allocation."""

    def test_returns_dict_with_required_keys(self):
        result = calculate_outlook()
        assert "outlook" in result
        assert "summary" in result
        assert "exceptions" in result

    def test_outlook_record_fields(self):
        result = calculate_outlook()
        if result["outlook"]:
            rec = result["outlook"][0]
            for field in ["wbs_element", "well_name"]:
                assert field in rec
            for cat in COST_CATEGORIES:
                assert f"{cat}_future_outlook" in rec

    def test_future_outlook_formula(self):
        """Future Outlook = Ops Budget - Total In System (after WI% adjustment)."""
        result = calculate_outlook()
        for rec in result["outlook"]:
            for cat in COST_CATEGORIES:
                # future = ops_budget - (vow * wi_pct)
                assert isinstance(rec[f"{cat}_future_outlook"], (int, float))

    def test_over_budget_exception_detected(self):
        result = calculate_outlook()
        over_budget = [e for e in result["exceptions"]
                       if e["exception_type"] == "Over Budget"]
        assert len(over_budget) >= 1

    def test_summary_totals(self):
        result = calculate_outlook()
        assert "total_future_outlook" in result["summary"]
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tools.py::TestCalculateOutlook -v --tb=short`
Expected: FAIL

**Step 3: Implement calculate_outlook**

Add to `agent/tools.py`:

```python
def calculate_outlook(business_unit: str = "all") -> dict:
    """Step 3: Calculate future outlook per well per category.

    Future Outlook = Ops Budget - (VOW * Actual WI%)
    Negative outlook = over budget.
    """
    df = load_wbs_master(business_unit)
    outlook = []
    exceptions = []

    for _, row in df.iterrows():
        rec = {
            "wbs_element": row["wbs_element"],
            "well_name": row["well_name"],
            "business_unit": row["business_unit"],
            "wi_pct": row["wi_pct"],
        }

        total_outlook = 0
        total_ops = 0

        for cat in COST_CATEGORIES:
            total_in_system = row[f"{cat}_vow"] * row["wi_pct"]
            ops = row[f"{cat}_ops_budget"]
            future = ops - total_in_system
            rec[f"{cat}_total_in_system"] = total_in_system
            rec[f"{cat}_ops_budget"] = ops
            rec[f"{cat}_future_outlook"] = future
            total_outlook += future
            total_ops += ops

        rec["total_future_outlook"] = total_outlook
        rec["total_ops_budget"] = total_ops
        outlook.append(rec)

        if total_outlook < 0:
            exceptions.append({
                "wbs_element": row["wbs_element"],
                "well_name": row["well_name"],
                "exception_type": "Over Budget",
                "severity": "HIGH",
                "detail": f"Total in system exceeds ops budget by ${abs(total_outlook):,.0f}",
            })

    summary = {
        "total_future_outlook": sum(r["total_future_outlook"] for r in outlook),
        "well_count": len(outlook),
        "over_budget_count": len(exceptions),
    }

    return {"outlook": outlook, "summary": summary, "exceptions": exceptions}
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_tools.py::TestCalculateOutlook -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement calculate_outlook (Step 3 - future outlook)"
```

---

## Task 7: Build OneStream Load File Generator

**Files:**
- Modify: `capex-agent-demo/agent/tools.py`
- Modify: `capex-agent-demo/tests/test_tools.py`

**Step 1: Write failing tests**

Add to `tests/test_tools.py`:

```python
from agent.tools import generate_outlook_load_file


class TestGenerateOutlookLoadFile:
    """Monthly outlook grid for OneStream."""

    def test_returns_dataframe(self):
        result = generate_outlook_load_file()
        assert "load_file" in result
        import pandas as pd
        assert isinstance(result["load_file"], pd.DataFrame)

    def test_columns_include_well_and_category(self):
        result = generate_outlook_load_file()
        df = result["load_file"]
        assert "well_name" in df.columns
        assert "wbs_element" in df.columns
        assert "cost_category" in df.columns

    def test_has_monthly_columns(self):
        result = generate_outlook_load_file()
        df = result["load_file"]
        month_cols = [c for c in df.columns if c not in
                      ["well_name", "wbs_element", "cost_category", "total"]]
        assert len(month_cols) >= 3, "Should have at least 3 monthly columns"

    def test_four_rows_per_well(self):
        result = generate_outlook_load_file()
        df = result["load_file"]
        for wbs in df["wbs_element"].unique():
            well_rows = df[df["wbs_element"] == wbs]
            assert len(well_rows) == 4, f"{wbs} should have 4 rows (one per category)"

    def test_category_values(self):
        result = generate_outlook_load_file()
        df = result["load_file"]
        expected = {"Drilling", "Completions", "Flowback", "Hookup"}
        actual = set(df["cost_category"].unique())
        assert actual == expected

    def test_monthly_values_sum_to_total(self):
        result = generate_outlook_load_file()
        df = result["load_file"]
        month_cols = [c for c in df.columns if c not in
                      ["well_name", "wbs_element", "cost_category", "total"]]
        for _, row in df.iterrows():
            row_sum = sum(row[c] for c in month_cols)
            assert abs(row_sum - row["total"]) < 1.0, (
                f"Monthly values don't sum to total for {row['wbs_element']} {row['cost_category']}"
            )
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tools.py::TestGenerateOutlookLoadFile -v --tb=short`
Expected: FAIL

**Step 3: Implement generate_outlook_load_file**

Add to `agent/tools.py`:

```python
import pandas as pd
from datetime import date, timedelta


# At module level
CATEGORY_LABELS = {
    "drill": "Drilling",
    "comp": "Completions",
    "fb": "Flowback",
    "hu": "Hookup",
}

CATEGORY_ALLOCATION = {
    "drill": "linear",     # Linear by day (Spud -> TD)
    "comp": "linear",      # Linear by day (Frac Start -> Frac End)
    "fb": "linear",        # Linear by day (Flowback period)
    "hu": "lump_sum",      # 100% in hookup month
}

CATEGORY_PHASE_MAP = {
    "drill": ("Spud", "TD"),
    "comp": ("Frac Start", "Frac End"),
    "fb": ("Frac End", "First Production"),
    "hu": ("First Production", "First Production"),
}

# Reference date for the demo (hardcoded per PRD)
REFERENCE_DATE = date(2026, 1, 1)


def _get_months_forward(n_months: int = 6) -> list[str]:
    """Generate month labels like 'Feb-26', 'Mar-26', etc."""
    months = []
    d = REFERENCE_DATE.replace(day=1)
    for i in range(n_months):
        month_offset = d.month + i
        year = d.year + (month_offset - 1) // 12
        month = ((month_offset - 1) % 12) + 1
        label = date(year, month, 1).strftime("%b-%y")
        months.append(label)
    return months


def _allocate_linear(total: float, start_date, end_date, months: list[str]) -> dict:
    """Allocate total linearly by day across months."""
    if total <= 0 or start_date >= end_date:
        return {m: 0.0 for m in months}

    total_days = (end_date - start_date).days + 1
    daily_rate = total / total_days
    allocation = {m: 0.0 for m in months}

    for m_label in months:
        # Parse month label back to date range
        m_date = pd.to_datetime(f"01-{m_label}", format="%d-%b-%y")
        m_start = m_date.date()
        if m_date.month == 12:
            m_end = date(m_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(m_date.year, m_date.month + 1, 1) - timedelta(days=1)

        # Overlap between phase and month
        overlap_start = max(start_date, m_start)
        overlap_end = min(end_date, m_end)
        if overlap_start <= overlap_end:
            days_in_month = (overlap_end - overlap_start).days + 1
            allocation[m_label] = round(daily_rate * days_in_month, 2)

    return allocation


def _allocate_lump_sum(total: float, target_date, months: list[str]) -> dict:
    """Allocate 100% to the month containing target_date."""
    allocation = {m: 0.0 for m in months}
    for m_label in months:
        m_date = pd.to_datetime(f"01-{m_label}", format="%d-%b-%y")
        if m_date.month == target_date.month and m_date.year == target_date.year:
            allocation[m_label] = round(total, 2)
            break
    return allocation


def generate_outlook_load_file(
    business_unit: str = "all",
    months_forward: int = 6,
) -> dict:
    """Generate monthly outlook grid (well x category x month) for OneStream.

    Allocation logic:
    - Drilling: linear by day (Spud -> TD)
    - Completions: linear by day (Frac Start -> Frac End)
    - Flowback: linear by day (Frac End -> First Production)
    - Hookup: lump sum (100% in First Production month)
    """
    wbs_df = load_wbs_master(business_unit)
    sched_df = load_drill_schedule()
    months = _get_months_forward(months_forward)

    # Build schedule lookup: {wbs_element: {phase: date}}
    sched_lookup = {}
    for _, sr in sched_df.iterrows():
        wbs = sr["wbs_element"]
        if wbs not in sched_lookup:
            sched_lookup[wbs] = {}
        sched_lookup[wbs][sr["planned_phase"]] = sr["planned_date"].date() if hasattr(sr["planned_date"], 'date') else sr["planned_date"]

    rows = []
    for _, row in wbs_df.iterrows():
        wbs = row["wbs_element"]
        phases = sched_lookup.get(wbs, {})

        for cat in COST_CATEGORIES:
            total_in_system = row[f"{cat}_vow"] * row["wi_pct"]
            ops_budget = row[f"{cat}_ops_budget"]
            future = ops_budget - total_in_system

            label = CATEGORY_LABELS[cat]
            alloc_type = CATEGORY_ALLOCATION[cat]
            start_phase, end_phase = CATEGORY_PHASE_MAP[cat]

            if future <= 0 or not phases:
                allocation = {m: 0.0 for m in months}
            elif alloc_type == "linear":
                s = phases.get(start_phase)
                e = phases.get(end_phase)
                if s and e:
                    allocation = _allocate_linear(future, s, e, months)
                else:
                    # No schedule data: spread evenly
                    per_month = round(future / len(months), 2)
                    allocation = {m: per_month for m in months}
            else:  # lump_sum
                target = phases.get(end_phase)
                if target:
                    allocation = _allocate_lump_sum(future, target, months)
                else:
                    allocation = {m: 0.0 for m in months}

            rec = {
                "well_name": row["well_name"],
                "wbs_element": wbs,
                "cost_category": label,
            }
            rec.update(allocation)
            rec["total"] = round(future if future > 0 else 0.0, 2)
            rows.append(rec)

    load_df = pd.DataFrame(rows)
    return {"load_file": load_df, "months": months}
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_tools.py::TestGenerateOutlookLoadFile -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement generate_outlook_load_file (OneStream monthly grid)"
```

---

## Task 8: Build Supporting Tools

**Files:**
- Modify: `capex-agent-demo/agent/tools.py`
- Modify: `capex-agent-demo/tests/test_tools.py`

**Step 1: Write failing tests for supporting tools**

Add to `tests/test_tools.py`:

```python
from agent.tools import (
    get_exceptions, get_well_detail, generate_journal_entry, get_close_summary,
)


class TestGetExceptions:
    def test_returns_all_exceptions(self):
        result = get_exceptions()
        assert "exceptions" in result
        assert len(result["exceptions"]) >= 3  # at least neg accrual + swing + over budget

    def test_filter_by_severity(self):
        result = get_exceptions(severity="HIGH")
        for exc in result["exceptions"]:
            assert exc["severity"] == "HIGH"


class TestGetWellDetail:
    def test_returns_full_waterfall(self):
        result = get_well_detail("WBS-1007")
        assert result["wbs_element"] == "WBS-1007"
        for key in ["total_gross_accrual", "total_net_accrual",
                      "net_down_adjustment", "total_in_system", "total_future_outlook"]:
            assert key in result, f"Missing: {key}"


class TestGenerateJournalEntry:
    def test_returns_journal_entry(self):
        result = generate_journal_entry()
        assert "journal_entry" in result
        je = result["journal_entry"]
        assert "debit_account" in je
        assert "credit_account" in je
        assert "net_down_amount" in je


class TestGetCloseSummary:
    def test_returns_summary_by_bu(self):
        result = get_close_summary()
        assert "by_business_unit" in result
        assert "grand_totals" in result
        totals = result["grand_totals"]
        for key in ["total_gross_accrual", "total_net_accrual",
                      "total_net_down_adjustment", "total_future_outlook"]:
            assert key in totals
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_tools.py -k "TestGetExceptions or TestGetWellDetail or TestGenerateJournalEntry or TestGetCloseSummary" -v --tb=short`
Expected: FAIL

**Step 3: Implement the four supporting tools**

Add to `agent/tools.py`:

```python
def get_exceptions(
    business_unit: str = "all",
    severity: str = "all",
) -> dict:
    """Get all exceptions from all 3 steps, optionally filtered by severity."""
    accrual_result = calculate_accruals(business_unit)
    net_down_result = calculate_net_down(business_unit)
    outlook_result = calculate_outlook(business_unit)

    all_exceptions = (
        accrual_result["exceptions"]
        + [{"wbs_element": a["wbs_element"], "well_name": a.get("well_name", ""),
            "exception_type": "WI% Mismatch", "severity": "MEDIUM",
            "detail": f"System WI={a['system_wi_pct']:.0%} vs Actual WI={a['actual_wi_pct']:.0%}, "
                      f"adjustment=${a['net_down_adjustment']:,.0f}"}
           for a in net_down_result["adjustments"]]
        + outlook_result["exceptions"]
    )

    if severity != "all":
        all_exceptions = [e for e in all_exceptions if e["severity"] == severity]

    return {
        "exceptions": all_exceptions,
        "count": len(all_exceptions),
        "by_severity": _count_by(all_exceptions, "severity"),
        "by_type": _count_by(all_exceptions, "exception_type"),
    }


def _count_by(items: list[dict], key: str) -> dict:
    counts = {}
    for item in items:
        v = item.get(key, "Unknown")
        counts[v] = counts.get(v, 0) + 1
    return counts


def get_well_detail(wbs_element: str) -> dict:
    """Full waterfall detail for a single well: accrual -> net-down -> outlook."""
    wbs_df = load_wbs_master()
    row = wbs_df[wbs_df["wbs_element"] == wbs_element]
    if row.empty:
        return {"error": f"WBS element {wbs_element} not found"}
    row = row.iloc[0]

    detail = {
        "wbs_element": row["wbs_element"],
        "well_name": row["well_name"],
        "business_unit": row["business_unit"],
        "status": row["status"],
        "wi_pct": row["wi_pct"],
        "system_wi_pct": row["system_wi_pct"],
    }

    total_gross = 0
    total_net = 0
    total_system_cost = 0
    total_future = 0

    for cat in COST_CATEGORIES:
        vow = row[f"{cat}_vow"]
        itd = row[f"{cat}_itd"]
        gross = vow - itd
        net = gross * row["wi_pct"]
        in_system = vow * row["wi_pct"]
        ops = row[f"{cat}_ops_budget"]
        future = ops - in_system

        detail[f"{cat}_itd"] = itd
        detail[f"{cat}_vow"] = vow
        detail[f"{cat}_gross_accrual"] = gross
        detail[f"{cat}_net_accrual"] = net
        detail[f"{cat}_ops_budget"] = ops
        detail[f"{cat}_future_outlook"] = future

        total_gross += gross
        total_net += net
        total_system_cost += vow
        total_future += future

    wi_discrepancy = row["system_wi_pct"] - row["wi_pct"]
    net_down_adj = total_system_cost * wi_discrepancy

    detail["total_gross_accrual"] = total_gross
    detail["total_net_accrual"] = total_net
    detail["net_down_adjustment"] = net_down_adj
    detail["total_in_system"] = total_system_cost * row["wi_pct"]
    detail["total_future_outlook"] = total_future
    detail["prior_gross_accrual"] = row["prior_gross_accrual"]

    return detail


def generate_journal_entry(business_unit: str = "all") -> dict:
    """Generate the net-down + accrual journal entry for GL posting."""
    accrual_result = calculate_accruals(business_unit)
    net_down_result = calculate_net_down(business_unit)

    total_net_accrual = accrual_result["summary"]["total_net_accrual"]
    total_wi_adjustment = net_down_result["summary"]["total_net_down_adjustment"]
    net_down_amount = total_net_accrual - total_wi_adjustment

    journal_entry = {
        "period": "2026-01",
        "description": "Monthly CapEx Gross Accrual with WI% Net-Down",
        "debit_account": "1410-000 CapEx WIP",
        "credit_account": "2110-000 Accrued Liabilities",
        "total_net_accrual": total_net_accrual,
        "total_wi_adjustment": total_wi_adjustment,
        "net_down_amount": net_down_amount,
    }

    return {"journal_entry": journal_entry}


def get_close_summary(business_unit: str = "all") -> dict:
    """Final close summary with all totals, grouped by BU."""
    wbs_df = load_wbs_master()
    bus = wbs_df["business_unit"].unique()

    by_bu = {}
    for bu in bus:
        accruals = calculate_accruals(bu)
        net_down = calculate_net_down(bu)
        outlook = calculate_outlook(bu)

        by_bu[bu] = {
            "total_gross_accrual": accruals["summary"]["total_gross_accrual"],
            "total_net_accrual": accruals["summary"]["total_net_accrual"],
            "total_net_down_adjustment": net_down["summary"]["total_net_down_adjustment"],
            "total_future_outlook": outlook["summary"]["total_future_outlook"],
            "well_count": accruals["summary"]["well_count"],
            "exception_count": accruals["summary"]["exception_count"] + outlook["summary"]["over_budget_count"],
        }

    grand = {k: sum(v[k] for v in by_bu.values())
             for k in ["total_gross_accrual", "total_net_accrual",
                       "total_net_down_adjustment", "total_future_outlook",
                       "well_count", "exception_count"]}

    return {"by_business_unit": by_bu, "grand_totals": grand}
```

**Step 4: Run all tool tests**

Run: `python -m pytest tests/test_tools.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: implement supporting tools (exceptions, well detail, journal entry, close summary)"
```

---

## Task 9: Build Tool Definitions for Claude API

**Files:**
- Create: `capex-agent-demo/agent/tool_definitions.py`

**Step 1: Write tool definitions**

Create the Claude API tool schemas for all 9 tools. Each tool definition is a JSON-compatible dict with name, description, and input_schema.

The tools are:
1. `load_wbs_master` — loads master data
2. `calculate_accruals` — Step 1
3. `calculate_net_down` — Step 2
4. `calculate_outlook` — Step 3
5. `get_exceptions` — exception report
6. `get_well_detail` — single well drilldown
7. `generate_journal_entry` — GL journal entry
8. `get_close_summary` — summary by BU
9. `generate_outlook_load_file` — OneStream monthly grid

Each should have appropriate parameter schemas (business_unit, severity, wbs_element, months_forward).

**Step 2: Verify definitions are valid JSON schemas**

Write a quick test:
```python
class TestToolDefinitions:
    def test_all_definitions_valid(self):
        from agent.tool_definitions import TOOL_DEFINITIONS
        assert len(TOOL_DEFINITIONS) == 9
        for td in TOOL_DEFINITIONS:
            assert "name" in td
            assert "description" in td
            assert "input_schema" in td
```

**Step 3: Run tests**

Run: `python -m pytest tests/test_tools.py::TestToolDefinitions -v`
Expected: PASS

**Step 4: Commit**

```bash
git add agent/tool_definitions.py tests/test_tools.py
git commit -m "feat: add Claude API tool definitions for all 9 tools"
```

---

## Task 10: Build System Prompt

**Files:**
- Create: `capex-agent-demo/agent/prompts.py`

**Step 1: Write the system prompt**

Update the PRD system prompt (Section 7) to reflect the new 3-step close process, WI% calculations, and OneStream load file output. The prompt should instruct the agent to:

1. Load WBS master
2. Run Step 1 (accruals) — report gross and net
3. Run Step 2 (net-down) — identify WI% mismatches
4. Run Step 3 (outlook) — calculate remaining spend
5. Present close summary
6. Offer to generate OneStream load file

Keep the mandatory clarifying question about missing ITD (but adapt it: since all data is now in one file, the "wow moment" becomes the agent identifying WI% mismatches and asking about them).

**Step 2: Commit**

```bash
git add agent/prompts.py
git commit -m "feat: add system prompt for 3-step close workflow"
```

---

## Task 11: Build Agent Orchestrator

**Files:**
- Create: `capex-agent-demo/agent/orchestrator.py`
- Modify: `capex-agent-demo/agent/__init__.py`
- Modify: `capex-agent-demo/requirements.txt` (add anthropic, python-dotenv)

**Step 1: Implement orchestrator**

The orchestrator handles:
1. Sending system prompt + user message + tool definitions to Claude API
2. Processing `tool_use` content blocks by dispatching to the correct tool function
3. Returning `tool_result` messages back to Claude
4. Looping until Claude returns a final text response
5. Streaming support (yield events as they arrive)
6. Error handling (wrap tool dispatch in try/except)

Pattern:
```python
class AgentOrchestrator:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def run(self, messages: list[dict]) -> Generator[Event, None, None]:
        """Run the agent loop, yielding events for streaming."""
        ...
```

**Step 2: Test with CLI**

Run: `python cli.py` and verify the basic loop works.

**Step 3: Commit**

```bash
git add agent/orchestrator.py agent/__init__.py requirements.txt
git commit -m "feat: implement agent orchestrator with tool-use loop"
```

---

## Task 12: Build CLI

**Files:**
- Create: `capex-agent-demo/cli.py`
- Create: `capex-agent-demo/.env.example`

**Step 1: Implement CLI**

Simple stdin/stdout loop that:
1. Loads API key from .env
2. Accepts user input
3. Calls orchestrator
4. Prints streaming events and final response
5. Loops for follow-ups

**Step 2: Test the full demo flow**

Run: `python cli.py`
Test prompt: "Run the monthly close for Permian Basin"

Expected behavior:
1. Agent loads WBS master
2. Runs Step 1 — shows accrual summary
3. Runs Step 2 — identifies WI% mismatches
4. Runs Step 3 — shows outlook
5. Presents close summary

**Step 3: Commit**

```bash
git add cli.py .env.example
git commit -m "feat: add CLI for testing agent workflow"
```

---

## Task 13: Build Streamlit UI

**Files:**
- Create: `capex-agent-demo/app.py`
- Create: `capex-agent-demo/.streamlit/config.toml`
- Create: `capex-agent-demo/utils/excel_export.py`
- Modify: `capex-agent-demo/requirements.txt` (add streamlit)

**Step 1: Create dark theme config**

`.streamlit/config.toml` with dark theme, green accents.

**Step 2: Implement app.py**

Follow the PRD Section 8 layout:
- Header, sidebar (status, tools, data counts, reset)
- Chat interface with streaming breadcrumbs
- Metric cards for each step
- DataFrames for accrual tables
- Exception report in expander
- Monthly outlook grid display
- Download buttons (Excel close package + OneStream load file CSV)

Key adaptation from PRD: The "clarifying question" moment is now about WI% mismatches instead of missing ITD:
> "I found 3 wells where the Working Interest in the system doesn't match the actual WI%. The largest is WBS-1007 — system has 85% but should be 60%. Should I proceed with the net-down adjustments?"

**Step 3: Implement excel_export.py**

Generate a multi-sheet Excel workbook:
- Sheet 1: "Accrual Summary" — per-well accruals
- Sheet 2: "Net-Down Report" — WI% adjustments
- Sheet 3: "Outlook Summary" — future outlook per well
- Sheet 4: "OneStream Load" — monthly grid (the main wow output)
- Sheet 5: "Exception Report"

**Step 4: Test locally**

Run: `streamlit run app.py`
Walk through the full demo flow.

**Step 5: Commit**

```bash
git add app.py .streamlit/config.toml utils/excel_export.py requirements.txt
git commit -m "feat: add Streamlit UI with 3-step close workflow and OneStream output"
```

---

## Task 14: Polish and Demo-Ready

**Files:**
- All files (review and polish)

**Step 1: Run the full demo script 3+ times**

Test the exact prompt sequence:
1. "Run the monthly close for Permian Basin"
2. (Respond to clarifying question)
3. "Show me the WI% discrepancies"
4. "Generate the OneStream load file"
5. Download Excel

**Step 2: Fix any issues found during rehearsal**

Common issues to watch for:
- Formatting of dollar amounts
- Table readability on projected screens
- Streaming latency between steps
- Edge cases in allocation math

**Step 3: Deploy to Streamlit Cloud**

Set up secrets, verify cold start time.

**Step 4: Record backup video**

2-minute screen recording of successful demo flow.

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: polish and demo-ready"
```
