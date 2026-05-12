"""External market-data gateway — isolates the yfinance dependency."""

from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf


@dataclass(frozen=True, slots=True)
class TickerResult:
    symbol: str
    price: float


def fetch_live_price(symbol: str) -> TickerResult:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    if hist.empty:
        raise LookupError(f"No data found for '{symbol}'.")
    return TickerResult(
        symbol=symbol,
        price=round(float(hist["Close"].iloc[-1]), 2),
    )
