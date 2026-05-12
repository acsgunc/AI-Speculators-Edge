"""Data-export utilities — CSV / Excel serialisation."""

from __future__ import annotations

import io

import pandas as pd

from .models import AverageDownRow, PriceTier


def tiers_to_dataframe(tiers: list[PriceTier]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Percentage Change (%)": [t.percentage for t in tiers],
            "Target Price ($)": [t.target_price for t in tiers],
        }
    )


def avg_down_to_dataframe(rows: list[AverageDownRow]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Target Avg Price ($)": [f"{r.target_avg_price:,.2f}" for r in rows],
            "Units to Buy Now": [f"{r.units_to_buy:,.2f}" for r in rows],
            "Total Cost to Buy ($)": [f"{r.total_cost:,.2f}" for r in rows],
            "New Total Position Value ($)": [
                f"{r.new_position_value:,.2f}" for r in rows
            ],
        }
    )


def combined_csv(
    tier_df: pd.DataFrame,
    avg_df: pd.DataFrame | None = None,
) -> str:
    buf = io.StringIO()
    buf.write("=== PRICE TIERS ===\n")
    buf.write(tier_df.to_csv(index=False))
    if avg_df is not None:
        buf.write("\n=== AVERAGE DOWN ===\n")
        buf.write(avg_df.to_csv(index=False))
    return buf.getvalue()
