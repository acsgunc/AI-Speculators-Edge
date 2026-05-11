from dataclasses import dataclass

import streamlit as st

from config import DEFAULT_PERCENTAGES


@dataclass
class UserInput:
    ticker: str
    manual_price: float
    custom_pcts: str
    submitted: bool


def render_inputs() -> UserInput:
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
        value=DEFAULT_PERCENTAGES,
        help="Enter percentage values separated by commas, e.g. 5, 10, 15, 20",
    )

    submitted = st.button("Calculate", type="primary", use_container_width=True)

    return UserInput(
        ticker=ticker,
        manual_price=manual_price,
        custom_pcts=custom_pcts,
        submitted=submitted,
    )
