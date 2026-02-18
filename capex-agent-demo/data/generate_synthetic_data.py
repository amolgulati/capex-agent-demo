"""
Synthetic data generator for CapEx Gross Accrual Agent Demo (Phase 1).

Produces 5 deterministic CSV files:
    - wbs_master.csv          (50 rows)
    - itd_extract.csv         (47 rows)
    - vow_estimates.csv       (45 rows)
    - prior_period_accruals.csv (48 rows)
    - drill_schedule.csv      (60-80 rows)

Hardcoded exception records per PRD; seeded random for normal records.
"""

import os
import random
from pathlib import Path
from datetime import date, timedelta

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED = 42
DATA_DIR = Path(__file__).resolve().parent

ALL_WBS = [f"WBS-{i}" for i in range(1001, 1051)]  # 50 elements

# Exception WBS elements
MISSING_ITD_WBS = {"WBS-1031", "WBS-1038", "WBS-1044"}  # absent from itd_extract
ZERO_ITD_WBS = {"WBS-1047", "WBS-1048", "WBS-1049"}      # itd_amount = 0
MISSING_VOW_ONLY = {"WBS-1015", "WBS-1042"}               # absent from vow_estimates only
MISSING_VOW_ALL = MISSING_VOW_ONLY | MISSING_ITD_WBS      # 5 total absent from vow

NEGATIVE_ACCRUAL_WBS = "WBS-1027"  # ITD > VOW
LARGE_SWING_WBS = "WBS-1009"       # >30% swing vs prior

# Prior period missing (new wells)
MISSING_PRIOR_WBS = {"WBS-1049", "WBS-1050"}

