"""
Agent tool functions for the CapEx Gross Accrual Agent.

Each function takes a session_state dict as its first parameter for sharing
data between tool calls. All functions return plain dicts (JSON-serializable).
"""

import sys
from datetime import date
from calendar import monthrange
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils import data_loader
from utils.formatting import format_dollar

# ---------------------------------------------------------------------------
# Reference date constant — hardcoded to January 2026
# ---------------------------------------------------------------------------

REFERENCE_DATE = date(2026, 1, 1)


def load_wbs_master(session_state: dict, business_unit: str) -> dict:
    """Load WBS Master List, optionally filtered by business unit."""
    df = data_loader.load_wbs_master(business_unit)
    session_state["wbs_data"] = df
    return {
        "wbs_elements": df.to_dict(orient="records"),
        "count": len(df),
        "active_count": int((df["status"] == "Active").sum()) if len(df) > 0 else 0,
        "business_units": sorted(df["business_unit"].unique().tolist()) if len(df) > 0 else [],
    }


def load_itd(session_state: dict, wbs_elements: list) -> dict:
    """Load ITD costs from SAP extract for specified WBS elements."""
    df = data_loader.load_itd()
    filtered = df[df["wbs_element"].isin(wbs_elements)]
    session_state["itd_data"] = filtered
    matched_wbs = set(filtered["wbs_element"])
    requested_wbs = set(wbs_elements)
    return {
        "itd_records": filtered.to_dict(orient="records"),
        "matched_count": len(filtered),
        "total_requested": len(wbs_elements),
        "unmatched": sorted(requested_wbs - matched_wbs),
        "zero_itd": sorted(filtered[filtered["itd_amount"] == 0]["wbs_element"].tolist()),
    }


def load_vow(session_state: dict, wbs_elements: list) -> dict:
    """Load VOW estimates for specified WBS elements."""
    df = data_loader.load_vow()
    filtered = df[df["wbs_element"].isin(wbs_elements)]
    session_state["vow_data"] = filtered
    matched_wbs = set(filtered["wbs_element"])
    requested_wbs = set(wbs_elements)
    return {
        "vow_records": filtered.to_dict(orient="records"),
        "matched_count": len(filtered),
        "total_requested": len(wbs_elements),
        "unmatched": sorted(requested_wbs - matched_wbs),
    }


# ---------------------------------------------------------------------------
# Severity ranking (for picking worst severity when a WBS has multiple)
# ---------------------------------------------------------------------------

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _worst_severity(severities: list) -> str:
    """Return the worst (highest-priority) severity from a list."""
    if not severities:
        return ""
    return min(severities, key=lambda s: _SEVERITY_RANK.get(s, 99))


# ---------------------------------------------------------------------------
# Exception detail/action templates
# ---------------------------------------------------------------------------

_EXCEPTION_TEMPLATES = {
    "Negative Accrual": {
        "detail": "ITD ({itd}) exceeds VOW ({vow}) — possible over-invoice or stale VOW estimate.",
        "recommended_action": "Verify ITD charges with AP and request updated VOW from engineer.",
    },
    "Missing ITD": {
        "detail": "No ITD postings found in SAP extract for this WBS element.",
        "recommended_action": "Confirm whether work has started; if yes, investigate missing cost postings.",
    },
    "Missing VOW": {
        "detail": "WBS is in the master list but has no VOW estimate from engineering.",
        "recommended_action": "Request VOW submission from the responsible engineer.",
    },
    "Large Swing": {
        "detail": "Accrual changed by {pct}% vs prior period (current: {current}, prior: {prior}).",
        "recommended_action": "Validate the VOW estimate with the engineer and review ITD for unusual postings.",
    },
    "Zero ITD": {
        "detail": "ITD amount is $0 despite having an active VOW — work may not have started or costs not yet posted.",
        "recommended_action": "Verify project start date and check for unposted invoices.",
    },
}


