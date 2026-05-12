"""
The Break-Even Matrix
A professional Streamlit application for stock price target visualization
and average-down capital calculation.
"""

import io
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Break-Even Matrix",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #fafafa; }
    .success-text { color: #00d47e; font-weight: 600; }
    .danger-text  { color: #ff4b4b; font-weight: 600; }
    .anchor-row   { background-color: #1e293b; font-weight: 700; }
    .metric-card {
        background-color: #1a1f2e;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2d3748;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #00d4aa; }
    .metric-label { font-size: 14px; color: #a0aec0; margin-top: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 The Break-Even Matrix")
st.caption("Visualize price targets · Calculate average-down capital · Export your data")
st.divider()


# ─── Sidebar: Input Controls ───────────────────────────────────────────────────
st.sidebar.header("⚙️ Configuration")

input_mode = st.sidebar.radio(
    "Price Source",
    ["Stock Ticker (Live)", "Manual Base Price"],
    horizontal=True,
)

base_price: float | None = None
ticker_name = ""

if input_mode == "Stock Ticker (Live)":
    ticker_input = st.sidebar.text_input(
        "Ticker Symbol", value="AAPL", max_chars=10
    ).strip().upper()
    if ticker_input:
        with st.spinner(f"Fetching {ticker_input}…"):
            try:
                ticker_obj = yf.Ticker(ticker_input)
                hist = ticker_obj.history(period="1d")
                if hist.empty:
                    st.sidebar.error(f"No data found for '{ticker_input}'.")
                else:
                    base_price = round(float(hist["Close"].iloc[-1]), 2)
                    ticker_name = ticker_input
                    st.sidebar.success(f"{ticker_input}  →  **${base_price:,.2f}**")
            except Exception as exc:
                st.sidebar.error(f"Error fetching data: {exc}")
else:
    manual = st.sidebar.number_input(
        "Base Price ($)", min_value=0.01, value=100.0, step=0.01, format="%.2f"
    )
    base_price = round(manual, 2)
    ticker_name = "MANUAL"


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE SET 1 — Price Tiers & Visualization
# ═══════════════════════════════════════════════════════════════════════════════
if base_price is not None and base_price > 0:
    st.header("📈 Price Tier Table")

    # Build tier data: -100% to +500% in 5% steps
    percentages = list(range(-100, 505, 5))
    target_prices = [round(base_price * (1 + pct / 100), 2) for pct in percentages]

    tier_df = pd.DataFrame(
        {"Percentage Change (%)": percentages, "Target Price ($)": target_prices}
    )

    # ── Colour-coded HTML table ─────────────────────────────────────────────
    def _render_tier_table(df: pd.DataFrame) -> str:
        rows: list[str] = []
        for _, r in df.iterrows():
            pct = int(r["Percentage Change (%)"])
            price = r["Target Price ($)"]
            if pct == 0:
                css = "anchor-row"
                pct_cell = f'<span style="font-weight:700">► {pct}% (Current)</span>'
            elif pct > 0:
                css = ""
                pct_cell = f'<span class="success-text">+{pct}%</span>'
            else:
                css = ""
                pct_cell = f'<span class="danger-text">{pct}%</span>'
            rows.append(
                f'<tr class="{css}"><td style="padding:6px 14px">{pct_cell}</td>'
                f'<td style="padding:6px 14px;text-align:right">${price:,.2f}</td></tr>'
            )
        header = (
            "<thead><tr>"
            '<th style="padding:8px 14px;text-align:left">Change</th>'
            '<th style="padding:8px 14px;text-align:right">Target Price</th>'
            "</tr></thead>"
        )
        return (
            '<div style="max-height:500px;overflow-y:auto">'
            '<table style="width:100%;border-collapse:collapse;font-size:14px">'
            f"{header}<tbody>{''.join(rows)}</tbody></table></div>"
        )

    col_table, col_chart = st.columns([1, 2])

    with col_table:
        st.markdown(_render_tier_table(tier_df), unsafe_allow_html=True)

    # ── Plotly line chart ───────────────────────────────────────────────────
    with col_chart:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=tier_df["Percentage Change (%)"],
                y=tier_df["Target Price ($)"],
                mode="lines+markers",
                marker=dict(size=4, color="#00d4aa"),
                line=dict(width=2, color="#00d4aa"),
                name="Target Price",
            )
        )
        # Anchor line at 0% / current price
        fig.add_hline(
            y=base_price,
            line_dash="dash",
            line_color="#ffd700",
            annotation_text=f"Current ${base_price:,.2f}",
            annotation_position="top left",
            annotation_font=dict(color="#ffd700", size=12),
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            title=dict(
                text=f"Price Targets — {ticker_name}",
                font=dict(size=18, color="#fafafa"),
            ),
            xaxis=dict(
                title="Percentage Change (%)",
                gridcolor="#1e293b",
                zeroline=True,
                zerolinecolor="#ffd700",
                zerolinewidth=1,
            ),
            yaxis=dict(
                title="Target Price ($)",
                gridcolor="#1e293b",
                tickprefix="$",
            ),
            margin=dict(l=60, r=30, t=50, b=50),
            height=520,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ─── Download CSV: Price Tiers ──────────────────────────────────────────
    csv_tiers = tier_df.to_csv(index=False)
    st.download_button(
        label="⬇️  Download Price Tiers CSV",
        data=csv_tiers,
        file_name=f"price_tiers_{ticker_name}.csv",
        mime="text/csv",
    )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # FEATURE SET 2 — Average-Down / Position Repair
    # ═══════════════════════════════════════════════════════════════════════
    st.header("🛠️ Position Repair — Average Down Calculator")

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        entry_price = st.number_input(
            "Entry Price ($)", min_value=0.01, value=300.0, step=0.01, format="%.2f"
        )
    with rc2:
        current_qty = st.number_input(
            "Current Quantity", min_value=1, value=2, step=1
        )
    with rc3:
        market_price = st.number_input(
            "Current Market Price ($)",
            min_value=0.01,
            value=50.0,
            step=0.01,
            format="%.2f",
        )

    # Validation
    errors: list[str] = []
    if entry_price <= 0:
        errors.append("Entry Price must be greater than zero.")
    if current_qty <= 0:
        errors.append("Current Quantity must be at least 1.")
    if market_price <= 0:
        errors.append("Current Market Price must be greater than zero.")
    if market_price >= entry_price:
        errors.append(
            "Current Market Price should be below your Entry Price for averaging down."
        )

    if errors:
        for e in errors:
            st.error(e)
    else:
        total_cost_basis = entry_price * current_qty

        # Target average prices — dynamic based on entry & market
        # Include explicit steps plus evenly spaced intermediary values
        explicit_targets = [250, 200, 150, 100, 75]
        # Filter targets that make sense: must be between market price and entry price
        targets = sorted(
            {t for t in explicit_targets if market_price < t < entry_price},
            reverse=True,
        )
        # If defaults don't fit the range, generate dynamic steps
        if len(targets) < 3:
            step_size = max(1, round((entry_price - market_price) / 8, 2))
            targets = sorted(
                {
                    round(market_price + i * step_size, 2)
                    for i in range(1, 8)
                    if market_price < market_price + i * step_size < entry_price
                },
                reverse=True,
            )

        rows = []
        for target_avg in targets:
            # DCA formula:
            # target_avg = (total_cost_basis + units_to_buy * market_price) /
            #              (current_qty + units_to_buy)
            # Solving for units_to_buy:
            # units_to_buy = (total_cost_basis - target_avg * current_qty) /
            #                (target_avg - market_price)
            denom = target_avg - market_price
            if denom <= 0:
                continue
            units_to_buy = (total_cost_basis - target_avg * current_qty) / denom
            if units_to_buy <= 0:
                continue
            units_to_buy_rounded = round(units_to_buy, 2)
            cost_to_buy = round(units_to_buy_rounded * market_price, 2)
            new_total_qty = current_qty + units_to_buy_rounded
            new_position_value = round(new_total_qty * market_price, 2)
            rows.append(
                {
                    "Target Avg Price ($)": f"{target_avg:,.2f}",
                    "Units to Buy Now": f"{units_to_buy_rounded:,.2f}",
                    "Total Cost to Buy ($)": f"{cost_to_buy:,.2f}",
                    "New Total Position Value ($)": f"{new_position_value:,.2f}",
                }
            )

        if rows:
            avg_df = pd.DataFrame(rows)

            # Metric cards
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(
                    '<div class="metric-card">'
                    f'<div class="metric-value">${entry_price:,.2f}</div>'
                    '<div class="metric-label">Original Entry</div></div>',
                    unsafe_allow_html=True,
                )
            with m2:
                st.markdown(
                    '<div class="metric-card">'
                    f'<div class="metric-value">${market_price:,.2f}</div>'
                    '<div class="metric-label">Current Market</div></div>',
                    unsafe_allow_html=True,
                )
            with m3:
                loss_pct = round((market_price - entry_price) / entry_price * 100, 1)
                st.markdown(
                    '<div class="metric-card">'
                    f'<div class="metric-value" style="color:#ff4b4b">{loss_pct}%</div>'
                    '<div class="metric-label">Unrealised P&L</div></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")
            st.dataframe(
                avg_df,
                use_container_width=True,
                hide_index=True,
            )

            # Download CSV: Average-Down table
            csv_avg = avg_df.to_csv(index=False)
            st.download_button(
                label="⬇️  Download Average-Down CSV",
                data=csv_avg,
                file_name=f"average_down_{ticker_name}.csv",
                mime="text/csv",
                key="avg_csv",
            )
        else:
            st.info(
                "No valid average-down targets could be computed with the current inputs. "
                "Try adjusting the Entry Price or Market Price."
            )

    # ─── Combined CSV Export ────────────────────────────────────────────────
    st.divider()
    st.subheader("📦 Export All Data")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        tier_df.to_excel(writer, sheet_name="Price Tiers", index=False)
        if not errors and rows:
            pd.DataFrame(rows).to_excel(
                writer, sheet_name="Average Down", index=False
            )
    combined_csv = io.StringIO()
    combined_csv.write("=== PRICE TIERS ===\n")
    combined_csv.write(tier_df.to_csv(index=False))
    if not errors and rows:
        combined_csv.write("\n=== AVERAGE DOWN ===\n")
        combined_csv.write(pd.DataFrame(rows).to_csv(index=False))

    st.download_button(
        label="⬇️  Download Combined CSV",
        data=combined_csv.getvalue(),
        file_name=f"break_even_matrix_{ticker_name}.csv",
        mime="text/csv",
        key="combined_csv",
    )

else:
    st.info("👈 Enter a ticker symbol or a manual base price in the sidebar to begin.")

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("The Break-Even Matrix · Built with Streamlit & Plotly · For educational purposes only.")
