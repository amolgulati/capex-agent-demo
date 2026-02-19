"""
Synthetic data generator for CapEx Close Agent Demo (v2).

Produces 2 deterministic CSV files:
    - wbs_master.csv      (18 rows, wide-table with per-category columns + WI%)
    - drill_schedule.csv  (18 wells x 5 phases = 90 rows)

Hardcoded exception records per design doc; seeded random for normal records.
"""

import random
from pathlib import Path
from datetime import date, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED = 42
DATA_DIR = Path(__file__).resolve().parent

ALL_WBS = [f"WBS-{i}" for i in range(1001, 1019)]  # 18 elements

COST_CATEGORIES = ["drill", "comp", "fb", "hu"]

# Exception wells
WI_MISMATCH_WELLS = {
    "WBS-1003": {"wi_pct": 0.75, "system_wi_pct": 0.80},  # moderate
    "WBS-1007": {"wi_pct": 0.60, "system_wi_pct": 0.85},  # large gap (25pp)
    "WBS-1011": {"wi_pct": 0.65, "system_wi_pct": 0.70},  # small
}
NEGATIVE_ACCRUAL_WELL = "WBS-1005"
LARGE_SWING_WELL = "WBS-1009"
OVER_BUDGET_WELL = "WBS-1015"

# Well name prefixes
WELL_PREFIXES = [
    "Eagle Ford", "Wolfcamp", "Spraberry", "Bone Spring", "Niobrara",
    "Codell", "Sussex", "Shannon", "Turner", "Mowry",
    "Frontier", "Muddy", "Dakota", "Parkman", "Teapot",
]

# Business unit distribution: ~12 Permian, ~4 DJ, ~2 Powder River
BU_ASSIGNMENT = {
    "WBS-1001": "Permian Basin",
    "WBS-1002": "Permian Basin",
    "WBS-1003": "Permian Basin",
    "WBS-1004": "DJ Basin",
    "WBS-1005": "Permian Basin",
    "WBS-1006": "Permian Basin",
    "WBS-1007": "Permian Basin",
    "WBS-1008": "DJ Basin",
    "WBS-1009": "Permian Basin",
    "WBS-1010": "Permian Basin",
    "WBS-1011": "Permian Basin",
    "WBS-1012": "DJ Basin",
    "WBS-1013": "Permian Basin",
    "WBS-1014": "Permian Basin",
    "WBS-1015": "Powder River",
    "WBS-1016": "DJ Basin",
    "WBS-1017": "Powder River",
    "WBS-1018": "Permian Basin",
}

