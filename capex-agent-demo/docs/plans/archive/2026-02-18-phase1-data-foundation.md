# Phase 1 — Data Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate 5 synthetic CSV files with hardcoded exception triggers, build data-loading utilities, and validate everything with pytest.

**Architecture:** A single deterministic generator script produces all CSVs. Exception-triggering records are hardcoded; remaining records use seeded randomness. A data_loader module provides typed functions to read each CSV. Tests validate all 12 PRD acceptance criteria.

**Tech Stack:** Python 3.11+, pandas, openpyxl, pytest

**PRD Reference:** `planning/prd.md` Sections 4.1–4.6

---

## Task 1: Project Scaffolding

**Files:**
- Create: `capex-agent-demo/requirements.txt`
- Create: `capex-agent-demo/data/.gitkeep` (placeholder)
- Create: `capex-agent-demo/utils/__init__.py`
- Create: `capex-agent-demo/tests/__init__.py`
- Create: `capex-agent-demo/agent/__init__.py`

**Step 1: Create directory structure**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
mkdir -p capex-agent-demo/{data,utils,tests,agent}
touch capex-agent-demo/utils/__init__.py
touch capex-agent-demo/tests/__init__.py
touch capex-agent-demo/agent/__init__.py
```

**Step 2: Create requirements.txt**

```
# capex-agent-demo/requirements.txt
pandas>=2.0.0
openpyxl>=3.1.0
pytest>=7.0.0
```

**Step 3: Install dependencies**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting/capex-agent-demo
pip install -r requirements.txt
```

**Step 4: Initialize git and commit**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
git init
git add capex-agent-demo/requirements.txt capex-agent-demo/utils/__init__.py capex-agent-demo/tests/__init__.py capex-agent-demo/agent/__init__.py
git commit -m "scaffold: Phase 1 project structure with requirements"
```

---

## Task 2: Write Failing Data Validation Tests

**Files:**
- Create: `capex-agent-demo/tests/test_data.py`

Write ALL test cases first. They will fail because no CSVs exist yet. This covers PRD acceptance criteria 1-12.

**Step 1: Write test_data.py**

```python
# capex-agent-demo/tests/test_data.py
"""
Validation tests for synthetic data files.
Covers all 12 Phase 1 acceptance criteria from PRD.
"""
import pandas as pd
import pytest
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


# --- Helpers ---

@pytest.fixture
def wbs_master():
    return pd.read_csv(DATA_DIR / "wbs_master.csv")

@pytest.fixture
def itd_extract():
    return pd.read_csv(DATA_DIR / "itd_extract.csv")

@pytest.fixture
def vow_estimates():
    return pd.read_csv(DATA_DIR / "vow_estimates.csv")

@pytest.fixture
def prior_period():
    return pd.read_csv(DATA_DIR / "prior_period_accruals.csv")

@pytest.fixture
def drill_schedule():
    return pd.read_csv(DATA_DIR / "drill_schedule.csv")


# --- AC 11: Row count caps (test first since it's a hard constraint) ---

class TestRowCaps:
    def test_wbs_master_cap(self, wbs_master):
        assert len(wbs_master) <= 50

    def test_itd_extract_cap(self, itd_extract):
        assert len(itd_extract) <= 47

    def test_vow_estimates_cap(self, vow_estimates):
        assert len(vow_estimates) <= 48

    def test_prior_period_cap(self, prior_period):
        assert len(prior_period) <= 50

    def test_drill_schedule_cap(self, drill_schedule):
        assert len(drill_schedule) <= 80


# --- AC 2: wbs_master schema and values ---

