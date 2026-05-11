from dataclasses import dataclass

import streamlit as st


@dataclass
class UserInput:
    ticker: str
    submitted: bool
    custom_pct: float | None = None


def render_sidebar() -> float | None:
    with st.sidebar:
        st.header("Custom Target")
        raw = st.number_input(
            "Custom Percentage (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5,
            format="%.1f",
            help="Add an extra dip/high level (e.g. 15). Set to 0 to skip.",
        )
        return raw if raw > 0 else None


def render_inputs() -> UserInput:
    ticker = st.text_input("Stock Ticker", placeholder="e.g. AAPL, TSLA").strip().upper()
    submitted = st.button("Fetch Current Price", type="primary", use_container_width=True)
    custom_pct = render_sidebar()

    return UserInput(
        ticker=ticker,
        submitted=submitted,
        custom_pct=custom_pct,
    )
