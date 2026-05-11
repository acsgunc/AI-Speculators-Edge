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

    col_buy, col_sell = st.columns(2)

    with col_buy:
        st.markdown("#### 🟢 Buy Targets (Dips)")
        st.dataframe(
            pd.DataFrame([
                {
                    "Dip %": row.pct_label,
                    "Price Change ($)": f"-${abs(row.change):,.2f}",
                    "Target Price ($)": f"${row.target:,.2f}",
                }
                for row in buy_targets
            ]),
            use_container_width=True,
            hide_index=True,
        )

    with col_sell:
        st.markdown("#### 🔴 Sell Targets (Gains)")
        st.dataframe(
            pd.DataFrame([
                {
                    "Gain %": row.pct_label,
                    "Price Change ($)": f"+${row.change:,.2f}",
                    "Target Price ($)": f"${row.target:,.2f}",
                }
                for row in sell_targets
            ]),
            use_container_width=True,
            hide_index=True,
        )