class TestWbsMaster:
    def test_exact_row_count(self, wbs_master):
        assert len(wbs_master) == 50

    def test_columns(self, wbs_master):
        expected = {"wbs_element", "well_name", "project_type", "business_unit",
                    "afe_number", "status", "budget_amount", "start_date"}
        assert set(wbs_master.columns) == expected

    def test_unique_wbs_elements(self, wbs_master):
        assert wbs_master["wbs_element"].is_unique

    def test_business_unit_distribution(self, wbs_master):
        counts = wbs_master["business_unit"].value_counts()
        assert counts.get("Permian Basin", 0) >= 30  # ~35
        assert counts.get("DJ Basin", 0) >= 8         # ~10
        assert counts.get("Powder River", 0) >= 3     # ~5

    def test_status_distribution(self, wbs_master):
        counts = wbs_master["status"].value_counts()
        assert counts.get("Active", 0) >= 38           # ~40
        assert counts.get("Complete", 0) >= 5           # ~7
        assert counts.get("Suspended", 0) >= 2          # ~3

    def test_project_type_values(self, wbs_master):
        valid = {"Drilling", "Completion", "Facilities", "Workover"}
        assert set(wbs_master["project_type"].unique()).issubset(valid)

    def test_budget_range(self, wbs_master):
        assert (wbs_master["budget_amount"] >= 2_000_000).all()
        assert (wbs_master["budget_amount"] <= 15_000_000).all()

    def test_wbs_element_format(self, wbs_master):
        assert wbs_master["wbs_element"].str.match(r"^WBS-\d{4}$").all()


# --- AC 3: itd_extract schema and exception triggers ---

class TestItdExtract:
    def test_row_count(self, itd_extract):
        assert len(itd_extract) == 44

    def test_columns(self, itd_extract):
        expected = {"wbs_element", "itd_amount", "last_posting_date",
                    "cost_category", "vendor_count"}
        assert set(itd_extract.columns) == expected

    def test_missing_itd_wbs(self, wbs_master, itd_extract):
        """AC 3: 3 WBS elements completely missing from ITD."""
        master_ids = set(wbs_master["wbs_element"])
        itd_ids = set(itd_extract["wbs_element"])
        missing = master_ids - itd_ids
        # Must include the 3 specific exception WBS IDs
        assert {"WBS-1031", "WBS-1038", "WBS-1044"}.issubset(missing)

    def test_zero_itd_count(self, itd_extract):
        """AC 3: 3 WBS elements have itd_amount = 0."""
        zero_itd = itd_extract[itd_extract["itd_amount"] == 0]
        assert len(zero_itd) == 3
        assert set(zero_itd["wbs_element"]) == {"WBS-1047", "WBS-1048", "WBS-1049"}

    def test_cost_category_values(self, itd_extract):
        valid = {"Material", "Service", "Labor", "Equipment"}
        assert set(itd_extract["cost_category"].unique()).issubset(valid)


# --- AC 4: vow_estimates schema and exception triggers ---

class TestVowEstimates:
    def test_row_count(self, vow_estimates):
        assert len(vow_estimates) == 45

    def test_columns(self, vow_estimates):
        expected = {"wbs_element", "vow_amount", "submission_date",
                    "engineer_name", "phase", "pct_complete"}
        assert set(vow_estimates.columns) == expected

    def test_missing_vow_wbs(self, wbs_master, vow_estimates):
        """AC 4: 2 WBS elements missing from VOW (different from ITD gaps)."""
        master_ids = set(wbs_master["wbs_element"])
        vow_ids = set(vow_estimates["wbs_element"])
        missing = master_ids - vow_ids
        assert {"WBS-1015", "WBS-1042"}.issubset(missing)

    def test_phase_values(self, vow_estimates):
        valid = {"Drilling", "Completion", "Flowback", "Equip"}
        assert set(vow_estimates["phase"].unique()).issubset(valid)

    def test_pct_complete_range(self, vow_estimates):
        assert (vow_estimates["pct_complete"] >= 0).all()
        assert (vow_estimates["pct_complete"] <= 100).all()


# --- AC 5: Negative accrual trigger ---

class TestNegativeAccrual:
    def test_wbs_1027_itd_exceeds_vow(self, itd_extract, vow_estimates):
        """AC 5: WBS-1027 ITD > VOW."""
        itd_val = itd_extract.loc[
            itd_extract["wbs_element"] == "WBS-1027", "itd_amount"
        ].iloc[0]
        vow_val = vow_estimates.loc[
            vow_estimates["wbs_element"] == "WBS-1027", "vow_amount"
        ].iloc[0]
        assert itd_val > vow_val
        assert abs(itd_val - 2_627_000) < 1_000  # ~$2,627K
        assert abs(vow_val - 2_500_000) < 1_000  # ~$2,500K


