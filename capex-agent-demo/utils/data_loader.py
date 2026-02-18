"""
Data Loader Utilities for CapEx Gross Accrual Agent Demo.

Provides functions to load each of the five synthetic CSV files
from the data/ directory. These loaders will be consumed by the
agent tools in Phase 2.

Note: Streamlit caching decorators (@st.cache_data) will be added
in Phase 4 when the UI layer is integrated.
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Data directory — resolved relative to this module
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Loader functions
# ---------------------------------------------------------------------------


def load_wbs_master(business_unit: str = "all") -> pd.DataFrame:
    """Load WBS Master List, optionally filtered by business unit.

    Parameters
    ----------
    business_unit : str, default "all"
        If "all", return every row. Otherwise, filter rows where the
        ``business_unit`` column matches this value (case-sensitive).

    Returns
    -------
    pd.DataFrame
        The (possibly filtered) WBS master data. Returns an empty
        DataFrame if no rows match the given business unit.
    """
    df = pd.read_csv(DATA_DIR / "wbs_master.csv")
    if business_unit != "all":
        df = df[df["business_unit"] == business_unit]
    return df


def load_itd() -> pd.DataFrame:
    """Load ITD (Inception-To-Date) extract from SAP.

    Returns
    -------
    pd.DataFrame
        The ITD extract with columns: wbs_element, itd_amount,
        last_posting_date, cost_category, vendor_count.
    """
    return pd.read_csv(DATA_DIR / "itd_extract.csv")


def load_vow() -> pd.DataFrame:
    """Load VOW (Value of Work) estimates from engineers.

    Returns
    -------
    pd.DataFrame
        The VOW estimates with columns: wbs_element, vow_amount,
        submission_date, engineer_name, phase, pct_complete.
    """
    return pd.read_csv(DATA_DIR / "vow_estimates.csv")


def load_prior_accruals() -> pd.DataFrame:
    """Load prior period accruals.

    Returns
    -------
    pd.DataFrame
        The prior period accruals with columns: wbs_element,
        prior_gross_accrual, period.
    """
    return pd.read_csv(DATA_DIR / "prior_period_accruals.csv")


def load_drill_schedule() -> pd.DataFrame:
    """Load drill/frac schedule with parsed dates.

    The ``planned_date`` column is automatically parsed as datetime.

    Returns
    -------
    pd.DataFrame
        The drill schedule with columns: wbs_element, planned_phase,
        planned_date (datetime64), estimated_cost.
    """
    return pd.read_csv(
        DATA_DIR / "drill_schedule.csv",
        parse_dates=["planned_date"],
    )
