"""Agent tools for the 3-step capex close process."""

import sys
from datetime import date, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd

from utils.data_loader import load_wbs_master, load_drill_schedule

COST_CATEGORIES = ["drill", "comp", "fb", "hu"]

CATEGORY_LABELS = {
    "drill": "Drilling",
    "comp": "Completions",
    "fb": "Flowback",
    "hu": "Hookup",
}

CATEGORY_ALLOCATION = {
    "drill": "linear",
    "comp": "linear",
    "fb": "linear",
    "hu": "lump_sum",
}

CATEGORY_PHASE_MAP = {
    "drill": ("Spud", "TD"),
    "comp": ("Frac Start", "Frac End"),
    "fb": ("Frac End", "First Production"),
    "hu": ("First Production", "First Production"),
}

REFERENCE_DATE = date(2026, 1, 1)


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
            total_system_cost += row[f"{cat}_vow"]

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


# ---------------------------------------------------------------------------
# OneStream load file helpers
# ---------------------------------------------------------------------------

def _get_months_forward(n_months: int = 6) -> list:
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


def _allocate_linear(total: float, start_date, end_date, months: list) -> dict:
    """Allocate total linearly by day across months."""
    if total <= 0 or start_date >= end_date:
        return {m: 0.0 for m in months}

    total_days = (end_date - start_date).days + 1
    daily_rate = total / total_days
    allocation = {m: 0.0 for m in months}

    for m_label in months:
        m_date = pd.to_datetime(f"01-{m_label}", format="%d-%b-%y")
        m_start = m_date.date()
        if m_date.month == 12:
            m_end = date(m_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(m_date.year, m_date.month + 1, 1) - timedelta(days=1)

        overlap_start = max(start_date, m_start)
        overlap_end = min(end_date, m_end)
        if overlap_start <= overlap_end:
            days_in_month = (overlap_end - overlap_start).days + 1
            allocation[m_label] = round(daily_rate * days_in_month, 2)

    return allocation


def _allocate_lump_sum(total: float, target_date, months: list) -> dict:
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
        pd_date = sr["planned_date"]
        sched_lookup[wbs][sr["planned_phase"]] = (
            pd_date.date() if hasattr(pd_date, "date") else pd_date
        )

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
                    allocation = {m: 0.0 for m in months}
            else:  # lump_sum
                target = phases.get(end_phase)
                if target:
                    allocation = _allocate_lump_sum(future, target, months)
                else:
                    allocation = {m: 0.0 for m in months}

            # If phase falls outside the month window, spread evenly
            if future > 0 and all(v == 0.0 for v in allocation.values()):
                per_month = round(future / len(months), 2)
                allocation = {m: per_month for m in months}

            rec = {
                "well_name": row["well_name"],
                "wbs_element": wbs,
                "cost_category": label,
            }
            rec.update(allocation)
            rec["total"] = round(sum(allocation.values()), 2)
            rows.append(rec)

    load_df = pd.DataFrame(rows)
    return {"load_file": load_df, "months": months}