def calculate_accruals(session_state: dict, missing_itd_handling: str) -> dict:
    """Calculate gross accruals (VOW - ITD) for each WBS element.

    Args:
        session_state: Dict containing wbs_data, itd_data, vow_data from prior loads.
        missing_itd_handling: How to handle WBS with VOW but no ITD.
            - "use_vow_as_accrual": treat ITD as $0, accrual = full VOW
            - "exclude_and_flag": exclude from calculation, set gross_accrual=None
            - "use_prior_period": use prior period accrual; fallback to exclude

    Returns:
        dict with "accruals", "summary", and "exceptions" keys.
    """
    for key in ("wbs_data", "itd_data", "vow_data"):
        if key not in session_state:
            return {"error": f"Required data not loaded. Missing: {key}"}

    wbs_df = session_state["wbs_data"].copy()
    itd_df = session_state["itd_data"].copy()
    vow_df = session_state["vow_data"].copy()
    prior_df = data_loader.load_prior_accruals()

    # ----- Build merged dataframe (left join from wbs_master) -----
    merged = wbs_df[["wbs_element", "well_name", "project_type", "business_unit", "status"]].copy()
    merged = merged.merge(
        vow_df[["wbs_element", "vow_amount"]], on="wbs_element", how="left"
    )
    merged = merged.merge(
        itd_df[["wbs_element", "itd_amount"]], on="wbs_element", how="left"
    )
    merged = merged.merge(
        prior_df[["wbs_element", "prior_gross_accrual"]], on="wbs_element", how="left"
    )

    # ----- Per-row calculation + exception detection -----
    accruals = []
    exceptions = []

    for _, row in merged.iterrows():
        wbs = row["wbs_element"]
        well_name = row["well_name"]
        vow = row["vow_amount"] if pd.notna(row["vow_amount"]) else None
        itd = row["itd_amount"] if pd.notna(row["itd_amount"]) else None
        prior = row["prior_gross_accrual"] if pd.notna(row["prior_gross_accrual"]) else None

        row_exceptions = []  # list of (type, severity) tuples
        gross_accrual = None

        # --- Flag Missing ITD (WBS has VOW but absent from ITD extract) ---
        if itd is None and vow is not None:
            row_exceptions.append(("Missing ITD", "HIGH"))

        # --- Flag Missing VOW (any WBS absent from VOW estimates) ---
        if vow is None:
            row_exceptions.append(("Missing VOW", "MEDIUM"))

        # --- Determine gross_accrual ---
        if vow is None:
            # Cannot calculate without VOW
            gross_accrual = None
        elif itd is None:
            # Has VOW but missing ITD — apply handling strategy
            if missing_itd_handling == "use_vow_as_accrual":
                itd = 0
                gross_accrual = vow
            elif missing_itd_handling == "use_prior_period":
                if prior is not None:
                    gross_accrual = prior
                else:
                    gross_accrual = None  # fallback to exclude
            else:
                # "exclude_and_flag" or unknown
                gross_accrual = None
        else:
            # Normal case: both VOW and ITD present
            gross_accrual = vow - itd

        # --- Additional exception checks (only when we have values) ---

        # Negative Accrual
        if gross_accrual is not None and gross_accrual < 0:
            row_exceptions.append(("Negative Accrual", "HIGH"))

        # Zero ITD (itd_amount == 0 and has VOW)
        if itd is not None and itd == 0 and vow is not None:
            row_exceptions.append(("Zero ITD", "LOW"))

        # Net change and pct change
        net_change = None
        pct_change = None
        if gross_accrual is not None and prior is not None:
            net_change = gross_accrual - prior
            if prior != 0:
                pct_change = net_change / prior

        # Large Swing (|pct_change| > 0.25, skip if prior is None or 0)
        if pct_change is not None and abs(pct_change) > 0.25:
            row_exceptions.append(("Large Swing", "MEDIUM"))

        # --- Build exception type / severity strings ---
        exc_types = [t for t, _ in row_exceptions]
        exc_sevs = [s for _, s in row_exceptions]
        exception_type_str = ", ".join(exc_types) if exc_types else ""
        exception_severity_str = _worst_severity(exc_sevs) if exc_sevs else ""

        accruals.append({
            "wbs_element": wbs,
            "well_name": well_name,
            "vow_amount": vow,
            "itd_amount": itd,
            "gross_accrual": gross_accrual,
            "prior_accrual": prior,
            "net_change": net_change,
            "pct_change": pct_change,
            "exception_type": exception_type_str,
            "exception_severity": exception_severity_str,
        })

        # --- Build per-exception records ---
        for exc_type, exc_sev in row_exceptions:
            tmpl = _EXCEPTION_TEMPLATES[exc_type]
            detail = tmpl["detail"].format(
                itd=itd, vow=vow,
                pct=round(pct_change * 100, 1) if pct_change is not None else "N/A",
                current=gross_accrual, prior=prior,
            )
            exceptions.append({
                "wbs_element": wbs,
                "well_name": well_name,
                "exception_type": exc_type,
                "severity": exc_sev,
                "detail": detail,
                "recommended_action": tmpl["recommended_action"],
                "vow_amount": vow,
                "itd_amount": itd,
                "accrual_amount": gross_accrual,
            })

    # ----- Summary -----
    calculated = [a for a in accruals if a["gross_accrual"] is not None]
    total_gross = sum(a["gross_accrual"] for a in calculated)

    prior_totals = [a["prior_accrual"] for a in calculated if a["prior_accrual"] is not None]
    prior_period_total = sum(prior_totals) if prior_totals else 0

    net_changes = [a["net_change"] for a in calculated if a["net_change"] is not None]
    net_change_total = sum(net_changes) if net_changes else 0

    pct_change_total = (
        net_change_total / prior_period_total
        if prior_period_total and prior_period_total != 0
        else None
    )

    summary = {
        "total_gross_accrual": total_gross,
        "total_wbs_count": len(accruals),
        "calculated_count": len(calculated),
        "exception_count": len(exceptions),
        "prior_period_total": prior_period_total,
        "net_change_total": net_change_total,
        "pct_change_total": pct_change_total,
    }

    # ----- Store in session state -----
    session_state["accrual_results"] = accruals
    session_state["exceptions"] = exceptions

    return {
        "accruals": accruals,
        "summary": summary,
        "exceptions": exceptions,
    }


