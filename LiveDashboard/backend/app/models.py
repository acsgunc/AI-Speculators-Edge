"""Typed data models shared across the backend.

These Pydantic models define the wire format exchanged with the Angular client
over both REST and WebSocket transports. Keeping them in one module guarantees
the frontend and backend agree on a single, fully typed contract.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    """High level grouping used by the symbol selector in the UI."""

    CRYPTO = "crypto"
    INDIAN_STOCK = "indian_stock"


class Candle(BaseModel):
    """A single OHLCV candle.

    ``time`` is a UNIX timestamp in **seconds**, which is the format expected by
    TradingView Lightweight Charts.
    """

    time: int = Field(..., description="UNIX timestamp in seconds")
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class SymbolInfo(BaseModel):
    """Metadata describing a tradable instrument exposed to the frontend."""

    symbol: str = Field(..., description="Provider specific symbol, e.g. 'BTC' or 'RELIANCE.NS'")
    label: str = Field(..., description="Human friendly display name")
    asset_class: AssetClass
    provider: str = Field(..., description="Name of the data source handling this symbol")


class HistoryResponse(BaseModel):
    """REST response payload for historical candles."""

    symbol: str
    interval: str
    candles: list[Candle]


# --- WebSocket messages ---------------------------------------------------


class SubscribeRequest(BaseModel):
    """Inbound message a client sends to start streaming a symbol."""

    action: Literal["subscribe"] = "subscribe"
    symbol: str
    interval: str = "1m"


class TickMessage(BaseModel):
    """Outbound lightweight price update used to flash the ticker bar."""

    type: Literal["tick"] = "tick"
    symbol: str
    price: float
    time: int


class CandleMessage(BaseModel):
    """Outbound candle update used to (re)draw the chart series."""

    type: Literal["candle"] = "candle"
    symbol: str
    interval: str
    candle: Candle


class ErrorMessage(BaseModel):
    """Outbound error notification."""

    type: Literal["error"] = "error"
    detail: str