DEFAULT_WI = 0.75  # default WI% for non-exception wells


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_date(rng: random.Random, start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 1. wbs_master.csv — 18 rows, wide-table
# ---------------------------------------------------------------------------

def generate_wbs_master(rng: random.Random) -> pd.DataFrame:
    """Generate wide-table wbs_master.csv with 18 rows.

    Columns: wbs_element, well_name, afe_number, business_unit, status,
    start_date, wi_pct, system_wi_pct,
    {drill,comp,fb,hu}_{budget,itd,vow,ops_budget},
    prior_gross_accrual
    """
    statuses = (
        ["Active"] * 14 + ["Complete"] * 3 + ["Suspended"] * 1
    )
    rng.shuffle(statuses)

    rows = []
    for i, wbs in enumerate(ALL_WBS):
        idx = i + 1001
        prefix = rng.choice(WELL_PREFIXES)
        well_name = f"{prefix} {idx}-{rng.randint(1, 20)}H"
        afe_number = f"AFE-{rng.randint(20000, 99999)}"
        bu = BU_ASSIGNMENT[wbs]
        status = statuses[i]
        start_dt = _random_date(rng, date(2025, 1, 1), date(2026, 6, 30))

        # WI% — defaults or exception
        if wbs in WI_MISMATCH_WELLS:
            wi_pct = WI_MISMATCH_WELLS[wbs]["wi_pct"]
            system_wi_pct = WI_MISMATCH_WELLS[wbs]["system_wi_pct"]
        else:
            wi_pct = DEFAULT_WI
            system_wi_pct = DEFAULT_WI

        row = {
            "wbs_element": wbs,
            "well_name": well_name,
            "afe_number": afe_number,
            "business_unit": bu,
            "status": status,
            "start_date": _format_date(start_dt),
            "wi_pct": wi_pct,
            "system_wi_pct": system_wi_pct,
        }

        # Per-category financials
        if wbs == NEGATIVE_ACCRUAL_WELL:
            row.update(_generate_negative_accrual_well(rng))
        elif wbs == LARGE_SWING_WELL:
            row.update(_generate_large_swing_well(rng))
        elif wbs == OVER_BUDGET_WELL:
            row.update(_generate_over_budget_well(rng))
        else:
            row.update(_generate_normal_well(rng))

        rows.append(row)

    return pd.DataFrame(rows)


def _generate_normal_well(rng: random.Random) -> dict:
    """Generate per-category financials for a normal well."""
    data = {}
    total_gross_accrual = 0

    for cat in COST_CATEGORIES:
        budget = rng.randint(100, 500) * 10_000  # $1M - $5M
        ops_budget = int(budget * rng.uniform(0.95, 1.10))
        itd = int(budget * rng.uniform(0.20, 0.70))
        vow = itd + rng.randint(50_000, 500_000)  # positive accrual

        data[f"{cat}_budget"] = budget
        data[f"{cat}_itd"] = itd
        data[f"{cat}_vow"] = vow
        data[f"{cat}_ops_budget"] = ops_budget

        total_gross_accrual += (vow - itd)

    # prior_gross_accrual: close to current (within ±10%) so swing < 25%
    factor = rng.uniform(0.90, 1.10)
    data["prior_gross_accrual"] = max(0, int(total_gross_accrual * factor))

    return data


def _generate_negative_accrual_well(rng: random.Random) -> dict:
    """WBS-1005: At least one category has ITD > VOW (negative accrual)."""
    data = {}
    total_gross_accrual = 0

    for cat in COST_CATEGORIES:
        budget = rng.randint(100, 500) * 10_000

        if cat == "drill":
            # Negative accrual: ITD > VOW (large gap to ensure total stays negative)
            itd = 4_500_000
            vow = 2_800_000
        else:
            itd = int(budget * rng.uniform(0.30, 0.50))
            vow = itd + rng.randint(50_000, 150_000)

        ops_budget = int(budget * rng.uniform(0.95, 1.10))

        data[f"{cat}_budget"] = budget
        data[f"{cat}_itd"] = itd
        data[f"{cat}_vow"] = vow
        data[f"{cat}_ops_budget"] = ops_budget

        total_gross_accrual += (vow - itd)

    data["prior_gross_accrual"] = max(0, int(abs(total_gross_accrual) * rng.uniform(0.8, 1.2)))

    return data


def _generate_large_swing_well(rng: random.Random) -> dict:
    """WBS-1009: Current accrual ~$1.07M vs prior ~$800K (+34% swing)."""
    data = {}
    # Target: total_gross_accrual ~= 1_070_000, prior = 800_000
    # Distribute across categories
    target_accruals = [400_000, 350_000, 200_000, 120_000]  # sum = 1_070_000

    for cat, target_accrual in zip(COST_CATEGORIES, target_accruals):
        budget = rng.randint(200, 400) * 10_000
        itd = int(budget * rng.uniform(0.30, 0.50))
        vow = itd + target_accrual
        ops_budget = int(budget * rng.uniform(0.95, 1.10))

        data[f"{cat}_budget"] = budget
        data[f"{cat}_itd"] = itd
        data[f"{cat}_vow"] = vow
        data[f"{cat}_ops_budget"] = ops_budget

    data["prior_gross_accrual"] = 800_000

    return data


def _generate_over_budget_well(rng: random.Random) -> dict:
    """WBS-1015: Total in-system (VOW * WI%) exceeds total ops_budget."""
    data = {}
    total_gross_accrual = 0

    for cat in COST_CATEGORIES:
        budget = rng.randint(200, 500) * 10_000
        itd = int(budget * rng.uniform(0.40, 0.60))
        vow = int(budget * rng.uniform(0.90, 1.15))
        # ops_budget must be < vow * wi_pct (0.75) so outlook goes negative
        ops_budget = int(vow * rng.uniform(0.55, 0.70))

        data[f"{cat}_budget"] = budget
        data[f"{cat}_itd"] = itd
        data[f"{cat}_vow"] = vow
        data[f"{cat}_ops_budget"] = ops_budget

        total_gross_accrual += (vow - itd)

    factor = rng.uniform(0.90, 1.10)
    data["prior_gross_accrual"] = max(0, int(total_gross_accrual * factor))

    return data


# ---------------------------------------------------------------------------
# 2. drill_schedule.csv — all 18 wells x 5 phases
# ---------------------------------------------------------------------------

def generate_drill_schedule(rng: random.Random, wbs_master: pd.DataFrame) -> pd.DataFrame:
    """Generate drill_schedule.csv with all 18 wells, each with all 5 phases."""
    all_phases = ["Spud", "TD", "Frac Start", "Frac End", "First Production"]

    rows = []
    for _, well in wbs_master.iterrows():
        wbs = well["wbs_element"]

        # Generate strictly sequential dates
        base_date = _random_date(rng, date(2025, 3, 1), date(2026, 6, 1))
        phase_dates = [base_date]
        for _ in range(len(all_phases) - 1):
            gap = rng.randint(15, 90)
            phase_dates.append(phase_dates[-1] + timedelta(days=gap))

        for phase, dt in zip(all_phases, phase_dates):
            rows.append({
                "wbs_element": wbs,
                "planned_phase": phase,
                "planned_date": _format_date(dt),
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rng = random.Random(SEED)

    print("Generating wbs_master.csv ...")
    wbs_master = generate_wbs_master(rng)
    wbs_master.to_csv(DATA_DIR / "wbs_master.csv", index=False)
    print(f"  -> {len(wbs_master)} rows")

    print("Generating drill_schedule.csv ...")
    drill_schedule = generate_drill_schedule(rng, wbs_master)
    drill_schedule.to_csv(DATA_DIR / "drill_schedule.csv", index=False)
    print(f"  -> {len(drill_schedule)} rows")

    print("\nAll CSV files generated successfully!")


if __name__ == "__main__":
    main()
