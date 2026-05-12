from typing import Sequence

import pandas as pd


def build_threshold_df(
    base_price: float,
    percentages: Sequence[int],
    custom_pct: float | None = None,
) -> pd.DataFrame:
    pct_set: list[float] = list(percentages)
    if custom_pct is not None and custom_pct not in pct_set:
        pct_set.append(custom_pct)
        pct_set.sort()

    records = []
    for pct in pct_set:
        multiplier = round(1 + pct / 100, 4)
        target = round(base_price * multiplier, 2)
        change = round(target - base_price, 2)
        is_custom = custom_pct is not None and pct == custom_pct
        records.append({
            "Percentage (%)": pct,
            "Multiplier": multiplier,
            "Price Change ($)": change,
            "Target Price ($)": target,
            "Tier": "Custom" if is_custom else ("Dip" if pct < 0 else "High" if pct > 0 else "Baseline"),
        })
    return pd.DataFrame(records)