# --- AC 6: Large swing trigger ---

class TestLargeSwing:
    def test_wbs_1009_swing(self, vow_estimates, itd_extract, prior_period):
        """AC 6: WBS-1009 accrual >25% different from prior period."""
        vow_val = vow_estimates.loc[
            vow_estimates["wbs_element"] == "WBS-1009", "vow_amount"
        ].iloc[0]
        itd_val = itd_extract.loc[
            itd_extract["wbs_element"] == "WBS-1009", "itd_amount"
        ].iloc[0]
        prior_val = prior_period.loc[
            prior_period["wbs_element"] == "WBS-1009", "prior_gross_accrual"
        ].iloc[0]

        current_accrual = vow_val - itd_val
        pct_change = abs(current_accrual - prior_val) / prior_val

        assert pct_change > 0.25  # >25% swing
        assert abs(prior_val - 800_000) < 1_000  # ~$800K prior
        assert abs(current_accrual - 1_072_000) < 5_000  # ~$1,072K current


# --- AC 7 & 8: Join gap counts ---

class TestJoinGaps:
    def test_wbs_to_itd_join(self, wbs_master, itd_extract):
        """AC 7: 44 matches, 6 gaps when joining wbs_master to itd_extract."""
        master_ids = set(wbs_master["wbs_element"])
        itd_ids = set(itd_extract["wbs_element"])
        matched = master_ids & itd_ids
        gaps = master_ids - itd_ids
        assert len(matched) == 44
        assert len(gaps) == 6  # 3 missing + 3 zero-ITD are IN the file

    def test_wbs_to_vow_join(self, wbs_master, vow_estimates):
        """AC 8: 45 matches, 5 gaps when joining wbs_master to vow_estimates."""
        master_ids = set(wbs_master["wbs_element"])
        vow_ids = set(vow_estimates["wbs_element"])
        matched = master_ids & vow_ids
        gaps = master_ids - vow_ids
        assert len(matched) == 45
        assert len(gaps) == 5


# --- AC 9: Drill schedule sequential dates ---

class TestDrillSchedule:
    def test_row_count_range(self, drill_schedule):
        """~60 rows, 20 wells x 3-5 phases."""
        assert 50 <= len(drill_schedule) <= 80

    def test_columns(self, drill_schedule):
        expected = {"wbs_element", "planned_phase", "planned_date", "estimated_cost"}
        assert set(drill_schedule.columns) == expected

    def test_phase_values(self, drill_schedule):
        valid = {"Spud", "TD", "Frac Start", "Frac End", "First Production"}
        assert set(drill_schedule["planned_phase"].unique()).issubset(valid)

    def test_sequential_dates_per_well(self, drill_schedule):
        """AC 9: Dates are sequential per WBS (Spud < TD < Frac Start < Frac End < First Production)."""
        phase_order = {"Spud": 0, "TD": 1, "Frac Start": 2, "Frac End": 3, "First Production": 4}
        drill_schedule["planned_date"] = pd.to_datetime(drill_schedule["planned_date"])
        drill_schedule["phase_rank"] = drill_schedule["planned_phase"].map(phase_order)

        for wbs, group in drill_schedule.groupby("wbs_element"):
            sorted_group = group.sort_values("phase_rank")
            dates = sorted_group["planned_date"].tolist()
            for i in range(len(dates) - 1):
                assert dates[i] <= dates[i + 1], f"{wbs}: {dates[i]} not <= {dates[i+1]}"

    def test_cost_ranges(self, drill_schedule):
        """AC 10: Phase costs are realistic."""
        assert (drill_schedule["estimated_cost"] >= 100_000).all()
        assert (drill_schedule["estimated_cost"] <= 5_500_000).all()


# --- AC 10: Dollar amounts realistic ---

class TestDollarAmounts:
    def test_itd_amounts_realistic(self, itd_extract):
        non_zero = itd_extract[itd_extract["itd_amount"] > 0]
        assert (non_zero["itd_amount"] <= 12_000_000).all()

    def test_vow_amounts_realistic(self, vow_estimates):
        assert (vow_estimates["vow_amount"] >= 100_000).all()
        assert (vow_estimates["vow_amount"] <= 15_000_000).all()
