"""Output formatting helpers for the CapEx Agent tools."""


def format_dollar(amount: float) -> str:
    """Format a dollar amount as $14.3M, $127.0K, or $500."""
    if amount == 0:
        return "$0"
    prefix = "-" if amount < 0 else ""
    abs_amt = abs(amount)
    if abs_amt >= 1_000_000:
        return f"{prefix}${abs_amt / 1_000_000:.1f}M"
    elif abs_amt >= 1_000:
        return f"{prefix}${abs_amt / 1_000:.1f}K"
    else:
        return f"{prefix}${abs_amt:.0f}"
