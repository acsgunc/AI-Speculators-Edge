from typing import Sequence

import pandas as pd


def build_threshold_df(base_price: float, percentages: Sequence[int]) -> pd.DataFrame:
    records = []
    for pct in percentages:
        target = round(base_price * (1 + pct / 100), 2)
        change = round(target - base_price, 2)
        records.append({
            "Percentage (%)": pct,
            "Price Change ($)": change,
            "Target Price ($)": target,
        })
    return pd.DataFrame(records)
