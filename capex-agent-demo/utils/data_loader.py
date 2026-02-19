"""Data Loader for CapEx Close Agent Demo.

Two data sources:
- wbs_master.csv: Wide table with all financial data per well
- drill_schedule.csv: Phase dates for time-based outlook allocation

CSV reads are cached with functools.lru_cache so repeated tool calls
within a session don't re-read from disk.  We use lru_cache (not
@st.cache_data) because this module is also imported by CLI and tests.
Streamlit-specific caching is layered on in app.py where needed.
"""

from functools import lru_cache
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def _read_wbs_master() -> pd.DataFrame:
    """Read the raw CSV once and cache it."""
    return pd.read_csv(DATA_DIR / "wbs_master.csv")


def load_wbs_master(business_unit: str = "all") -> pd.DataFrame:
    """Load WBS Master, optionally filtered by business unit."""
    df = _read_wbs_master()
    if business_unit != "all":
        df = df[df["business_unit"] == business_unit]
    return df


@lru_cache(maxsize=1)
def load_drill_schedule() -> pd.DataFrame:
    """Load drill/frac schedule with parsed dates."""
    return pd.read_csv(
        DATA_DIR / "drill_schedule.csv",
        parse_dates=["planned_date"],
    )


def clear_caches():
    """Clear all data caches. Useful for testing or data refresh."""
    _read_wbs_master.cache_clear()
    load_drill_schedule.cache_clear()
