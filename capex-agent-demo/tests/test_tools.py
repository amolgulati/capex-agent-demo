"""
Phase 2 Tool Function Tests for CapEx Gross Accrual Agent Demo.

Tests the formatting helpers (utils/formatting.py) and the three load
tool functions (agent/tools.py): load_wbs_master, load_itd, load_vow.

Written TDD-style: these tests WILL FAIL until the implementation
modules are created.
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — ensure capex-agent-demo/ is on sys.path for imports
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.formatting import format_dollar  # noqa: E402
from agent.tools import (  # noqa: E402
    load_wbs_master, load_itd, load_vow,
    calculate_accruals, get_exceptions, get_accrual_detail,
    generate_net_down_entry, get_summary, generate_outlook,
)

# ---------------------------------------------------------------------------
# Constants — WBS universe and known exception elements
# ---------------------------------------------------------------------------

ALL_WBS = [f"WBS-{i}" for i in range(1001, 1051)]  # WBS-1001 .. WBS-1050

MISSING_ITD_WBS = {"WBS-1031", "WBS-1038", "WBS-1044"}
ZERO_ITD_WBS = {"WBS-1047", "WBS-1048", "WBS-1049"}
MISSING_VOW_ONLY = {"WBS-1015", "WBS-1042"}
MISSING_VOW_ALL = MISSING_VOW_ONLY.copy()  # only 2 absent from vow


# ===================================================================
# 1. FORMAT DOLLAR — utils/formatting.py
# ===================================================================


class TestFormatDollar:
    """Verify format_dollar produces human-readable dollar strings."""

    def test_millions(self):
        assert format_dollar(14_300_000) == "$14.3M"

    def test_thousands(self):
        assert format_dollar(127_000) == "$127.0K"

    def test_hundreds(self):
        assert format_dollar(500) == "$500"

    def test_zero(self):
        assert format_dollar(0) == "$0"

    def test_negative(self):
        assert format_dollar(-2_500_000) == "-$2.5M"

    def test_exact_million(self):
        assert format_dollar(1_000_000) == "$1.0M"

    def test_exact_thousand(self):
        assert format_dollar(1_000) == "$1.0K"


# ===================================================================
# 2. LOAD WBS MASTER TOOL — agent/tools.py
# ===================================================================


class TestToolLoadWbsMaster:
    """Verify load_wbs_master tool function behavior."""

    def test_permian_returns_35(self):
        state = {}
        result = load_wbs_master(state, "Permian Basin")
        assert result["count"] == 35

    def test_all_returns_50(self):
        state = {}
        result = load_wbs_master(state, "all")
        assert result["count"] == 50

    def test_active_count_is_40(self):
        state = {}
        result = load_wbs_master(state, "all")
        assert result["active_count"] == 40

    def test_business_units_list(self):
        state = {}
        result = load_wbs_master(state, "all")
        assert result["business_units"] == ["DJ Basin", "Permian Basin", "Powder River"]

    def test_stores_in_session_state(self):
        state = {}
        load_wbs_master(state, "all")
        assert "wbs_data" in state
        assert len(state["wbs_data"]) == 50

    def test_element_schema(self):
        """Each record in wbs_elements must have the expected keys."""
        state = {}
        result = load_wbs_master(state, "all")
        record = result["wbs_elements"][0]
        expected_keys = {
            "wbs_element", "well_name", "project_type", "business_unit",
            "afe_number", "status", "budget_amount", "start_date",
        }
        assert set(record.keys()) == expected_keys

    def test_invalid_bu_returns_empty(self):
        state = {}
        result = load_wbs_master(state, "NonExistent Basin")
        assert result["count"] == 0
        assert result["active_count"] == 0
        assert result["business_units"] == []
        assert result["wbs_elements"] == []


# ===================================================================
# 3. LOAD ITD TOOL — agent/tools.py
# ===================================================================


class TestToolLoadItd:
    """Verify load_itd tool function behavior."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Load ITD for all 50 WBS elements."""
        self.state = {}
        self.result = load_itd(self.state, ALL_WBS)

    def test_matched_count(self):
        assert self.result["matched_count"] == 47

    def test_total_requested(self):
        assert self.result["total_requested"] == 50

    def test_unmatched_wbs(self):
        assert set(self.result["unmatched"]) == MISSING_ITD_WBS

    def test_zero_itd_wbs(self):
        assert set(self.result["zero_itd"]) == ZERO_ITD_WBS

    def test_stores_in_session_state(self):
        assert "itd_data" in self.state
        assert len(self.state["itd_data"]) == 47

    def test_record_schema(self):
        """Each record in itd_records must have the expected keys."""
        record = self.result["itd_records"][0]
        expected_keys = {
            "wbs_element", "itd_amount", "last_posting_date",
            "cost_category", "vendor_count",
        }
        assert set(record.keys()) == expected_keys


