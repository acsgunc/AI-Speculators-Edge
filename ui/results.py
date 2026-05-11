import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.inputs import FilterOptions


# ── Colour helpers ──────────────────────────────────────────

def _color_row(row: pd.Series) -> list[str]:
    tier = row.get("Tier", "")
    if tier == "Custom":
        return ["background-color: #e0d4fc; color: #4a0080"] * len(row)
    pct = row["Percentage (%)"]
    if pct < 0:
        return ["background-color: #fdd; color: #b00"] * len(row)
    if pct > 0:
        return ["background-color: #dfd; color: #060"] * len(row)
    return ["background-color: #ffc; color: #333"] * len(row)


_TIER_COLORS = {"Dip": "#d32f2f", "Baseline": "#fbc02d", "High": "#388e3c", "Custom": "#7b1fa2"}
_TIER_SYMBOLS = {"Dip": "triangle-down", "Baseline": "diamond", "High": "triangle-up", "Custom": "star"}


# ── Chart ───────────────────────────────────────────────────

def _render_chart(df: pd.DataFrame, base_price: float) -> None:
    fig = go.Figure()

    for tier, group in df.groupby("Tier", sort=False):
        fig.add_trace(go.Scatter(
            x=group["Percentage (%)"],
            y=group["Target Price ($)"],
            mode="lines+markers",
            name=str(tier),
            marker=dict(
                color=_TIER_COLORS.get(str(tier), "#999"),
                symbol=_TIER_SYMBOLS.get(str(tier), "circle"),
                size=8 if tier != "Custom" else 14,
            ),
            line=dict(color=_TIER_COLORS.get(str(tier), "#999"), width=2),
            hovertemplate=(
                "<b>%{x:+.1f}%</b><br>"
                "Target: $%{y:,.2f}<br>"
                f"Tier: {tier}"
                "<extra></extra>"
            ),
        ))

    # Anchor line at current price
    fig.add_hline(
        y=base_price,
        line_dash="dash",
        line_color="#1565c0",
        line_width=2,
        annotation_text=f"Current ${base_price:,.2f}",
        annotation_position="top left",
        annotation_font_color="#1565c0",
    )

    fig.update_layout(
        title="Price Target Curve",
        xaxis_title="Percentage Change (%)",
        yaxis_title="Stock Price ($)",
        template="plotly_white",
        height=500,
        legend_title="Tier",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


# ── Table + Export ──────────────────────────────────────────

def _render_table(df: pd.DataFrame) -> None:
    display_df = df.copy()

    fmt: dict = {
        "Multiplier": "{:.4f}x",
        "Price Change ($)": "${:,.2f}",
        "Target Price ($)": "${:,.2f}",
    }

    # Format percentage: int-like values without decimals, custom floats with 1 decimal
    def _fmt_pct(v: float) -> str:
        return f"{v:+.1f}%" if v != int(v) else f"{int(v):+d}%"

    styled = (
        display_df.style
        .apply(_color_row, axis=1)
        .format(fmt)
        .format({"Percentage (%)"}, formatter=_fmt_pct)
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=600)

    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="stock_thresholds.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ── Public entry point ──────────────────────────────────────

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
            st.success(
                f"Found **{filters.search_pct:+g}%** → "
                f"Target Price: **${match.iloc[0]['Target Price ($)']:,.2f}**"
            )
        else:
            st.warning(f"{filters.search_pct:+g}% is not in the current table.")

    # --- Chart then Table ---
    tab_chart, tab_table = st.tabs(["📊 Chart", "📋 Table"])

    with tab_chart:
        _render_chart(filtered, base_price)

    with tab_table:
        _render_table(filtered)
