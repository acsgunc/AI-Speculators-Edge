import streamlit as st

from config import APP_TITLE, APP_ICON, STANDARD_PERCENTAGES
from services.price_service import fetch_last_price, PriceFetchError
from services.calculator import compute_thresholds
from ui.inputs import render_inputs
from ui.results import render_results

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")

st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("Calculate **Buy** (dip) and **Sell** (gain) price targets based on percentage offsets.")

user_input = render_inputs()

if not user_input.submitted:
    st.stop()

# --- Resolve base price ---
if not user_input.ticker:
    st.warning("Please enter a stock ticker.")
    st.stop()

with st.spinner(f"Fetching data for **{user_input.ticker}**..."):
    try:
        result = fetch_last_price(user_input.ticker)
    except PriceFetchError as e:
        st.error(str(e))
        st.stop()

# --- Build percentage list ---
percentages = sorted(set(STANDARD_PERCENTAGES) | ({user_input.custom_pct} if user_input.custom_pct else set()))

# --- Compute & render ---
buy_targets, sell_targets = compute_thresholds(result.price, percentages)
render_results(result.price, result.label, buy_targets, sell_targets)