# ===================================================================
# 4. LOAD VOW TOOL — agent/tools.py
# ===================================================================


class TestToolLoadVow:
    """Verify load_vow tool function behavior."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Load VOW for all 50 WBS elements."""
        self.state = {}
        self.result = load_vow(self.state, ALL_WBS)

    def test_matched_count(self):
        assert self.result["matched_count"] == 48

    def test_total_requested(self):
        assert self.result["total_requested"] == 50

    def test_unmatched_includes_expected(self):
        """Unmatched should include the 2 missing-VOW-only WBS."""
        unmatched = set(self.result["unmatched"])
        assert MISSING_VOW_ALL <= unmatched, (
            f"Expected at least {MISSING_VOW_ALL}, got {unmatched}"
        )

    def test_stores_in_session_state(self):
        assert "vow_data" in self.state
        assert len(self.state["vow_data"]) == 48

    def test_record_schema(self):
        """Each record in vow_records must have the expected keys."""
        record = self.result["vow_records"][0]
        expected_keys = {
            "wbs_element", "vow_amount", "submission_date",
            "engineer_name", "phase", "pct_complete",
        }
        assert set(record.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Helper — load all 3 data sources into session_state for calculate tests
# ---------------------------------------------------------------------------


def _load_all_data(state):
    """Helper: load all 3 data sources into session_state."""
    result = load_wbs_master(state, business_unit="all")
    all_wbs = [e["wbs_element"] for e in result["wbs_elements"]]
    load_itd(state, wbs_elements=all_wbs)
    load_vow(state, wbs_elements=all_wbs)
    return all_wbs


# ===================================================================
# 5. CALCULATE ACCRUALS — "use_vow_as_accrual" mode
# ===================================================================


class TestCalculateAccrualsUseVow:
    """Verify calculate_accruals with missing_itd_handling='use_vow_as_accrual'."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)
        self.result = calculate_accruals(self.state, missing_itd_handling="use_vow_as_accrual")

    def test_returns_accruals_list(self):
        assert isinstance(self.result["accruals"], list)
        assert len(self.result["accruals"]) > 0

    def test_summary_keys(self):
        summary = self.result["summary"]
        expected_keys = {
            "total_gross_accrual", "total_wbs_count", "calculated_count",
            "exception_count", "prior_period_total", "net_change_total",
        }
        assert expected_keys <= set(summary.keys())

    def test_gross_accrual_formula(self):
        """WBS-1001: VOW=4881331, ITD=4488004 => accrual=393327."""
        wbs1001 = [a for a in self.result["accruals"] if a["wbs_element"] == "WBS-1001"]
        assert len(wbs1001) == 1
        rec = wbs1001[0]
        assert rec["vow_amount"] == 4881331
        assert rec["itd_amount"] == 4488004
        assert rec["gross_accrual"] == 393327

    def test_negative_accrual_detected(self):
        """WBS-1027: ITD > VOW => negative accrual and exception."""
        wbs1027 = [a for a in self.result["accruals"] if a["wbs_element"] == "WBS-1027"]
        assert len(wbs1027) == 1
        rec = wbs1027[0]
        assert rec["gross_accrual"] < 0
        assert "Negative Accrual" in rec["exception_type"]

    def test_detects_all_5_exception_types(self):
        """All 5 exception types must appear in the exceptions list."""
        all_types = {e["exception_type"] for e in self.result["exceptions"]}
        assert "Missing ITD" in all_types
        assert "Negative Accrual" in all_types
        assert "Missing VOW" in all_types
        assert "Large Swing" in all_types
        assert "Zero ITD" in all_types

    def test_large_swing_wbs_1009(self):
        """WBS-1009: accrual ~1072000 vs prior 800000 => Large Swing."""
        wbs1009 = [a for a in self.result["accruals"] if a["wbs_element"] == "WBS-1009"]
        assert len(wbs1009) == 1
        rec = wbs1009[0]
        assert rec["gross_accrual"] == 1072000
        assert "Large Swing" in rec["exception_type"]

    def test_zero_itd_exception(self):
        """WBS-1047, WBS-1048, WBS-1049 should all have Zero ITD exception."""
        zero_itd_exceptions = [
            e for e in self.result["exceptions"]
            if e["exception_type"] == "Zero ITD"
        ]
        zero_itd_wbs = {e["wbs_element"] for e in zero_itd_exceptions}
        assert ZERO_ITD_WBS <= zero_itd_wbs

    def test_stores_results_in_state(self):
        assert "accrual_results" in self.state
        assert "exceptions" in self.state
        assert isinstance(self.state["accrual_results"], list)
        assert isinstance(self.state["exceptions"], list)

    def test_prior_period_loaded(self):
        """WBS-1001 should have prior_accrual populated (not None)."""
        wbs1001 = [a for a in self.result["accruals"] if a["wbs_element"] == "WBS-1001"]
        assert len(wbs1001) == 1
        assert wbs1001[0]["prior_accrual"] is not None

    def test_missing_itd_uses_vow_as_accrual(self):
        """In use_vow mode, missing-ITD WBS should have accrual = full VOW."""
        # WBS-1031/1038/1044 have VOW but no ITD. In use_vow mode,
        # ITD is treated as $0 so gross_accrual should equal vow_amount.
        for wbs_id in MISSING_ITD_WBS:
            recs = [a for a in self.result["accruals"] if a["wbs_element"] == wbs_id]
            assert len(recs) == 1, f"{wbs_id} not found in accruals"
            rec = recs[0]
            assert rec["vow_amount"] is not None, f"{wbs_id} should have a VOW amount"
            assert rec["itd_amount"] == 0, (
                f"{wbs_id} ITD should be treated as 0, got {rec['itd_amount']}"
            )
            assert rec["gross_accrual"] == rec["vow_amount"], (
                f"{wbs_id} accrual should equal VOW ({rec['vow_amount']}), "
                f"got {rec['gross_accrual']}"
            )


# ===================================================================
# 6. CALCULATE ACCRUALS — "exclude_and_flag" mode
# ===================================================================


class TestCalculateAccrualsExclude:
    """Verify calculate_accruals with missing_itd_handling='exclude_and_flag'."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state_vow = {}
        _load_all_data(self.state_vow)
        self.result_vow = calculate_accruals(
            self.state_vow, missing_itd_handling="use_vow_as_accrual"
        )

        self.state_excl = {}
        _load_all_data(self.state_excl)
        self.result_excl = calculate_accruals(
            self.state_excl, missing_itd_handling="exclude_and_flag"
        )

    def test_exclude_produces_fewer_calculated(self):
        """Exclude mode should calculate fewer WBS than use_vow mode."""
        assert (
            self.result_excl["summary"]["calculated_count"]
            <= self.result_vow["summary"]["calculated_count"]
        )

    def test_still_detects_exceptions(self):
        """Key exception types must still be detected in exclude mode."""
        all_types = {e["exception_type"] for e in self.result_excl["exceptions"]}
        assert "Missing ITD" in all_types
        assert "Negative Accrual" in all_types
        assert "Missing VOW" in all_types
        assert "Large Swing" in all_types
        assert "Zero ITD" in all_types

    def test_missing_itd_excluded_from_total(self):
        """In exclude mode, total_gross_accrual should be lower than use_vow mode
        because WBS-1031/1038/1044 have VOW but no ITD and are excluded."""
        assert self.result_excl["summary"]["total_gross_accrual"] is not None
        assert (
            self.result_excl["summary"]["total_gross_accrual"]
            < self.result_vow["summary"]["total_gross_accrual"]
        )


# ===================================================================
# 7. GET EXCEPTIONS
# ===================================================================


class TestGetExceptions:
    """Verify get_exceptions filtering and structure."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)
        calculate_accruals(self.state, missing_itd_handling="use_vow_as_accrual")

    def test_all_returns_all(self):
        result = get_exceptions(self.state, severity="all")
        assert result["count"] == len(result["exceptions"])
        assert result["count"] > 0

    def test_high_only(self):
        result = get_exceptions(self.state, severity="high")
        for exc in result["exceptions"]:
            assert exc["severity"] == "HIGH"

    def test_medium_only(self):
        result = get_exceptions(self.state, severity="medium")
        for exc in result["exceptions"]:
            assert exc["severity"] == "MEDIUM"

    def test_low_only(self):
        result = get_exceptions(self.state, severity="low")
        for exc in result["exceptions"]:
            assert exc["severity"] == "LOW"

    def test_by_type_counts(self):
        result = get_exceptions(self.state, severity="all")
        by_type = result["by_type"]
        assert by_type.get("Negative Accrual", 0) >= 1
        assert by_type.get("Missing VOW", 0) >= 1
        assert by_type.get("Zero ITD", 0) >= 1

    def test_high_includes_negative_accrual(self):
        result = get_exceptions(self.state, severity="high")
        types = {e["exception_type"] for e in result["exceptions"]}
        assert "Negative Accrual" in types

    def test_exception_schema(self):
        result = get_exceptions(self.state, severity="all")
        assert len(result["exceptions"]) > 0
        exc = result["exceptions"][0]
        expected_keys = {
            "wbs_element", "well_name", "exception_type", "severity",
            "detail", "recommended_action", "vow_amount", "itd_amount",
            "accrual_amount",
        }
        assert expected_keys <= set(exc.keys())


# ===================================================================
# 8. GET ACCRUAL DETAIL
# ===================================================================


class TestGetAccrualDetail:
    """Verify get_accrual_detail returns merged per-WBS info."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)
        calculate_accruals(self.state, missing_itd_handling="use_vow_as_accrual")

    def test_wbs_1027_negative(self):
        result = get_accrual_detail(self.state, wbs_element="WBS-1027")
        assert result["gross_accrual"] < 0
        assert result["itd_amount"] > result["vow_amount"]

    def test_wbs_1027_has_exception(self):
        result = get_accrual_detail(self.state, wbs_element="WBS-1027")
        exc_types = [e["exception_type"] for e in result["exceptions"]]
        assert "Negative Accrual" in exc_types

    def test_normal_wbs(self):
        """WBS-1001 should have gross_accrual, vow, and itd populated."""
        result = get_accrual_detail(self.state, wbs_element="WBS-1001")
        assert result["gross_accrual"] is not None
        assert result["vow_amount"] is not None
        assert result["itd_amount"] is not None

    def test_includes_metadata(self):
        result = get_accrual_detail(self.state, wbs_element="WBS-1001")
        assert "project_type" in result
        assert "business_unit" in result
        assert "status" in result
        assert "well_name" in result

    def test_not_found(self):
        result = get_accrual_detail(self.state, wbs_element="WBS-9999")
        assert "error" in result


# ===================================================================
# 9. GENERATE NET-DOWN ENTRY
# ===================================================================


class TestGenerateNetDownEntry:
    """Verify generate_net_down_entry produces a valid journal entry."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)
        calculate_accruals(self.state, missing_itd_handling="use_vow_as_accrual")
        self.result = generate_net_down_entry(self.state)

    def test_returns_journal_entry(self):
        je = self.result["journal_entry"]
        assert "period" in je
        assert "net_down_amount" in je
        assert "total_current_accrual" in je
        assert "total_prior_accrual" in je

    def test_net_down_equals_current_minus_prior(self):
        je = self.result["journal_entry"]
        assert je["total_current_accrual"] - je["total_prior_accrual"] == je["net_down_amount"]

    def test_detail_per_wbs(self):
        detail = self.result["detail"]
        assert len(detail) > 0
        rec = detail[0]
        assert "wbs_element" in rec
        assert "current_accrual" in rec
        assert "prior_accrual" in rec
        assert "net_change" in rec

    def test_has_debit_credit(self):
        je = self.result["journal_entry"]
        assert "debit_account" in je
        assert "credit_account" in je

    def test_has_summary_text(self):
        assert isinstance(self.result["summary_text"], str)
        assert len(self.result["summary_text"]) > 0


# ===================================================================
# 10. GET SUMMARY
# ===================================================================


class TestGetSummary:
    """Verify get_summary groups accruals by dimension."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)
        calculate_accruals(self.state, missing_itd_handling="use_vow_as_accrual")

    def test_group_by_business_unit(self):
        result = get_summary(self.state, group_by="business_unit")
        group_values = [s["group_value"] for s in result["summary"]]
        assert "Permian Basin" in group_values

    def test_group_by_project_type(self):
        result = get_summary(self.state, group_by="project_type")
        group_values = [s["group_value"] for s in result["summary"]]
        assert "Drilling" in group_values

    def test_totals_match_grand_total(self):
        result = get_summary(self.state, group_by="business_unit")
        group_sum = sum(s["total_accrual"] for s in result["summary"])
        assert abs(group_sum - result["grand_total"]) < 0.01

    def test_pct_of_total_sums_to_1(self):
        result = get_summary(self.state, group_by="business_unit")
        pct_sum = sum(s["pct_of_total"] for s in result["summary"])
        assert abs(pct_sum - 1.0) < 0.01

    def test_summary_record_schema(self):
        result = get_summary(self.state, group_by="business_unit")
        assert len(result["summary"]) > 0
        rec = result["summary"][0]
        expected_keys = {
            "group_value", "total_accrual", "wbs_count",
            "avg_accrual", "exception_count", "pct_of_total",
        }
        assert expected_keys <= set(rec.keys())


# ===================================================================
# 11. GENERATE OUTLOOK
# ===================================================================


class TestGenerateOutlook:
    """Verify generate_outlook projects future accruals correctly."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.state = {}
        _load_all_data(self.state)

    def test_returns_3_months(self):
        result = generate_outlook(self.state, months_forward=3)
        assert len(result["outlook"]) == 3

    def test_returns_6_months(self):
        result = generate_outlook(self.state, months_forward=6)
        assert len(result["outlook"]) == 6

    def test_month_schema(self):
        result = generate_outlook(self.state, months_forward=3)
        rec = result["outlook"][0]
        expected_keys = {
            "month", "expected_accrual", "well_count",
            "new_wells_starting", "phases_completing",
        }
        assert expected_keys <= set(rec.keys())

    def test_total_outlook_is_sum(self):
        result = generate_outlook(self.state, months_forward=3)
        expected = sum(m["expected_accrual"] for m in result["outlook"])
        assert abs(expected - result["total_outlook"]) < 0.01

    def test_wells_in_schedule_count(self):
        result = generate_outlook(self.state, months_forward=3)
        assert result["wells_in_schedule"] > 0

    def test_schedule_detail_present(self):
        result = generate_outlook(self.state, months_forward=3)
        assert len(result["schedule_detail"]) > 0
        rec = result["schedule_detail"][0]
        assert "wbs_element" in rec
        assert "estimated_cost" in rec

    def test_months_are_sequential(self):
        result = generate_outlook(self.state, months_forward=3)
        months = [m["month"] for m in result["outlook"]]
        assert months == ["2026-02", "2026-03", "2026-04"]


# ===================================================================
# 10. TOOL DEFINITIONS — agent/tool_definitions.py
# ===================================================================

from agent.tool_definitions import TOOL_DEFINITIONS


class TestToolDefinitions:
    """PRD AC 13: tool_definitions.py contains valid Claude API schemas."""

    def test_has_9_tools(self):
        assert len(TOOL_DEFINITIONS) == 9

    def test_all_tools_have_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
            assert "input_schema" in tool, f"Tool {tool.get('name')} missing 'input_schema'"

    def test_all_tool_names(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        expected = {
            "load_wbs_master", "load_itd", "load_vow",
            "calculate_accruals", "get_exceptions", "get_accrual_detail",
            "generate_net_down_entry", "get_summary", "generate_outlook",
        }
        assert names == expected

    def test_schemas_are_valid_json_schema(self):
        for tool in TOOL_DEFINITIONS:
            schema = tool["input_schema"]
            assert schema.get("type") == "object"
            assert "properties" in schema

    def test_session_state_not_in_schemas(self):
        """session_state is injected by orchestrator, not in API schemas."""
        for tool in TOOL_DEFINITIONS:
            props = tool["input_schema"].get("properties", {})
            assert "session_state" not in props, (
                f"Tool {tool['name']} should not expose session_state"
            )
