from dataclasses import dataclass

import streamlit as st


@dataclass
class UserInput:
    ticker: str
    manual_price: float
    submitted: bool


@dataclass
class FilterOptions:
    search_pct: int | None
    show_dips: bool
    show_highs: bool


def render_sidebar() -> FilterOptions:
    with st.sidebar:
        st.header("Filters")

        raw = st.text_input(
            "Jump to Percentage (%)",
            placeholder="e.g. 155",
            help="Enter a percentage value to highlight that row.",
        ).strip()
        search_pct = int(raw) if raw.lstrip('-').isdigit() else None

        st.markdown("---")
        show_dips = st.checkbox("Show Dips (negative %)", value=True)
        show_highs = st.checkbox("Show Highs (positive %)", value=True)

    return FilterOptions(
        search_pct=search_pct,
        show_dips=show_dips,
        show_highs=show_highs,
    )


def render_inputs() -> tuple[UserInput, FilterOptions]:
    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("Stock Ticker", placeholder="e.g. AAPL, TSLA").strip().upper()

    with col2:
        manual_price = st.number_input(
            "Manual Base Price (optional)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            help="Enter a custom stock price instead of fetching live data.",
        )

    submitted = st.button("Fetch Current Price", type="primary", use_container_width=True)
    filters = render_sidebar()

    return (
        UserInput(ticker=ticker, manual_price=manual_price, submitted=submitted),
        filters,
    )
