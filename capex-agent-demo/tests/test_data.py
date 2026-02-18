"""
Phase 1 Data Validation Tests for CapEx Gross Accrual Agent Demo.

Tests all 12 PRD acceptance criteria for the five synthetic CSV files.
Written TDD-style: these tests WILL FAIL until the data generator (Task 3)
creates the CSV files in capex-agent-demo/data/.

CSV files under test:
    - wbs_master.csv          (50 rows)
    - itd_extract.csv         (47 rows)
    - vow_estimates.csv       (45 rows)
    - prior_period_accruals.csv (48 rows)
    - drill_schedule.csv      (60-70 rows, max 80)
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

WBS_MASTER_PATH = DATA_DIR / "wbs_master.csv"
ITD_EXTRACT_PATH = DATA_DIR / "itd_extract.csv"
VOW_ESTIMATES_PATH = DATA_DIR / "vow_estimates.csv"
PRIOR_PERIOD_PATH = DATA_DIR / "prior_period_accruals.csv"
DRILL_SCHEDULE_PATH = DATA_DIR / "drill_schedule.csv"

# WBS element universe
ALL_WBS = [f"WBS-{i}" for i in range(1001, 1051)]  # WBS-1001 .. WBS-1050

# Specific exception WBS elements
MISSING_ITD_WBS = {"WBS-1031", "WBS-1038", "WBS-1044"}
ZERO_ITD_WBS = {"WBS-1047", "WBS-1048", "WBS-1049"}
MISSING_VOW_ONLY = {"WBS-1015", "WBS-1042"}
MISSING_VOW_ALL = MISSING_VOW_ONLY | MISSING_ITD_WBS  # 5 total

NEGATIVE_ACCRUAL_WBS = "WBS-1027"
LARGE_SWING_WBS = "WBS-1009"

# ---------------------------------------------------------------------------
# Fixtures — load each CSV once per test session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def wbs_master() -> pd.DataFrame:
    return pd.read_csv(WBS_MASTER_PATH)


@pytest.fixture(scope="session")
def itd_extract() -> pd.DataFrame:
    return pd.read_csv(ITD_EXTRACT_PATH)


@pytest.fixture(scope="session")
def vow_estimates() -> pd.DataFrame:
    return pd.read_csv(VOW_ESTIMATES_PATH)


@pytest.fixture(scope="session")
def prior_period() -> pd.DataFrame:
    return pd.read_csv(PRIOR_PERIOD_PATH)


@pytest.fixture(scope="session")
def drill_schedule() -> pd.DataFrame:
    return pd.read_csv(DRILL_SCHEDULE_PATH)


# ===================================================================
# 1. ROW CAPS — hard limits from the PRD
# ===================================================================


class TestRowCaps:
    """PRD Criterion: Each file must not exceed its row cap."""

    def test_wbs_master_row_count(self, wbs_master):
        assert len(wbs_master) == 50, f"Expected 50 rows, got {len(wbs_master)}"

    def test_itd_extract_row_count(self, itd_extract):
        assert len(itd_extract) == 47, f"Expected 47 rows, got {len(itd_extract)}"

    def test_vow_estimates_row_count(self, vow_estimates):
        assert len(vow_estimates) == 45, f"Expected 45 rows, got {len(vow_estimates)}"

    def test_prior_period_row_count(self, prior_period):
        assert len(prior_period) == 48, f"Expected 48 rows, got {len(prior_period)}"

    def test_drill_schedule_row_cap(self, drill_schedule):
        n = len(drill_schedule)
        assert 60 <= n <= 80, (
            f"Expected 60-80 rows, got {n}"
        )


# ===================================================================
# 2. WBS MASTER — schema, formats, distributions
# ===================================================================


class TestWbsMaster:
    """PRD Criterion: wbs_master.csv schema and value constraints."""

    EXPECTED_COLUMNS = [
        "wbs_element", "well_name", "project_type", "business_unit",
        "afe_number", "status", "budget_amount", "start_date",
    ]

    def test_columns(self, wbs_master):
        assert list(wbs_master.columns) == self.EXPECTED_COLUMNS

    def test_wbs_element_format(self, wbs_master):
        """WBS elements must be WBS-1001 through WBS-1050."""
        expected = set(ALL_WBS)
        actual = set(wbs_master["wbs_element"])
        assert actual == expected, f"Difference: {actual.symmetric_difference(expected)}"

    def test_wbs_element_uniqueness(self, wbs_master):
        assert wbs_master["wbs_element"].is_unique

    def test_project_type_values(self, wbs_master):
        allowed = {"Drilling", "Completion", "Facilities", "Workover"}
        actual = set(wbs_master["project_type"].unique())
        assert actual <= allowed, f"Unexpected project types: {actual - allowed}"
        assert actual == allowed, f"Missing project types: {allowed - actual}"

    def test_business_unit_distribution(self, wbs_master):
        counts = wbs_master["business_unit"].value_counts()
        assert counts.get("Permian Basin", 0) == 35, (
            f"Permian Basin: expected ~35, got {counts.get('Permian Basin', 0)}"
        )
        assert counts.get("DJ Basin", 0) == 10, (
            f"DJ Basin: expected ~10, got {counts.get('DJ Basin', 0)}"
        )
        assert counts.get("Powder River", 0) == 5, (
            f"Powder River: expected ~5, got {counts.get('Powder River', 0)}"
        )

    def test_status_distribution(self, wbs_master):
        counts = wbs_master["status"].value_counts()
        assert counts.get("Active", 0) == 40, (
            f"Active: expected ~40, got {counts.get('Active', 0)}"
        )
        assert counts.get("Complete", 0) == 7, (
            f"Complete: expected ~7, got {counts.get('Complete', 0)}"
        )
        assert counts.get("Suspended", 0) == 3, (
            f"Suspended: expected ~3, got {counts.get('Suspended', 0)}"
        )

    def test_budget_amount_range(self, wbs_master):
        low = wbs_master["budget_amount"].min()
        high = wbs_master["budget_amount"].max()
        assert low >= 2_000_000, f"Min budget {low:,.0f} below $2M"
        assert high <= 15_000_000, f"Max budget {high:,.0f} above $15M"

    def test_start_date_parseable(self, wbs_master):
        """start_date must parse as a valid date."""
        dates = pd.to_datetime(wbs_master["start_date"], errors="coerce")
        assert dates.notna().all(), "Some start_date values failed to parse"


# ===================================================================
# 3. ITD EXTRACT — schema, missing/zero patterns
# ===================================================================


class TestItdExtract:
    """PRD Criterion: itd_extract.csv schema and exception patterns."""

    EXPECTED_COLUMNS = [
        "wbs_element", "itd_amount", "last_posting_date",
        "cost_category", "vendor_count",
    ]

    def test_columns(self, itd_extract):
        assert list(itd_extract.columns) == self.EXPECTED_COLUMNS

    def test_wbs_element_uniqueness(self, itd_extract):
        assert itd_extract["wbs_element"].is_unique

    def test_missing_itd_wbs_absent(self, itd_extract):
        """The 3 'Missing ITD' WBS elements must NOT appear in itd_extract."""
        present = set(itd_extract["wbs_element"])
        overlap = MISSING_ITD_WBS & present
        assert overlap == set(), f"These should be absent: {overlap}"

    def test_zero_itd_wbs_present_with_zero(self, itd_extract):
        """The 3 'Zero ITD' WBS must be present with itd_amount == 0."""
        for wbs in ZERO_ITD_WBS:
            row = itd_extract[itd_extract["wbs_element"] == wbs]
            assert len(row) == 1, f"{wbs} not found in itd_extract"
            assert row.iloc[0]["itd_amount"] == 0, (
                f"{wbs} itd_amount should be 0, got {row.iloc[0]['itd_amount']}"
            )

    def test_cost_category_values(self, itd_extract):
        allowed = {"Material", "Service", "Labor", "Equipment"}
        actual = set(itd_extract["cost_category"].unique())
        assert actual <= allowed, f"Unexpected cost categories: {actual - allowed}"
        assert actual == allowed, f"Missing cost categories: {allowed - actual}"

    def test_vendor_count_positive_or_zero(self, itd_extract):
        assert (itd_extract["vendor_count"] >= 0).all()

    def test_last_posting_date_parseable(self, itd_extract):
        dates = pd.to_datetime(itd_extract["last_posting_date"], errors="coerce")
        assert dates.notna().all(), "Some last_posting_date values failed to parse"


# ===================================================================
# 4. VOW ESTIMATES — schema, missing patterns
# ===================================================================


class TestVowEstimates:
    """PRD Criterion: vow_estimates.csv schema and exception patterns."""

    EXPECTED_COLUMNS = [
        "wbs_element", "vow_amount", "submission_date",
        "engineer_name", "phase", "pct_complete",
    ]

    def test_columns(self, vow_estimates):
        assert list(vow_estimates.columns) == self.EXPECTED_COLUMNS

    def test_wbs_element_uniqueness(self, vow_estimates):
        assert vow_estimates["wbs_element"].is_unique

    def test_missing_vow_wbs_absent(self, vow_estimates):
        """All 5 Missing-VOW WBS elements must NOT appear in vow_estimates."""
        present = set(vow_estimates["wbs_element"])
        overlap = MISSING_VOW_ALL & present
        assert overlap == set(), f"These should be absent: {overlap}"

    def test_phase_values(self, vow_estimates):
        allowed = {"Drilling", "Completion", "Flowback", "Equip"}
        actual = set(vow_estimates["phase"].unique())
        assert actual <= allowed, f"Unexpected phases: {actual - allowed}"
        assert actual == allowed, f"Missing phases: {allowed - actual}"

    def test_pct_complete_range(self, vow_estimates):
        assert (vow_estimates["pct_complete"] >= 0).all(), "pct_complete < 0 found"
        assert (vow_estimates["pct_complete"] <= 100).all(), "pct_complete > 100 found"

    def test_submission_date_parseable(self, vow_estimates):
        dates = pd.to_datetime(vow_estimates["submission_date"], errors="coerce")
        assert dates.notna().all(), "Some submission_date values failed to parse"

    def test_vow_amount_non_negative(self, vow_estimates):
        assert (vow_estimates["vow_amount"] >= 0).all(), "Negative vow_amount found"


# ===================================================================
# 5. PRIOR PERIOD ACCRUALS
# ===================================================================


class TestPriorPeriod:
    """PRD Criterion: prior_period_accruals.csv schema and values."""

    EXPECTED_COLUMNS = ["wbs_element", "prior_gross_accrual", "period"]

    def test_columns(self, prior_period):
        assert list(prior_period.columns) == self.EXPECTED_COLUMNS

    def test_period_value(self, prior_period):
        assert (prior_period["period"] == "2025-12").all(), (
            "All period values must be '2025-12'"
        )

    def test_wbs_element_uniqueness(self, prior_period):
        assert prior_period["wbs_element"].is_unique

    def test_prior_gross_accrual_non_negative(self, prior_period):
        assert (prior_period["prior_gross_accrual"] >= 0).all()


# ===================================================================
# 6. NEGATIVE ACCRUAL EXCEPTION — WBS-1027
# ===================================================================


class TestNegativeAccrual:
    """PRD Criterion: WBS-1027 must produce a negative accrual (ITD > VOW)."""

    def test_wbs_1027_itd_exceeds_vow(self, itd_extract, vow_estimates):
        itd_row = itd_extract[itd_extract["wbs_element"] == NEGATIVE_ACCRUAL_WBS]
        vow_row = vow_estimates[vow_estimates["wbs_element"] == NEGATIVE_ACCRUAL_WBS]

        assert len(itd_row) == 1, f"{NEGATIVE_ACCRUAL_WBS} not in itd_extract"
        assert len(vow_row) == 1, f"{NEGATIVE_ACCRUAL_WBS} not in vow_estimates"

        itd_amt = itd_row.iloc[0]["itd_amount"]
        vow_amt = vow_row.iloc[0]["vow_amount"]

        assert itd_amt > vow_amt, (
            f"Negative accrual requires ITD > VOW: "
            f"ITD={itd_amt:,.0f}, VOW={vow_amt:,.0f}"
        )

    def test_wbs_1027_itd_approx_2627k(self, itd_extract):
        row = itd_extract[itd_extract["wbs_element"] == NEGATIVE_ACCRUAL_WBS]
        itd_amt = row.iloc[0]["itd_amount"]
        assert abs(itd_amt - 2_627_000) < 50_000, (
            f"WBS-1027 ITD expected ~$2,627K, got {itd_amt:,.0f}"
        )

    def test_wbs_1027_vow_approx_2500k(self, vow_estimates):
        row = vow_estimates[vow_estimates["wbs_element"] == NEGATIVE_ACCRUAL_WBS]
        vow_amt = row.iloc[0]["vow_amount"]
        assert abs(vow_amt - 2_500_000) < 50_000, (
            f"WBS-1027 VOW expected ~$2,500K, got {vow_amt:,.0f}"
        )


# ===================================================================
# 7. LARGE SWING EXCEPTION — WBS-1009
# ===================================================================


class TestLargeSwing:
    """PRD Criterion: WBS-1009 must show a >30% swing vs. prior period."""

    def test_wbs_1009_swing_exceeds_30_pct(
        self, itd_extract, vow_estimates, prior_period
    ):
        itd_row = itd_extract[itd_extract["wbs_element"] == LARGE_SWING_WBS]
        vow_row = vow_estimates[vow_estimates["wbs_element"] == LARGE_SWING_WBS]
        pp_row = prior_period[prior_period["wbs_element"] == LARGE_SWING_WBS]

        assert len(itd_row) == 1, f"{LARGE_SWING_WBS} not in itd_extract"
        assert len(vow_row) == 1, f"{LARGE_SWING_WBS} not in vow_estimates"
        assert len(pp_row) == 1, f"{LARGE_SWING_WBS} not in prior_period"

        itd_amt = itd_row.iloc[0]["itd_amount"]
        vow_amt = vow_row.iloc[0]["vow_amount"]
        prior_accrual = pp_row.iloc[0]["prior_gross_accrual"]

        current_accrual = vow_amt - itd_amt
        swing_pct = abs(current_accrual - prior_accrual) / prior_accrual * 100

        assert swing_pct > 30, (
            f"Expected >30% swing, got {swing_pct:.1f}% "
            f"(current={current_accrual:,.0f}, prior={prior_accrual:,.0f})"
        )

    def test_wbs_1009_prior_accrual_approx_800k(self, prior_period):
        row = prior_period[prior_period["wbs_element"] == LARGE_SWING_WBS]
        prior_amt = row.iloc[0]["prior_gross_accrual"]
        assert abs(prior_amt - 800_000) < 50_000, (
            f"WBS-1009 prior_gross_accrual expected ~$800K, got {prior_amt:,.0f}"
        )

    def test_wbs_1009_current_accrual_approx_1072k(self, itd_extract, vow_estimates):
        itd_row = itd_extract[itd_extract["wbs_element"] == LARGE_SWING_WBS]
        vow_row = vow_estimates[vow_estimates["wbs_element"] == LARGE_SWING_WBS]

        current_accrual = (
            vow_row.iloc[0]["vow_amount"] - itd_row.iloc[0]["itd_amount"]
        )
        assert abs(current_accrual - 1_072_000) < 50_000, (
            f"WBS-1009 current accrual expected ~$1,072K, got {current_accrual:,.0f}"
        )


# ===================================================================
# 8. JOIN GAPS — cross-file referential integrity
# ===================================================================


class TestJoinGaps:
    """PRD Criterion: Correct join gaps between master and child files."""

    def test_wbs_master_to_itd_matches(self, wbs_master, itd_extract):
        """wbs_master -> itd_extract: 47 matches, 3 gaps."""
        master_wbs = set(wbs_master["wbs_element"])
        itd_wbs = set(itd_extract["wbs_element"])

        matches = master_wbs & itd_wbs
        gaps = master_wbs - itd_wbs

        assert len(matches) == 47, f"Expected 47 ITD matches, got {len(matches)}"
        assert len(gaps) == 3, f"Expected 3 ITD gaps, got {len(gaps)}"
        assert gaps == MISSING_ITD_WBS, f"ITD gap WBS mismatch: {gaps}"

    def test_wbs_master_to_vow_matches(self, wbs_master, vow_estimates):
        """wbs_master -> vow_estimates: 45 matches, 5 gaps."""
        master_wbs = set(wbs_master["wbs_element"])
        vow_wbs = set(vow_estimates["wbs_element"])

        matches = master_wbs & vow_wbs
        gaps = master_wbs - vow_wbs

        assert len(matches) == 45, f"Expected 45 VOW matches, got {len(matches)}"
        assert len(gaps) == 5, f"Expected 5 VOW gaps, got {len(gaps)}"
        assert gaps == MISSING_VOW_ALL, f"VOW gap WBS mismatch: {gaps}"

    def test_itd_wbs_subset_of_master(self, wbs_master, itd_extract):
        """Every WBS in itd_extract must exist in wbs_master (no orphans)."""
        master_wbs = set(wbs_master["wbs_element"])
        itd_wbs = set(itd_extract["wbs_element"])
        orphans = itd_wbs - master_wbs
        assert orphans == set(), f"Orphan WBS in itd_extract: {orphans}"

    def test_vow_wbs_subset_of_master(self, wbs_master, vow_estimates):
        """Every WBS in vow_estimates must exist in wbs_master (no orphans)."""
        master_wbs = set(wbs_master["wbs_element"])
        vow_wbs = set(vow_estimates["wbs_element"])
        orphans = vow_wbs - master_wbs
        assert orphans == set(), f"Orphan WBS in vow_estimates: {orphans}"

    def test_prior_period_wbs_subset_of_master(self, wbs_master, prior_period):
        """Every WBS in prior_period must exist in wbs_master."""
        master_wbs = set(wbs_master["wbs_element"])
        pp_wbs = set(prior_period["wbs_element"])
        orphans = pp_wbs - master_wbs
        assert orphans == set(), f"Orphan WBS in prior_period: {orphans}"


# ===================================================================
# 9. DRILL SCHEDULE — schema, sequencing, phases
# ===================================================================


class TestDrillSchedule:
    """PRD Criterion: drill_schedule.csv schema and date sequencing."""

    EXPECTED_COLUMNS = [
        "wbs_element", "planned_phase", "planned_date", "estimated_cost",
    ]
    PHASE_ORDER = ["Spud", "TD", "Frac Start", "Frac End", "First Production"]

    def test_columns(self, drill_schedule):
        assert list(drill_schedule.columns) == self.EXPECTED_COLUMNS

    def test_planned_phase_values(self, drill_schedule):
        allowed = set(self.PHASE_ORDER)
        actual = set(drill_schedule["planned_phase"].unique())
        assert actual <= allowed, f"Unexpected phases: {actual - allowed}"
        assert actual == allowed, f"Missing phases: {allowed - actual}"

    def test_estimated_cost_range(self, drill_schedule):
        low = drill_schedule["estimated_cost"].min()
        high = drill_schedule["estimated_cost"].max()
        assert low >= 100_000, f"Min estimated_cost {low:,.0f} below $100K"
        assert high <= 5_500_000, f"Max estimated_cost {high:,.0f} above $5.5M"

    def test_planned_date_parseable(self, drill_schedule):
        dates = pd.to_datetime(drill_schedule["planned_date"], errors="coerce")
        assert dates.notna().all(), "Some planned_date values failed to parse"

    def test_dates_sequential_per_wbs(self, drill_schedule):
        """For each WBS, phase dates must be strictly ascending in phase order."""
        phase_rank = {p: i for i, p in enumerate(self.PHASE_ORDER)}
        df = drill_schedule.copy()
        df["planned_date"] = pd.to_datetime(df["planned_date"])
        df["phase_rank"] = df["planned_phase"].map(phase_rank)

        violations = []
        for wbs, group in df.groupby("wbs_element"):
            group_sorted = group.sort_values("phase_rank")
            dates = group_sorted["planned_date"].tolist()
            phases = group_sorted["planned_phase"].tolist()
            for i in range(1, len(dates)):
                if dates[i] <= dates[i - 1]:
                    violations.append(
                        f"{wbs}: {phases[i-1]}({dates[i-1].date()}) "
                        f">= {phases[i]}({dates[i].date()})"
                    )

        assert violations == [], (
            f"Date sequencing violations:\n" + "\n".join(violations)
        )

    def test_wbs_elements_subset_of_master(self, wbs_master, drill_schedule):
        """Every WBS in drill_schedule must exist in wbs_master."""
        master_wbs = set(wbs_master["wbs_element"])
        drill_wbs = set(drill_schedule["wbs_element"])
        orphans = drill_wbs - master_wbs
        assert orphans == set(), f"Orphan WBS in drill_schedule: {orphans}"


# ===================================================================
# 10. DOLLAR AMOUNTS — general sanity checks across files
# ===================================================================


class TestDollarAmounts:
    """PRD Criterion: Dollar amounts fall within expected ranges."""

    def test_itd_amounts_non_negative(self, itd_extract):
        assert (itd_extract["itd_amount"] >= 0).all(), "Negative itd_amount found"

    def test_itd_non_zero_amounts_reasonable(self, itd_extract):
        """Non-zero ITD amounts should be in a reasonable range for CapEx."""
        non_zero = itd_extract[itd_extract["itd_amount"] > 0]["itd_amount"]
        if len(non_zero) > 0:
            assert non_zero.min() >= 10_000, (
                f"Suspiciously small non-zero ITD: {non_zero.min():,.0f}"
            )
            assert non_zero.max() <= 15_000_000, (
                f"ITD exceeds max budget: {non_zero.max():,.0f}"
            )

    def test_vow_amounts_reasonable(self, vow_estimates):
        """VOW amounts should be positive and within budget range."""
        assert (vow_estimates["vow_amount"] >= 0).all()
        assert vow_estimates["vow_amount"].max() <= 15_000_000, (
            f"VOW exceeds max budget: {vow_estimates['vow_amount'].max():,.0f}"
        )

    def test_prior_accrual_reasonable(self, prior_period):
        """Prior gross accrual should be within a reasonable range."""
        assert prior_period["prior_gross_accrual"].max() <= 15_000_000
