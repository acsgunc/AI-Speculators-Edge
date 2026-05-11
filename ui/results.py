import pandas as pd
import streamlit as st

from ui.inputs import FilterOptions


def _color_row(row: pd.Series) -> list[str]:
    pct = row["Percentage (%)"]
    if pct < 0:
        return ["background-color: #fdd; color: #b00"] * len(row)
    if pct > 0:
        return ["background-color: #dfd; color: #060"] * len(row)
    return ["background-color: #ffc; color: #333"] * len(row)


def render_results(
    base_price: float,
    source_label: str,
    df: pd.DataFrame,
    filters: FilterOptions,
) -> None:
    st.divider()
    st.subheader(f"Results — Base Price: **${base_price:,.2f}** ({source_label})")

    # --- Apply sidebar filters ---
    mask = pd.Series(True, index=df.index)
    if not filters.show_dips:
        mask &= df["Percentage (%)"] >= 0
    if not filters.show_highs:
        mask &= df["Percentage (%)"] <= 0
    filtered = df[mask].reset_index(drop=True)

    if filtered.empty:
        st.info("No rows match the current filters.")
        return

    # --- Highlight searched percentage ---
    if filters.search_pct is not None:
        match = filtered[filtered["Percentage (%)"] == filters.search_pct]
        if not match.empty:
            idx = match.index[0]
            st.success(f"Found **{filters.search_pct}%** → Target Price: **${match.iloc[0]['Target Price ($)']:,.2f}**")
        else:
            st.warning(f"{filters.search_pct}% is not in the current table. Try a multiple of 5 between -100 and 500.")

    # --- Display styled table ---
    styled = (
        filtered.style
        .apply(_color_row, axis=1)
        .format({
            "Price Change ($)": "${:,.2f}",
            "Target Price ($)": "${:,.2f}",
            "Percentage (%)": "{:+d}%",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=600)

    # --- Export ---
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="stock_thresholds.csv",
        mime="text/csv",
        use_container_width=True,
    )
