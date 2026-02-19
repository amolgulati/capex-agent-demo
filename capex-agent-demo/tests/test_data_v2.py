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