# Well name prefixes
WELL_PREFIXES = [
    "Eagle Ford", "Wolfcamp", "Spraberry", "Bone Spring", "Niobrara",
    "Codell", "Sussex", "Shannon", "Turner", "Mowry",
    "Frontier", "Muddy", "Dakota", "Parkman", "Teapot",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_date(rng: random.Random, start: date, end: date) -> date:
    """Return a random date between start and end inclusive."""
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 1. wbs_master.csv — 50 rows
# ---------------------------------------------------------------------------

def generate_wbs_master(rng: random.Random) -> pd.DataFrame:
    """Generate wbs_master.csv with exactly 50 rows."""

    # Business unit distribution: 35 Permian, 10 DJ, 5 Powder River
    business_units = (
        ["Permian Basin"] * 35 +
        ["DJ Basin"] * 10 +
        ["Powder River"] * 5
    )
    rng.shuffle(business_units)

    # Status distribution: 40 Active, 7 Complete, 3 Suspended
    statuses = (
        ["Active"] * 40 +
        ["Complete"] * 7 +
        ["Suspended"] * 3
    )
    rng.shuffle(statuses)

    # Project types: ensure all 4 appear, rest random
    project_types_base = ["Drilling", "Completion", "Facilities", "Workover"]
    project_types = project_types_base[:4]  # first 4 guaranteed
    for _ in range(46):
        project_types.append(rng.choice(project_types_base))
    rng.shuffle(project_types)

    rows = []
    for i, wbs in enumerate(ALL_WBS):
        idx = i + 1001
        prefix = rng.choice(WELL_PREFIXES)
        well_name = f"{prefix} {idx}-{rng.randint(1, 20)}H"
        afe_number = f"AFE-{rng.randint(20000, 99999)}"
        budget = rng.randint(200, 1500) * 10_000  # $2M - $15M
        start_dt = _random_date(rng, date(2025, 1, 1), date(2026, 6, 30))

        rows.append({
            "wbs_element": wbs,
            "well_name": well_name,
            "project_type": project_types[i],
            "business_unit": business_units[i],
            "afe_number": afe_number,
            "status": statuses[i],
            "budget_amount": budget,
            "start_date": _format_date(start_dt),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. itd_extract.csv — 47 rows (3 missing WBS)
# ---------------------------------------------------------------------------

def generate_itd_extract(rng: random.Random, wbs_master: pd.DataFrame) -> pd.DataFrame:
    """Generate itd_extract.csv with exactly 47 rows."""

    budget_map = dict(zip(wbs_master["wbs_element"], wbs_master["budget_amount"]))
    cost_categories = ["Material", "Service", "Labor", "Equipment"]

    # WBS elements present: all except the 3 missing
    itd_wbs_list = [w for w in ALL_WBS if w not in MISSING_ITD_WBS]
    assert len(itd_wbs_list) == 47

    # Make sure all 4 cost categories appear - assign first 4 deterministically
    forced_categories = list(cost_categories)
    rng.shuffle(forced_categories)

    rows = []
    for i, wbs in enumerate(itd_wbs_list):
        budget = budget_map[wbs]
        last_post = _random_date(rng, date(2025, 6, 1), date(2026, 1, 15))

        if i < 4:
            cat = forced_categories[i]
        else:
            cat = rng.choice(cost_categories)

        vendor_count = rng.randint(1, 12)

        # Determine itd_amount
        if wbs in ZERO_ITD_WBS:
            itd_amount = 0
        elif wbs == NEGATIVE_ACCRUAL_WBS:
            itd_amount = 2_627_000
        elif wbs == LARGE_SWING_WBS:
            # current_accrual = vow - itd ~= 1,072,000
            # We'll set vow for WBS-1009 in vow generator, need itd here
            # vow_1009 will be itd_1009 + 1_072_000
            # Let's pick a reasonable itd for WBS-1009
            itd_amount = 3_500_000  # vow will be 4_572_000
        else:
            # Normal: ITD is 20-80% of budget, at least 10,000
            pct = rng.uniform(0.20, 0.80)
            itd_amount = max(10_000, int(budget * pct))

        rows.append({
            "wbs_element": wbs,
            "itd_amount": itd_amount,
            "last_posting_date": _format_date(last_post),
            "cost_category": cat,
            "vendor_count": vendor_count,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. vow_estimates.csv — 45 rows (5 missing WBS)
# ---------------------------------------------------------------------------

def generate_vow_estimates(
    rng: random.Random,
    wbs_master: pd.DataFrame,
    itd_extract: pd.DataFrame,
) -> pd.DataFrame:
    """Generate vow_estimates.csv with exactly 45 rows."""

    budget_map = dict(zip(wbs_master["wbs_element"], wbs_master["budget_amount"]))
    itd_map = dict(zip(itd_extract["wbs_element"], itd_extract["itd_amount"]))
    phases = ["Drilling", "Completion", "Flowback", "Equip"]
    engineers = [
        "J. Smith", "R. Patel", "M. Garcia", "A. Johnson", "K. Lee",
        "T. Williams", "S. Brown", "D. Martinez", "L. Chen", "P. Wilson",
    ]

    # WBS elements present: all except the 5 missing
    vow_wbs_list = [w for w in ALL_WBS if w not in MISSING_VOW_ALL]
    assert len(vow_wbs_list) == 45

    # Force all 4 phases to appear
    forced_phases = list(phases)
    rng.shuffle(forced_phases)

    rows = []
    for i, wbs in enumerate(vow_wbs_list):
        budget = budget_map[wbs]
        submission_dt = _random_date(rng, date(2025, 10, 1), date(2026, 1, 31))
        engineer = rng.choice(engineers)

        if i < 4:
            phase = forced_phases[i]
        else:
            phase = rng.choice(phases)

        pct_complete = round(rng.uniform(0.0, 100.0), 1)

        # Determine vow_amount
        if wbs == NEGATIVE_ACCRUAL_WBS:
            vow_amount = 2_500_000
        elif wbs == LARGE_SWING_WBS:
            # current_accrual = vow - itd = 1,072,000
            # itd for WBS-1009 = 3,500,000
            itd_1009 = itd_map.get(wbs, 3_500_000)
            vow_amount = itd_1009 + 1_072_000  # = 4,572,000
        else:
            # Normal: VOW is 60-100% of budget, but at least 100,000 and at most 15M
            itd = itd_map.get(wbs, 0)
            # VOW should generally be > ITD for positive accrual
            pct = rng.uniform(0.60, 1.00)
            vow_amount = int(budget * pct)
            # Ensure vow >= itd for normal wells (positive accrual)
            if itd > 0 and vow_amount < itd:
                vow_amount = itd + rng.randint(50_000, 500_000)
            vow_amount = max(100_000, min(15_000_000, vow_amount))

        rows.append({
            "wbs_element": wbs,
            "vow_amount": vow_amount,
            "submission_date": _format_date(submission_dt),
            "engineer_name": engineer,
            "phase": phase,
            "pct_complete": pct_complete,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. prior_period_accruals.csv — 48 rows
# ---------------------------------------------------------------------------

def generate_prior_period(
    rng: random.Random,
    itd_extract: pd.DataFrame,
    vow_estimates: pd.DataFrame,
) -> pd.DataFrame:
    """Generate prior_period_accruals.csv with exactly 48 rows."""

    itd_map = dict(zip(itd_extract["wbs_element"], itd_extract["itd_amount"]))
    vow_map = dict(zip(vow_estimates["wbs_element"], vow_estimates["vow_amount"]))

    # WBS elements present: all except the 2 new wells (WBS-1049, WBS-1050)
    prior_wbs_list = [w for w in ALL_WBS if w not in MISSING_PRIOR_WBS]
    assert len(prior_wbs_list) == 48

    rows = []
    for wbs in prior_wbs_list:
        if wbs == LARGE_SWING_WBS:
            prior_accrual = 800_000
        else:
            # Current accrual = vow - itd (if both exist), else just a reasonable value
            itd = itd_map.get(wbs, 0)
            vow = vow_map.get(wbs, 0)

            if vow > 0 and itd >= 0:
                current_accrual = vow - itd
            else:
                current_accrual = 0

            if current_accrual > 0:
                # Prior is within ~10-15% of current => swing < 30%
                factor = rng.uniform(0.90, 1.10)
                prior_accrual = max(0, int(current_accrual * factor))
            else:
                # For zero/negative current accrual, set a small prior
                prior_accrual = rng.randint(0, 100_000)

        rows.append({
            "wbs_element": wbs,
            "prior_gross_accrual": prior_accrual,
            "period": "2025-12",
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. drill_schedule.csv — 60-80 rows
# ---------------------------------------------------------------------------

def generate_drill_schedule(rng: random.Random, wbs_master: pd.DataFrame) -> pd.DataFrame:
    """Generate drill_schedule.csv with 60-80 rows, ~20 wells x 3-5 phases."""

    all_phases = ["Spud", "TD", "Frac Start", "Frac End", "First Production"]
    master_wbs = list(wbs_master["wbs_element"])

    # Select ~20 wells for the drill schedule
    drill_wells = rng.sample(master_wbs, 20)

    # We need all 5 phases to appear in the data.
    # Strategy: ensure at least one well has all 5 phases,
    # and vary others between 3-5 phases.
    # Also need total rows between 60 and 80.

    # First, plan how many phases each well gets
    phase_counts = []
    # First well: all 5 phases (guarantees all phases appear)
    phase_counts.append(5)
    # Remaining 19 wells: 3-4 phases to keep total in 60-80 range
    for _ in range(19):
        phase_counts.append(rng.choice([3, 3, 4, 4, 4]))

    total = sum(phase_counts)
    # Adjust if needed to be in 60-80 range
    # With 1*5 + 19*(avg 3.6) = 5 + 68.4 = ~73, should be fine

    rows = []
    for well_idx, wbs in enumerate(drill_wells):
        n_phases = phase_counts[well_idx]

        if n_phases == 5:
            selected_phases = all_phases[:]
        elif n_phases == 4:
            # Drop one of the later phases (not Spud, to keep variety)
            drop_idx = rng.choice([1, 2, 3, 4])
            selected_phases = [p for j, p in enumerate(all_phases) if j != drop_idx]
        else:  # 3
            # Pick 3 phases maintaining order
            indices = sorted(rng.sample(range(5), 3))
            selected_phases = [all_phases[j] for j in indices]

        # Generate strictly sequential dates
        base_date = _random_date(rng, date(2025, 3, 1), date(2026, 3, 1))
        phase_dates = [base_date]
        for _ in range(len(selected_phases) - 1):
            gap = rng.randint(15, 90)  # 15-90 days between phases
            phase_dates.append(phase_dates[-1] + timedelta(days=gap))

        for phase, dt in zip(selected_phases, phase_dates):
            cost = rng.randint(10, 550) * 10_000  # $100K - $5.5M
            rows.append({
                "wbs_element": wbs,
                "planned_phase": phase,
                "planned_date": _format_date(dt),
                "estimated_cost": cost,
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

    print("Generating itd_extract.csv ...")
    itd_extract = generate_itd_extract(rng, wbs_master)
    itd_extract.to_csv(DATA_DIR / "itd_extract.csv", index=False)
    print(f"  -> {len(itd_extract)} rows")

    print("Generating vow_estimates.csv ...")
    vow_estimates = generate_vow_estimates(rng, wbs_master, itd_extract)
    vow_estimates.to_csv(DATA_DIR / "vow_estimates.csv", index=False)
    print(f"  -> {len(vow_estimates)} rows")

    print("Generating prior_period_accruals.csv ...")
    prior_period = generate_prior_period(rng, itd_extract, vow_estimates)
    prior_period.to_csv(DATA_DIR / "prior_period_accruals.csv", index=False)
    print(f"  -> {len(prior_period)} rows")

    print("Generating drill_schedule.csv ...")
    drill_schedule = generate_drill_schedule(rng, wbs_master)
    drill_schedule.to_csv(DATA_DIR / "drill_schedule.csv", index=False)
    print(f"  -> {len(drill_schedule)} rows")

    print("\nAll 5 CSV files generated successfully!")


if __name__ == "__main__":
    main()