def get_exceptions(session_state: dict, severity: str) -> dict:
    """Retrieve exception report from the most recent accrual calculation.

    Args:
        session_state: Dict containing "exceptions" from calculate_accruals.
        severity: Filter level — "all", "high", "medium", or "low".

    Returns:
        dict with "exceptions", "count", "by_type", "by_severity" keys.
    """
    all_exceptions = session_state.get("exceptions", [])

    if severity.lower() == "all":
        filtered = all_exceptions
    else:
        filtered = [e for e in all_exceptions if e["severity"] == severity.upper()]

    by_type: dict = {}
    by_severity: dict = {}
    for exc in filtered:
        by_type[exc["exception_type"]] = by_type.get(exc["exception_type"], 0) + 1
        by_severity[exc["severity"]] = by_severity.get(exc["severity"], 0) + 1

    return {
        "exceptions": filtered,
        "count": len(filtered),
        "by_type": by_type,
        "by_severity": by_severity,
    }


def get_accrual_detail(session_state: dict, wbs_element: str) -> dict:
    """Get detailed accrual information for a specific WBS element.

    Args:
        session_state: Dict containing loaded data and accrual results.
        wbs_element: The WBS element ID to look up.

    Returns:
        dict with merged WBS master info, VOW info, ITD info, accrual result,
        and exceptions for that WBS. Returns {"error": "..."} if not found.
    """
    # --- WBS master lookup ---
    wbs_df = session_state.get("wbs_data")
    if wbs_df is None or wbs_element not in wbs_df["wbs_element"].values:
        return {"error": f"WBS element {wbs_element} not found"}

    wbs_row = wbs_df[wbs_df["wbs_element"] == wbs_element].iloc[0]

    result = {
        "wbs_element": wbs_element,
        "well_name": wbs_row["well_name"],
        "project_type": wbs_row["project_type"],
        "business_unit": wbs_row["business_unit"],
        "status": wbs_row["status"],
        "budget_amount": float(wbs_row["budget_amount"]),
    }

    # --- VOW info ---
    vow_df = session_state.get("vow_data")
    if vow_df is not None and wbs_element in vow_df["wbs_element"].values:
        vow_row = vow_df[vow_df["wbs_element"] == wbs_element].iloc[0]
        result["vow_amount"] = float(vow_row["vow_amount"])
        result["phase"] = vow_row["phase"]
        result["pct_complete"] = float(vow_row["pct_complete"])
        result["engineer_name"] = vow_row["engineer_name"]
    else:
        result["vow_amount"] = None
        result["phase"] = None
        result["pct_complete"] = None
        result["engineer_name"] = None

    # --- ITD info ---
    itd_df = session_state.get("itd_data")
    if itd_df is not None and wbs_element in itd_df["wbs_element"].values:
        itd_row = itd_df[itd_df["wbs_element"] == wbs_element].iloc[0]
        result["itd_amount"] = float(itd_row["itd_amount"])
        result["last_posting_date"] = itd_row["last_posting_date"]
    else:
        result["itd_amount"] = None
        result["last_posting_date"] = None

    # --- Accrual result ---
    accrual_results = session_state.get("accrual_results", [])
    accrual_rec = [a for a in accrual_results if a["wbs_element"] == wbs_element]
    if accrual_rec:
        rec = accrual_rec[0]
        result["gross_accrual"] = rec["gross_accrual"]
        result["prior_accrual"] = rec["prior_accrual"]
        result["net_change"] = rec["net_change"]
        result["pct_change"] = rec["pct_change"]
    else:
        result["gross_accrual"] = None
        result["prior_accrual"] = None
        result["net_change"] = None
        result["pct_change"] = None

    # --- Exceptions for this WBS ---
    all_exceptions = session_state.get("exceptions", [])
    result["exceptions"] = [e for e in all_exceptions if e["wbs_element"] == wbs_element]

    return result


