"""Sidebar — price-source selection and live-ticker fetch."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from core.market_data import fetch_live_price


@dataclass
class SidebarResult:
    base_price: float | None
    ticker_name: str


def render() -> SidebarResult:
    st.sidebar.header("⚙️ Configuration")

    input_mode = st.sidebar.radio(
        "Price Source",
        ["Manual Base Price", "Stock Ticker (Live)"],
        horizontal=True,
    )

    if input_mode == "Manual Base Price":
        return _manual_mode()
    return _ticker_mode()


def _ticker_mode() -> SidebarResult:
    symbol = (
        st.sidebar.text_input("Ticker Symbol", value="AAPL", max_chars=10)
        .strip()
        .upper()
    )
    if not symbol:
        return SidebarResult(base_price=None, ticker_name="")

    with st.spinner(f"Fetching {symbol}…"):
        try:
            result = fetch_live_price(symbol)
            st.sidebar.success(f"{symbol}  →  **${result.price:,.2f}**")
            return SidebarResult(base_price=result.price, ticker_name=symbol)
        except LookupError as exc:
            st.sidebar.error(str(exc))
        except Exception as exc:
            st.sidebar.error(f"Error fetching data: {exc}")

    return SidebarResult(base_price=None, ticker_name="")


def _manual_mode() -> SidebarResult:
    price = round(
        st.sidebar.number_input(
            "Base Price ($)", min_value=0.01, value=100.0, step=0.01, format="%.2f"
        ),
        2,
    )
    return SidebarResult(base_price=price, ticker_name="MANUAL")
