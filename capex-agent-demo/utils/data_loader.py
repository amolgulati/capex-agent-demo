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
