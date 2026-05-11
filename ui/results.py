import pandas as pd
import streamlit as st

from services.calculator import ThresholdRow


def render_results(
    base_price: float,
    source_label: str,
    buy_targets: list[ThresholdRow],
    sell_targets: list[ThresholdRow],
) -> None:
    st.divider()
    st.subheader(f"Results — Base Price: **${base_price:,.2f}** ({source_label})")

    rows = []
    for buy, sell in zip(buy_targets, sell_targets):
        rows.append({
            "Percentage": f"{abs(float(buy.pct_label.replace('%', '')))}%",
            "Dip Target ($)": f"${buy.target:,.2f}",
            "Dip Change ($)": f"-${abs(buy.change):,.2f}",
            "High Target ($)": f"${sell.target:,.2f}",
            "High Change ($)": f"+${sell.change:,.2f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
