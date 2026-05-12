"""Fetch ticker lists for Nifty 500 (NSE) and S&P 500 (NYSE)."""

import io
import pandas as pd
import requests
import streamlit as st

# Wikipedia blocks the default urllib User-Agent with 403; use a browser UA.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _read_html_safe(url: str) -> list[pd.DataFrame]:
    """Fetch a URL with a browser User-Agent and parse HTML tables.

    Falls back to SSL verification disabled when a corporate proxy causes
    certificate chain errors (SSLError / self-signed cert in chain).
    No credentials are transmitted, so disabling verification here is safe.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15, verify=True)
        resp.raise_for_status()
        return pd.read_html(io.StringIO(resp.text), header=0)
    except requests.exceptions.SSLError:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = requests.get(url, headers=_HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
        return pd.read_html(io.StringIO(resp.text), header=0)


@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_nifty500_tickers() -> list[str]:
    """Fetch Nifty 500 tickers from Wikipedia and append .NS suffix."""
    url = "https://en.wikipedia.org/wiki/NIFTY_500"
    try:
        tables = _read_html_safe(url)
        # The main table with tickers is usually the largest one
        for table in tables:
            cols_lower = [str(c).lower() for c in table.columns]
            for col_name in ["symbol", "ticker", "nse symbol", "company"]:
                if col_name in cols_lower:
                    idx = cols_lower.index(col_name)
                    col = table.columns[idx]
                    tickers = table[col].dropna().astype(str).tolist()
                    if len(tickers) > 100:
                        return [f"{t.strip()}.NS" for t in tickers if t.strip()]
        # Fallback: try first table, second column
        if len(tables) > 0 and len(tables[0].columns) >= 2:
            col = tables[0].columns[1]
            tickers = tables[0][col].dropna().astype(str).tolist()
            return [f"{t.strip()}.NS" for t in tickers if t.strip() and t.strip().isalpha()]
    except Exception:
        pass

    # Hardcoded fallback — top ~50 Nifty stocks
    return [f"{t}.NS" for t in _NIFTY_FALLBACK]


@st.cache_data(ttl=86400)
def get_sp500_tickers() -> list[str]:
    """Fetch S&P 500 tickers from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = _read_html_safe(url)
        df = tables[0]
        tickers = df["Symbol"].dropna().astype(str).tolist()
        # yfinance uses dots instead of hyphens for some tickers (BRK.B not BRK-B)
        return [t.strip().replace(".", "-") for t in tickers if t.strip()]
    except Exception:
        pass

    return list(_SP500_FALLBACK)


_NIFTY_FALLBACK = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC", "LT", "AXISBANK",
    "BAJFINANCE", "ASIANPAINT", "MARUTI", "HCLTECH", "SUNPHARMA",
    "TITAN", "WIPRO", "ULTRACEMCO", "NESTLEIND", "TATAMOTORS",
    "BAJAJFINSV", "ONGC", "NTPC", "POWERGRID", "TATASTEEL",
    "ADANIENT", "ADANIPORTS", "JSWSTEEL", "TECHM", "HDFCLIFE",
    "DIVISLAB", "DRREDDY", "CIPLA", "GRASIM", "APOLLOHOSP",
    "COALINDIA", "EICHERMOT", "BPCL", "INDUSINDBK", "SBILIFE",
    "BRITANNIA", "TATACONSUM", "M&M", "HEROMOTOCO", "UPL",
    "BAJAJ-AUTO", "HINDALCO", "VEDL",
]

_SP500_FALLBACK = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "UNH",
    "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK", "ABBV",
    "LLY", "PEP", "KO", "COST", "AVGO", "TMO", "WMT", "MCD", "CSCO",
    "ACN", "ABT", "DHR", "CRM", "NEE", "LIN", "TXN", "PM", "UPS",
    "MS", "RTX", "HON", "LOW", "AMGN", "UNP", "T", "ELV", "GS",
    "CAT", "BA", "DE", "INTU", "BLK",
]
