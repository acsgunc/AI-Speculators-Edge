import streamlit as st

from config import APP_TITLE, APP_ICON, PCT_RANGE
from services.price_service import fetch_last_price, PriceFetchError
from services.calculator import build_threshold_df
from ui.inputs import render_inputs
from ui.results import render_results

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

st.title(f"{APP_ICON} {APP_TITLE}")
st.markdown("Calculate **Buy** (dip) and **Sell** (gain) price targets from **-100%** to **+500%** in 5% steps.")

user_input, filters = render_inputs()

if not user_input.submitted:
    st.stop()

# --- Resolve base price ---
if user_input.manual_price > 0:
    base_price = user_input.manual_price
    source_label = "Manual Input"
elif user_input.ticker:
    with st.spinner(f"Fetching data for **{user_input.ticker}**..."):
        try:
            result = fetch_last_price(user_input.ticker)
            base_price = result.price
            source_label = result.label
        except PriceFetchError as e:
            st.error(str(e))
            st.stop()
else:
    st.warning("Please enter a stock ticker or a manual base price.")
    st.stop()

# --- Compute & render ---
df = build_threshold_df(base_price, PCT_RANGE)
render_results(base_price, source_label, df, filters)
