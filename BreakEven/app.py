"""
The Break-Even Matrix — Application entry point.
Thin orchestrator: wires together core logic and UI components.
"""

import streamlit as st

from core.calculator import compute_price_tiers
from core.export import combined_csv, tiers_to_dataframe
from ui import sidebar, charts, position_repair, theme


# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Break-Even Matrix",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.inject_css()

st.title("📊 The Break-Even Matrix")
st.caption("Visualize price targets · Calculate average-down capital · Export your data")
st.divider()


# ─── Sidebar ────────────────────────────────────────────────────────────────────
ctx = sidebar.render()

if ctx.base_price is None or ctx.base_price <= 0:
    st.info("👈 Enter a ticker symbol or a manual base price in the sidebar to begin.")
    st.stop()


# ─── Feature 1: Price Tiers & Chart ────────────────────────────────────────────
st.header("📈 Price Tier Table")

tiers = compute_price_tiers(ctx.base_price)
tier_df = tiers_to_dataframe(tiers)

col_table, col_chart = st.columns([1, 2])
with col_table:
    charts.render_tier_table(tier_df)
with col_chart:
    charts.render_price_chart(tier_df, ctx.base_price, ctx.ticker_name)

st.download_button(
    label="⬇️  Download Price Tiers CSV",
    data=tier_df.to_csv(index=False),
    file_name=f"price_tiers_{ctx.ticker_name}.csv",
    mime="text/csv",
)

st.divider()


# ─── Feature 2: Position Repair ────────────────────────────────────────────────
avg_df, errors = position_repair.render(ctx.ticker_name)

st.divider()


# ─── Feature 3: Combined Export ─────────────────────────────────────────────────
st.subheader("📦 Export All Data")
st.download_button(
    label="⬇️  Download Combined CSV",
    data=combined_csv(tier_df, avg_df),
    file_name=f"break_even_matrix_{ctx.ticker_name}.csv",
    mime="text/csv",
    key="combined_csv",
)

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("The Break-Even Matrix · Built with Streamlit & Plotly · For educational purposes only.")
