from typing import Sequence

import pandas as pd


def build_threshold_df(base_price: float, percentages: Sequence[int]) -> pd.DataFrame:
    records = []
    for pct in percentages:
        multiplier = round(1 + pct / 100, 2)
        target = round(base_price * multiplier, 2)
        change = round(target - base_price, 2)
        records.append({
            "Percentage (%)": pct,
            "Multiplier": multiplier,
            "Price Change ($)": change,
            "Target Price ($)": target,
        })
    return pd.DataFrame(records)
