import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Speculator’s Edge", page_icon="📈", layout="centered")

st.title("📈 Speculator’s Edge")
st.markdown("Calculate **Buy** (dip) and **Sell** (gain) price targets based on percentage offsets.")

# --- Input Section ---
st.header("Input")

col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Stock Ticker", placeholder="e.g. AAPL, TSLA").strip().upper()

with col2:
    manual_price = st.number_input(
        "Manual Base Price (optional, overrides ticker)",
        min_value=0.0,
        value=0.0,
        step=0.01,
        format="%.2f",
    )

custom_pcts = st.text_input(
    "Custom Percentages (comma-separated)",
    value="5, 10, 15, 20",
    help="Enter percentage values separated by commas, e.g. 5, 10, 15, 20",
)

calculate = st.button("Calculate", type="primary", use_container_width=True)

# --- Calculation ---
if calculate:
    # Resolve base price
    base_price = None
    source_label = ""

    if manual_price > 0:
        base_price = manual_price
        source_label = "Manual Input"
    elif ticker:
        with st.spinner(f"Fetching data for **{ticker}**..."):
            try:
                stock = yf.Ticker(ticker)
                info = stock.fast_info
                ltp = getattr(info, "last_price", None)
                if ltp is None or ltp <= 0:
                    st.error(
                        f"Could not retrieve a valid price for **{ticker}**. "
                        "Please check the ticker symbol and try again."
                    )
                    st.stop()
                base_price = round(ltp, 2)
                source_label = f"{ticker} (Last Traded Price)"
            except Exception:
                st.error(
                    f"Failed to fetch data for **{ticker}**. "
                    "Please verify the ticker symbol is correct."
                )
                st.stop()
    else:
        st.warning("Please enter a stock ticker or a manual base price.")
        st.stop()

    # Parse custom percentages
    try:
        percentages = sorted(
            {abs(float(p.strip())) for p in custom_pcts.split(",") if p.strip()}
        )
        if not percentages:
            raise ValueError
    except ValueError:
        st.error("Invalid percentage input. Please enter comma-separated numbers (e.g. 5, 10, 15, 20).")
        st.stop()

    # --- Build results ---
    st.divider()
    st.subheader(f"Results — Base Price: **${base_price:,.2f}** ({source_label})")

    # Buy targets (dips)
    buy_rows = []
    for pct in percentages:
        change = round(base_price * pct / 100, 2)
        target = round(base_price - change, 2)
        buy_rows.append(
            {"Dip %": f"-{pct}%", "Price Change ($)": f"-${change:,.2f}", "Target Price ($)": f"${target:,.2f}"}
        )

    # Sell targets (gains)
    sell_rows = []
    for pct in percentages:
        change = round(base_price * pct / 100, 2)
        target = round(base_price + change, 2)
        sell_rows.append(
            {"Gain %": f"+{pct}%", "Price Change ($)": f"+${change:,.2f}", "Target Price ($)": f"${target:,.2f}"}
        )

    col_buy, col_sell = st.columns(2)

    with col_buy:
        st.markdown("#### 🟢 Buy Targets (Dips)")
        st.dataframe(
            pd.DataFrame(buy_rows),
            use_container_width=True,
            hide_index=True,
        )

    with col_sell:
        st.markdown("#### 🔴 Sell Targets (Gains)")
        st.dataframe(
            pd.DataFrame(sell_rows),
            use_container_width=True,
            hide_index=True,
        )