# ===================================================================
# 9. GENERATE NET-DOWN ENTRY
# ===================================================================


def generate_net_down_entry(session_state: dict) -> dict:
    """Generate the monthly net-down journal entry from accrual results.

    Reads session_state["accrual_results"] (list of accrual dicts from
    calculate_accruals). For each WBS with gross_accrual not None:
    net_change = gross_accrual - (prior_accrual or 0).
    Sum to get total_current, total_prior, net_down = total_current - total_prior.

    Returns:
        dict with "journal_entry", "detail", and "summary_text" keys.
    """
    accrual_results = session_state.get("accrual_results", [])

    detail = []
    total_current = 0.0
    total_prior = 0.0

    for rec in accrual_results:
        if rec["gross_accrual"] is None:
            continue
        current = rec["gross_accrual"]
        prior = rec["prior_accrual"] if rec["prior_accrual"] is not None else 0
        net_change = current - prior
        total_current += current
        total_prior += prior
        detail.append({
            "wbs_element": rec["wbs_element"],
            "well_name": rec["well_name"],
            "current_accrual": current,
            "prior_accrual": prior,
            "net_change": net_change,
        })

    net_down = total_current - total_prior

    if net_down >= 0:
        debit_account = "1410-000 (CapEx WIP)"
        credit_account = "2110-000 (Accrued Liabilities)"
    else:
        debit_account = "2110-000 (Accrued Liabilities)"
        credit_account = "1410-000 (CapEx WIP)"

    journal_entry = {
        "period": "2026-01",
        "description": "Monthly CapEx gross accrual net-down",
        "debit_account": debit_account,
        "credit_account": credit_account,
        "total_current_accrual": total_current,
        "total_prior_accrual": total_prior,
        "net_down_amount": net_down,
    }

    summary_text = (
        f"Net-down journal entry for 2026-01: "
        f"Current accrual {format_dollar(total_current)}, "
        f"Prior period {format_dollar(total_prior)}, "
        f"Net-down {format_dollar(net_down)}. "
        f"Debit {debit_account}, Credit {credit_account}."
    )

    return {
        "journal_entry": journal_entry,
        "detail": detail,
        "summary_text": summary_text,
    }


# ===================================================================
# 10. GET SUMMARY
# ===================================================================


