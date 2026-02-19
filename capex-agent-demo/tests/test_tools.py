"""Tests for agent tools — the 3-step close calculation chain."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.tools import (
    calculate_accruals, calculate_net_down, calculate_outlook,
    generate_outlook_load_file,
)

import pandas as pd

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
                assert isinstance(rec[f"{cat}_future_outlook"], (int, float))

    def test_over_budget_exception_detected(self):
        result = calculate_outlook()
        over_budget = [e for e in result["exceptions"]
                       if e["exception_type"] == "Over Budget"]
        assert len(over_budget) >= 1

    def test_summary_totals(self):
        result = calculate_outlook()
        assert "total_future_outlook" in result["summary"]


class TestGenerateOutlookLoadFile:
    """Monthly outlook grid for OneStream."""

    def test_returns_dataframe(self):
        result = generate_outlook_load_file()
        assert "load_file" in result
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