```

**Step 2: Run tests to verify they fail**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
python -m pytest capex-agent-demo/tests/test_data.py -v 2>&1 | head -30
```

Expected: All tests FAIL with `FileNotFoundError` (CSVs don't exist yet).

**Step 3: Commit failing tests**

```bash
git add capex-agent-demo/tests/test_data.py
git commit -m "test: add Phase 1 data validation tests (all failing)"
```

---

## Task 3: Build Synthetic Data Generator

**Files:**
- Create: `capex-agent-demo/data/generate_synthetic_data.py`

This is the main implementation task. One script generates all 5 CSVs.

**Step 1: Write generate_synthetic_data.py**

```python
# capex-agent-demo/data/generate_synthetic_data.py
"""
Generate all 5 synthetic CSV files for the CapEx Gross Accrual Agent demo.

Deterministic: hardcoded exception records + seeded random for normal records.
Run: python data/generate_synthetic_data.py
"""
import pandas as pd
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
SEED = 42

# --- Well name components for realistic O&G naming ---
PREFIXES = [
    "Permian Eagle", "Wolfcamp A", "Delaware Basin", "Bone Spring",
    "Spraberry", "Midland Basin", "Avalon", "Brushy Canyon",
    "Niobrara", "Codell", "Sussex", "Parkman", "Frontier",
    "Shannon", "Powder River", "DJ Basin", "Wattenberg",
    "Pioneer", "Mesa Verde", "Mancos"
]
SUFFIXES = [
    "14H", "22-1H", "7-2H", "3-4H", "11H", "15-3H", "8H",
    "21-2H", "6-1H", "9H", "17-4H", "12H", "5-2H", "19-1H",
    "2H", "16-3H", "10H", "23-1H", "4-2H", "13H",
    "20-1H", "1H", "18-2H", "25H", "24-3H", "26H", "27-1H",
    "28-2H", "29H", "30-1H", "31-2H", "32H", "33-1H", "34-2H",
    "35H", "36-1H", "37-2H", "38H", "39-1H", "40-2H",
    "41H", "42-1H", "43-2H", "44H", "45-1H", "46-2H",
    "47H", "48-1H", "49-2H", "50-1H"
]

# Exception WBS IDs (from PRD Section 4.6)
MISSING_ITD = {"WBS-1031", "WBS-1038", "WBS-1044"}      # HIGH: absent from ITD
ZERO_ITD = {"WBS-1047", "WBS-1048", "WBS-1049"}          # LOW: itd_amount = 0
NEGATIVE_ACCRUAL = "WBS-1027"                              # HIGH: ITD > VOW
MISSING_VOW = {"WBS-1015", "WBS-1042"}                    # MEDIUM: absent from VOW
LARGE_SWING = "WBS-1009"                                   # MEDIUM: >25% change

# WBS elements that are in drill schedule (~20 active drilling/completion wells)
DRILL_SCHEDULE_WBS = [
    f"WBS-{i}" for i in [1001, 1002, 1003, 1005, 1006, 1007, 1008, 1009, 1010,
                          1011, 1013, 1016, 1018, 1020, 1022, 1025, 1029, 1033, 1036, 1040]
]


def generate_wbs_master(rng: random.Random) -> pd.DataFrame:
    """Generate wbs_master.csv: 50 rows."""
    rows = []
    # Business unit assignment: 35 Permian, 10 DJ, 5 Powder River
    bu_assignments = (
        ["Permian Basin"] * 35 +
        ["DJ Basin"] * 10 +
        ["Powder River"] * 5
    )
    # Status assignment: 40 Active, 7 Complete, 3 Suspended
    status_assignments = (
        ["Active"] * 40 +
        ["Complete"] * 7 +
        ["Suspended"] * 3
    )
    # Project type: 30 Drilling, 13 Completion, 5 Facilities, 2 Workover
    type_assignments = (
        ["Drilling"] * 30 +
        ["Completion"] * 13 +
        ["Facilities"] * 5 +
        ["Workover"] * 2
    )

    rng.shuffle(bu_assignments)
    rng.shuffle(status_assignments)
    rng.shuffle(type_assignments)

    for i in range(50):
        wbs_id = f"WBS-{1001 + i}"
        well_name = f"{PREFIXES[i % len(PREFIXES)]} {SUFFIXES[i]}"
        project_type = type_assignments[i]
        business_unit = bu_assignments[i]
        afe_year = rng.choice(["2025", "2026"])
        afe_number = f"AFE-{afe_year}-{rng.randint(1, 200):04d}"
        status = status_assignments[i]
        budget_amount = round(rng.uniform(2_000_000, 15_000_000), 2)
        start_month = rng.randint(1, 12)
        start_year = rng.choice([2025, 2026])
        start_date = date(start_year, start_month, rng.randint(1, 28))

        rows.append({
            "wbs_element": wbs_id,
            "well_name": well_name,
            "project_type": project_type,
            "business_unit": business_unit,
            "afe_number": afe_number,
            "status": status,
            "budget_amount": budget_amount,
            "start_date": start_date.isoformat(),
        })

    return pd.DataFrame(rows)


def generate_itd_extract(wbs_master: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    """Generate itd_extract.csv: 44 rows (6 WBS missing: 3 absent + 3 zero-ITD present)."""
    cost_categories = ["Material", "Service", "Labor", "Equipment"]
    rows = []

    for _, row in wbs_master.iterrows():
        wbs_id = row["wbs_element"]

        # Skip the 3 "Missing ITD" exception WBS elements entirely
        if wbs_id in MISSING_ITD:
            continue

        # Determine ITD amount
        if wbs_id in ZERO_ITD:
            itd_amount = 0.0
        elif wbs_id == NEGATIVE_ACCRUAL:
            itd_amount = 2_627_000.0  # Exceeds VOW of $2,500K
        else:
            budget = row["budget_amount"]
            itd_amount = round(rng.uniform(budget * 0.2, budget * 0.85), 2)

        last_posting = date(2026, 1, rng.randint(5, 28))
        if wbs_id in ZERO_ITD:
            last_posting = date(2025, 12, rng.randint(1, 15))

        rows.append({
            "wbs_element": wbs_id,
            "itd_amount": itd_amount,
            "last_posting_date": last_posting.isoformat(),
            "cost_category": rng.choice(cost_categories),
            "vendor_count": rng.randint(1, 15),
        })

    df = pd.DataFrame(rows)
    assert len(df) == 47, f"Expected 47 ITD rows (50 - 3 missing), got {len(df)}"
    return df


def generate_vow_estimates(
    wbs_master: pd.DataFrame,
    itd_df: pd.DataFrame,
    rng: random.Random
) -> pd.DataFrame:
    """Generate vow_estimates.csv: 45 rows (5 WBS missing from VOW)."""
    engineers = [
        "Sarah Chen", "Mike Torres", "Lisa Park", "James Wright",
        "Maria Garcia", "David Kim", "Rachel Adams", "Tom Henderson"
    ]
    phases = ["Drilling", "Completion", "Flowback", "Equip"]
    rows = []

    # Build ITD lookup for generating realistic VOW amounts
    itd_lookup = dict(zip(itd_df["wbs_element"], itd_df["itd_amount"]))

    for _, row in wbs_master.iterrows():
        wbs_id = row["wbs_element"]

        # Skip the "Missing VOW" exception WBS elements
        if wbs_id in MISSING_VOW:
            continue

        # Also skip the 3 "Missing ITD" WBS elements that also lack VOW
        # PRD: "5 gaps" in VOW = 2 Missing VOW + 3 that overlap with ITD gaps
        if wbs_id in MISSING_ITD:
            continue

        budget = row["budget_amount"]
        itd_val = itd_lookup.get(wbs_id, 0)

        # Determine VOW amount
        if wbs_id == NEGATIVE_ACCRUAL:
            vow_amount = 2_500_000.0  # Less than ITD of $2,627K
        elif wbs_id == LARGE_SWING:
            # Need current accrual ~$1,072K. ITD for this WBS will be generated.
            # VOW = ITD + accrual. We need to know the ITD.
            # Set VOW so that VOW - ITD ≈ $1,072,000
            vow_amount = round(itd_val + 1_072_000, 2)
        elif wbs_id in ZERO_ITD:
            # ITD is 0, so VOW is the full accrual
            vow_amount = round(rng.uniform(500_000, 3_000_000), 2)
        else:
            # Normal: VOW > ITD (positive accrual)
            accrual_pct = rng.uniform(0.05, 0.35)  # 5-35% accrual gap
            vow_amount = round(itd_val * (1 + accrual_pct), 2)
            # Ensure VOW doesn't exceed budget
            vow_amount = min(vow_amount, budget * 0.95)

        pct_complete = round(rng.uniform(10, 100), 1)
        if row["status"] == "Complete":
            pct_complete = 100.0

        rows.append({
            "wbs_element": wbs_id,
            "vow_amount": round(vow_amount, 2),
            "submission_date": "2026-01-28",
            "engineer_name": rng.choice(engineers),
            "phase": rng.choice(phases),
            "pct_complete": pct_complete,
        })

    df = pd.DataFrame(rows)
    assert len(df) == 45, f"Expected 45 VOW rows, got {len(df)}"
    return df


def generate_prior_period_accruals(
    wbs_master: pd.DataFrame,
    itd_df: pd.DataFrame,
    vow_df: pd.DataFrame,
    rng: random.Random
) -> pd.DataFrame:
    """Generate prior_period_accruals.csv: 48 rows."""
    itd_lookup = dict(zip(itd_df["wbs_element"], itd_df["itd_amount"]))
    vow_lookup = dict(zip(vow_df["wbs_element"], vow_df["vow_amount"]))
    rows = []

    # 2 WBS elements won't have prior period (new in Jan 2026)
    skip_prior = {"WBS-1049", "WBS-1050"}

    for _, row in wbs_master.iterrows():
        wbs_id = row["wbs_element"]

        if wbs_id in skip_prior:
            continue

        vow_val = vow_lookup.get(wbs_id)
        itd_val = itd_lookup.get(wbs_id)

        if wbs_id == LARGE_SWING:
            # Prior accrual ~$800K, current ~$1,072K → +34% swing
            prior_accrual = 800_000.0
        elif vow_val is not None and itd_val is not None:
            current_accrual = vow_val - itd_val
            # Normal: prior is within 10-15% of current
            variance = rng.uniform(-0.15, 0.15)
            prior_accrual = round(current_accrual * (1 + variance), 2)
            # Don't let prior go negative for normal records
            prior_accrual = max(prior_accrual, 0)
        else:
            # WBS with missing data — use a reasonable default
            prior_accrual = round(rng.uniform(100_000, 1_500_000), 2)

        rows.append({
            "wbs_element": wbs_id,
            "prior_gross_accrual": round(prior_accrual, 2),
            "period": "2025-12",
        })

    df = pd.DataFrame(rows)
    assert len(df) == 48, f"Expected 48 prior period rows, got {len(df)}"
    return df


def generate_drill_schedule(rng: random.Random) -> pd.DataFrame:
    """Generate drill_schedule.csv: ~60-70 rows (20 wells x 3-5 phases)."""
    all_phases = ["Spud", "TD", "Frac Start", "Frac End", "First Production"]
    rows = []

    for wbs_id in DRILL_SCHEDULE_WBS:
        # Random start date in Q1-Q2 2026
        spud_date = date(2026, rng.randint(1, 4), rng.randint(1, 28))

        # How many phases this well has (3-5)
        num_phases = rng.randint(3, 5)
        phases = all_phases[:num_phases]

        current_date = spud_date
        for phase in phases:
            if phase == "Spud":
                cost = round(rng.uniform(200_000, 500_000), 2)
                gap_days = 0
            elif phase == "TD":
                cost = round(rng.uniform(2_000_000, 5_000_000), 2)
                gap_days = rng.randint(20, 40)
            elif phase == "Frac Start":
                cost = round(rng.uniform(3_000_000, 5_500_000), 2)
                gap_days = rng.randint(5, 15)
            elif phase == "Frac End":
                cost = round(rng.uniform(100_000, 200_000), 2)
                gap_days = rng.randint(14, 28)
            elif phase == "First Production":
                cost = round(rng.uniform(200_000, 400_000), 2)
                gap_days = rng.randint(10, 20)

            current_date = current_date + timedelta(days=gap_days)

            rows.append({
                "wbs_element": wbs_id,
                "planned_phase": phase,
                "planned_date": current_date.isoformat(),
                "estimated_cost": cost,
            })

    return pd.DataFrame(rows)


def main():
    rng = random.Random(SEED)

    print("Generating synthetic data...")

    wbs_df = generate_wbs_master(rng)
    wbs_df.to_csv(OUTPUT_DIR / "wbs_master.csv", index=False)
    print(f"  wbs_master.csv: {len(wbs_df)} rows")

    itd_df = generate_itd_extract(wbs_df, rng)
    itd_df.to_csv(OUTPUT_DIR / "itd_extract.csv", index=False)
    print(f"  itd_extract.csv: {len(itd_df)} rows")

    vow_df = generate_vow_estimates(wbs_df, itd_df, rng)
    vow_df.to_csv(OUTPUT_DIR / "vow_estimates.csv", index=False)
    print(f"  vow_estimates.csv: {len(vow_df)} rows")

    prior_df = generate_prior_period_accruals(wbs_df, itd_df, vow_df, rng)
    prior_df.to_csv(OUTPUT_DIR / "prior_period_accruals.csv", index=False)
    print(f"  prior_period_accruals.csv: {len(prior_df)} rows")

    drill_df = generate_drill_schedule(rng)
    drill_df.to_csv(OUTPUT_DIR / "drill_schedule.csv", index=False)
    print(f"  drill_schedule.csv: {len(drill_df)} rows")

    print("\nDone! All CSV files generated in data/")


if __name__ == "__main__":
    main()
```

**Step 2: Run the generator**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting/capex-agent-demo
python data/generate_synthetic_data.py
```

Expected output:
```
Generating synthetic data...
  wbs_master.csv: 50 rows
  itd_extract.csv: 47 rows
  itd_extract.csv: 44 rows  # after removing 3 missing
  ...
Done! All CSV files generated in data/
```

**Step 3: Run tests**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
python -m pytest capex-agent-demo/tests/test_data.py -v
```

Expected: Most tests should pass. Fix any failures by adjusting the generator.

**Step 4: Iterate until all tests pass**

Debug and fix the generator until `pytest` shows all green. Common issues:
- Join gap counts off by 1 (check which WBS IDs overlap between Missing ITD and Missing VOW)
- Dollar amounts outside expected ranges
- ITD row count not exactly 44 (the 3 zero-ITD rows ARE in the file, so 50 - 3 missing = 47... but PRD says "~44 rows"). Reconcile: the 47 count includes 3 zero-ITD; the test should expect 47 rows with 44 non-zero.

**Important reconciliation note:** Re-read PRD Section 4.2: "~44 rows" in the header, but the detail says "Matches 44 of 50 from wbs_master" — this means 44 rows with ITD data + 3 with zero ITD = 47 rows in the file, with 3 WBS completely absent. The test for `test_row_count` should be 47, and `test_wbs_to_itd_join` should show 47 matched (since zero-ITD rows ARE present in the file) and 3 gaps. **Update the test accordingly.**

**Step 5: Commit**

```bash
git add capex-agent-demo/data/generate_synthetic_data.py capex-agent-demo/data/*.csv
git commit -m "feat: synthetic data generator with all 5 CSV files"
```

---

## Task 4: Build Data Loader

**Files:**
- Create: `capex-agent-demo/utils/data_loader.py`

**Step 1: Write data_loader.py**

```python
# capex-agent-demo/utils/data_loader.py
"""
Data loading utilities for the CapEx Gross Accrual Agent.
Plain functions — @st.cache_data decorators added in Phase 4.
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_wbs_master(business_unit: str = "all") -> pd.DataFrame:
    """Load WBS Master List, optionally filtered by business unit."""
    df = pd.read_csv(DATA_DIR / "wbs_master.csv")
    if business_unit != "all":
        df = df[df["business_unit"] == business_unit]
    return df


def load_itd() -> pd.DataFrame:
    """Load ITD extract from SAP."""
    return pd.read_csv(DATA_DIR / "itd_extract.csv")


def load_vow() -> pd.DataFrame:
    """Load VOW estimates from engineers."""
    return pd.read_csv(DATA_DIR / "vow_estimates.csv")


def load_prior_accruals() -> pd.DataFrame:
    """Load prior period accruals."""
    return pd.read_csv(DATA_DIR / "prior_period_accruals.csv")


def load_drill_schedule() -> pd.DataFrame:
    """Load drill/frac schedule."""
    df = pd.read_csv(DATA_DIR / "drill_schedule.csv")
    df["planned_date"] = pd.to_datetime(df["planned_date"])
    return df
```

**Step 2: Add loader tests to test_data.py**

Append to the end of `capex-agent-demo/tests/test_data.py`:

```python
# --- Data Loader Tests ---
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import (
    load_wbs_master, load_itd, load_vow, load_prior_accruals, load_drill_schedule
)


class TestDataLoader:
    def test_load_wbs_master_all(self):
        df = load_wbs_master("all")
        assert len(df) == 50

    def test_load_wbs_master_permian(self):
        df = load_wbs_master("Permian Basin")
        assert len(df) >= 30
        assert (df["business_unit"] == "Permian Basin").all()

    def test_load_wbs_master_invalid_bu(self):
        df = load_wbs_master("Nonexistent Basin")
        assert len(df) == 0

    def test_load_itd(self):
        df = load_itd()
        assert "itd_amount" in df.columns

    def test_load_vow(self):
        df = load_vow()
        assert "vow_amount" in df.columns

    def test_load_prior_accruals(self):
        df = load_prior_accruals()
        assert "prior_gross_accrual" in df.columns

    def test_load_drill_schedule_date_parsing(self):
        df = load_drill_schedule()
        assert pd.api.types.is_datetime64_any_dtype(df["planned_date"])
```

**Step 3: Run all tests**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
python -m pytest capex-agent-demo/tests/test_data.py -v
```

Expected: ALL PASS

**Step 4: Commit**

```bash
git add capex-agent-demo/utils/data_loader.py capex-agent-demo/tests/test_data.py
git commit -m "feat: data loader utilities with tests"
```

---

## Task 5: Final Verification & PRD Update

**Step 1: Run full test suite one final time**

```bash
cd /Users/amol_gulati/Documents/Coding_Projects/Capex_Forecasting
python -m pytest capex-agent-demo/tests/test_data.py -v --tb=short
```

Expected: All tests pass. Zero failures.

**Step 2: Verify CSV files exist and look reasonable**

```bash
wc -l capex-agent-demo/data/*.csv
head -3 capex-agent-demo/data/wbs_master.csv
```

**Step 3: Update PRD Build Progress Dashboard**

In `planning/prd.md`, update:
- Phase 1 status: `NOT STARTED` → `DONE`
- Phase 1 Started/Completed dates
- Check off all 12 acceptance criteria
- Add Session Log entry
- Set "Current focus" to Phase 2

**Step 4: Commit PRD update**

```bash
git add planning/prd.md
git commit -m "docs: mark Phase 1 complete in PRD"
```

---

## Key Reconciliation Notes

These are things to watch for during implementation that could cause test failures:

1. **ITD row count ambiguity:** PRD header says "~44 rows" but the join logic means 47 rows are in the file (50 - 3 missing). The 3 zero-ITD records ARE present. Tests should expect 47 rows in the file, 47 matches on join, and 3 gaps.

2. **VOW gap count:** PRD says "45 matches and 5 gaps." The 5 gaps = 2 Missing VOW (WBS-1015, WBS-1042) + 3 Missing ITD that also lack VOW (WBS-1031, WBS-1038, WBS-1044). The generator must skip all 5 from VOW.

3. **Large Swing calculation:** WBS-1009 needs VOW - ITD ≈ $1,072K AND prior ≈ $800K. Since ITD is generated randomly, VOW must be computed as ITD + $1,072,000 to hit the target.

4. **Prior period row count:** 48 = 50 - 2 (new wells with no prior). Pick 2 WBS IDs that are "new in Jan 2026" and exclude them.