def get_summary(session_state: dict, group_by: str) -> dict:
    """Summarize accrual results grouped by a dimension.

    Args:
        session_state: Dict containing "accrual_results" from calculate_accruals.
        group_by: Dimension to group by — "project_type", "business_unit", or "phase".

    Returns:
        dict with "summary" (list of group dicts) and "grand_total" keys.
    """
    accrual_results = session_state.get("accrual_results", [])

    # Build lookup dicts for grouping dimensions
    wbs_df = session_state.get("wbs_data")
    vow_df = session_state.get("vow_data")

    wbs_lookup = {}
    if wbs_df is not None:
        for _, row in wbs_df.iterrows():
            wbs_lookup[row["wbs_element"]] = {
                "project_type": row["project_type"],
                "business_unit": row["business_unit"],
            }

    vow_lookup = {}
    if vow_df is not None:
        for _, row in vow_df.iterrows():
            vow_lookup[row["wbs_element"]] = {"phase": row["phase"]}

    # Group accrual results
    groups: dict = {}
    grand_total = 0.0

    for rec in accrual_results:
        if rec["gross_accrual"] is None:
            continue

        wbs = rec["wbs_element"]
        accrual = rec["gross_accrual"]
        has_exception = 1 if rec["exception_type"] else 0

        # Determine group value
        if group_by == "phase":
            info = vow_lookup.get(wbs, {})
            group_value = info.get("phase", "Unknown")
        else:
            info = wbs_lookup.get(wbs, {})
            group_value = info.get(group_by, "Unknown")

        if group_value not in groups:
            groups[group_value] = {
                "total_accrual": 0.0,
                "wbs_count": 0,
                "exception_count": 0,
            }

        groups[group_value]["total_accrual"] += accrual
        groups[group_value]["wbs_count"] += 1
        groups[group_value]["exception_count"] += has_exception
        grand_total += accrual

    # Build summary list with pct_of_total
    summary = []
    for group_value, data in sorted(groups.items()):
        pct = data["total_accrual"] / grand_total if grand_total != 0 else 0
        summary.append({
            "group_value": group_value,
            "total_accrual": data["total_accrual"],
            "wbs_count": data["wbs_count"],
            "avg_accrual": data["total_accrual"] / data["wbs_count"] if data["wbs_count"] > 0 else 0,
            "exception_count": data["exception_count"],
            "pct_of_total": round(pct, 4),
        })

    return {
        "summary": summary,
        "grand_total": grand_total,
    }


# ===================================================================
# 11. GENERATE OUTLOOK — Linear by Day allocation
# ===================================================================


def _allocate_linear(phase_start: date, phase_end: date, total_cost: float,
                     month_start: date, month_end: date) -> float:
    """Allocate cost linearly across days, returning the portion in the given month.

    Args:
        phase_start: Start date of the phase.
        phase_end: End date of the phase.
        total_cost: Total cost for the phase.
        month_start: First day of the target month.
        month_end: Last day of the target month.

    Returns:
        The allocated cost for the overlap period, rounded to 2 decimal places.
    """
    if phase_end < month_start or phase_start > month_end:
        return 0.0
    total_days = (phase_end - phase_start).days + 1
    if total_days <= 0:
        return 0.0
    overlap_start = max(phase_start, month_start)
    overlap_end = min(phase_end, month_end)
    overlap_days = (overlap_end - overlap_start).days + 1
    if overlap_days <= 0:
        return 0.0
    return round(total_cost / total_days * overlap_days, 2)


def generate_outlook(session_state: dict, months_forward: int) -> dict:
    """Generate a forward-looking accrual outlook using linear-by-day allocation.

    Uses the drill_schedule.csv to project future accruals based on planned
    phase dates and estimated costs. Reference date is hardcoded to 2026-01.

    Args:
        session_state: Session state dict (used for consistency; schedule is
            loaded directly from CSV).
        months_forward: Number of months to project forward from 2026-02.

    Returns:
        dict with "outlook", "total_outlook", "wells_in_schedule",
        and "schedule_detail" keys.
    """
    schedule_df = data_loader.load_drill_schedule()

    # --- Load WBS master for well names ---
    wbs_df = session_state.get("wbs_data")
    wbs_name_lookup = {}
    if wbs_df is not None:
        for _, row in wbs_df.iterrows():
            wbs_name_lookup[row["wbs_element"]] = row["well_name"]

    # --- Build schedule detail ---
    schedule_detail = []
    for _, row in schedule_df.iterrows():
        schedule_detail.append({
            "wbs_element": row["wbs_element"],
            "well_name": wbs_name_lookup.get(row["wbs_element"], "Unknown"),
            "planned_phase": row["planned_phase"],
            "planned_date": str(row["planned_date"].date()) if hasattr(row["planned_date"], "date") else str(row["planned_date"]),
            "estimated_cost": float(row["estimated_cost"]),
        })

    wells_in_schedule = len(schedule_df["wbs_element"].unique())

    # --- Build phase spans per well ---
    # Group schedule by wbs_element
    well_phases = {}
    for _, row in schedule_df.iterrows():
        wbs = row["wbs_element"]
        phase = row["planned_phase"]
        pdate = row["planned_date"].date() if hasattr(row["planned_date"], "date") else row["planned_date"]
        cost = float(row["estimated_cost"])
        if wbs not in well_phases:
            well_phases[wbs] = {}
        well_phases[wbs][phase] = {"date": pdate, "cost": cost}

    # Build allocatable spans:
    # - Drilling: Spud → TD, cost = TD's estimated_cost
    # - Completions: Frac Start → Frac End, cost = Frac End's estimated_cost
    # - First Production: lump sum on that date (single day)
    spans = []
    for wbs, phases in well_phases.items():
        # Drilling phase: Spud to TD
        if "Spud" in phases and "TD" in phases:
            spans.append({
                "wbs": wbs,
                "phase_name": "Drilling",
                "start": phases["Spud"]["date"],
                "end": phases["TD"]["date"],
                "cost": phases["TD"]["cost"],
            })
        # Completions phase: Frac Start to Frac End
        if "Frac Start" in phases and "Frac End" in phases:
            spans.append({
                "wbs": wbs,
                "phase_name": "Completions",
                "start": phases["Frac Start"]["date"],
                "end": phases["Frac End"]["date"],
                "cost": phases["Frac End"]["cost"],
            })
        # First Production: single day lump sum
        if "First Production" in phases:
            fp = phases["First Production"]
            spans.append({
                "wbs": wbs,
                "phase_name": "First Production",
                "start": fp["date"],
                "end": fp["date"],
                "cost": fp["cost"],
            })

    # --- Build future months ---
    # Start from February 2026 (month after REFERENCE_DATE)
    future_months = []
    for i in range(months_forward):
        # month offset: 0 → Feb 2026, 1 → Mar 2026, etc.
        year = 2026
        month = 2 + i
        while month > 12:
            month -= 12
            year += 1
        future_months.append((year, month))

    # --- Allocate costs per month ---
    outlook = []
    total_outlook = 0.0

    for year, month in future_months:
        month_start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        month_end = date(year, month, last_day)
        month_label = f"{year}-{month:02d}"

        month_accrual = 0.0
        active_wells = set()
        new_wells = set()
        completing_phases = 0

        for span in spans:
            allocated = _allocate_linear(
                span["start"], span["end"], span["cost"],
                month_start, month_end,
            )
            if allocated > 0:
                month_accrual += allocated
                active_wells.add(span["wbs"])
                # A well is "new" if its first phase starts in this month
                if span["start"] >= month_start and span["start"] <= month_end:
                    new_wells.add(span["wbs"])
                # A phase completes if its end date falls in this month
                if span["end"] >= month_start and span["end"] <= month_end:
                    completing_phases += 1

        month_accrual = round(month_accrual, 2)
        total_outlook += month_accrual

        outlook.append({
            "month": month_label,
            "expected_accrual": month_accrual,
            "well_count": len(active_wells),
            "new_wells_starting": len(new_wells),
            "phases_completing": completing_phases,
        })

    total_outlook = round(total_outlook, 2)

    return {
        "outlook": outlook,
        "total_outlook": total_outlook,
        "wells_in_schedule": wells_in_schedule,
        "schedule_detail": schedule_detail,
    }
