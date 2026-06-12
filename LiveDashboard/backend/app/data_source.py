"""Pluggable asynchronous data source architecture.

This module is the single integration point for market data. Every provider is
implemented as an :class:`DataSource` subclass exposing the same async contract:

* :meth:`DataSource.supports`     -- does this source own a given symbol?
* :meth:`DataSource.list_symbols` -- advertise the instruments it serves.
* :meth:`DataSource.get_history`  -- fetch historical OHLCV candles.
* :meth:`DataSource.stream`       -- yield live updates as an async generator.

Adding a new broker/provider (Alpaca, Binance, Zerodha, Polygon, ...) only
requires writing one new subclass and registering it in :data:`REGISTRY`. No
other part of the codebase needs to change.
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx
import websockets

from .config import Settings, get_settings
from .models import AssetClass, Candle, SymbolInfo

# ---------------------------------------------------------------------------
# Interval helpers
# ---------------------------------------------------------------------------

# Number of seconds represented by each supported interval. Used to compute
# sensible history windows and to align polling.
INTERVAL_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "1h": 60 * 60,
    "1d": 24 * 60 * 60,
}


def normalize_interval(interval: str) -> str:
    """Return a supported interval, defaulting to ``1m`` when unknown."""
    return interval if interval in INTERVAL_SECONDS else "1m"


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class DataSource(ABC):
    """Abstract async market-data provider.

    Subclasses encapsulate everything provider specific (transport, auth,
    payload parsing) behind a uniform, fully typed async interface.
    """

    #: Stable identifier surfaced to the frontend via :class:`SymbolInfo`.
    name: str = "base"

    #: Asset class served by this source.
    asset_class: AssetClass

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def list_symbols(self) -> list[SymbolInfo]:
        """Return the instruments this source can serve."""

    @abstractmethod
    def supports(self, symbol: str) -> bool:
        """Return ``True`` when this source owns ``symbol``."""

    @abstractmethod
    async def get_history(self, symbol: str, interval: str) -> list[Candle]:
        """Return historical OHLCV candles, oldest first."""

    @abstractmethod
    def stream(self, symbol: str, interval: str) -> AsyncIterator[dict]:
        """Yield live updates for ``symbol``.

        Each yielded item is a ``dict`` with a ``kind`` key of either
        ``"tick"`` (a bare price update) or ``"candle"`` (a full OHLCV update).
        Implemented as an async generator so callers can simply
        ``async for update in source.stream(...)``.
        """


# ---------------------------------------------------------------------------
# Hyperliquid (crypto) via native WebSocket + REST
# ---------------------------------------------------------------------------


class HyperliquidSource(DataSource):
    """Crypto data from Hyperliquid's public, key-free API.

    History is fetched over REST (``candleSnapshot``) and live updates stream
    from the public WebSocket ``candle`` channel, which pushes an updated candle
    on every trade -- giving us both chart updates and price ticks.
    """

    name = "hyperliquid"
    asset_class = AssetClass.CRYPTO

    # Curated set of liquid perpetuals that work without any credentials.
    _SYMBOLS: dict[str, str] = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "ARB": "Arbitrum",
        "AVAX": "Avalanche",
        "DOGE": "Dogecoin",
        "MATIC": "Polygon",
        "LINK": "Chainlink",
    }

    def list_symbols(self) -> list[SymbolInfo]:
        return [
            SymbolInfo(
                symbol=sym,
                label=f"{name} ({sym})",
                asset_class=self.asset_class,
                provider=self.name,
            )
            for sym, name in self._SYMBOLS.items()
        ]

    def supports(self, symbol: str) -> bool:
        return symbol in self._SYMBOLS

    async def get_history(self, symbol: str, interval: str) -> list[Candle]:
        interval = normalize_interval(interval)
        now_ms = int(time.time() * 1000)
        window_ms = INTERVAL_SECONDS[interval] * 500 * 1000  # ~500 candles
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": interval,
                "startTime": now_ms - window_ms,
                "endTime": now_ms,
            },
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.settings.hyperliquid_rest_url, json=payload)
            resp.raise_for_status()
            raw = resp.json()

        candles = [self._parse_candle(item) for item in raw]
        return sorted(candles, key=lambda c: c.time)

    async def stream(self, symbol: str, interval: str) -> AsyncIterator[dict]:
        interval = normalize_interval(interval)
        subscription = {
            "method": "subscribe",
            "subscription": {"type": "candle", "coin": symbol, "interval": interval},
        }
        # Reconnect loop keeps the bridge resilient to dropped sockets.
        while True:
            try:
                async with websockets.connect(
                    self.settings.hyperliquid_ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    await ws.send(json.dumps(subscription))
                    async for raw in ws:
                        message = json.loads(raw)
                        if message.get("channel") != "candle":
                            continue
                        candle = self._parse_candle(message["data"])
                        yield {"kind": "candle", "candle": candle}
                        yield {"kind": "tick", "price": candle.close, "time": candle.time}
            except (websockets.WebSocketException, OSError):
                # Brief backoff before attempting to reconnect.
                await asyncio.sleep(2.0)

    @staticmethod
    def _parse_candle(item: dict) -> Candle:
        """Convert a Hyperliquid candle payload into a :class:`Candle`."""
        return Candle(
            time=int(item["t"]) // 1000,
            open=float(item["o"]),
            high=float(item["h"]),
            low=float(item["l"]),
            close=float(item["c"]),
            volume=float(item.get("v", 0.0)),
        )


# ---------------------------------------------------------------------------
# yfinance (Indian stocks) via async polling
# ---------------------------------------------------------------------------


class YFinanceSource(DataSource):
    """Indian equities sourced from Yahoo Finance through ``yfinance``.

    ``yfinance`` is synchronous and offers no streaming socket, so blocking
    calls are off-loaded to a thread pool and live behaviour is emulated by
    polling the most recent candles on an interval.
    """

    name = "yfinance"
    asset_class = AssetClass.INDIAN_STOCK

    # NSE listed tickers (Yahoo uses the ``.NS`` suffix) plus the Nifty index.
    _SYMBOLS: dict[str, str] = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "SBIN.NS": "State Bank of India",
        "TATAMOTORS.NS": "Tata Motors",
        "^NSEI": "Nifty 50 Index",
    }

    # Map our canonical intervals onto the values yfinance understands.
    _INTERVAL_MAP: dict[str, str] = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "60m",
        "1d": "1d",
    }

    # yfinance enforces a maximum look-back per interval for intraday data.
    _PERIOD_MAP: dict[str, str] = {
        "1m": "5d",
        "5m": "1mo",
        "15m": "1mo",
        "1h": "3mo",
        "1d": "2y",
    }

    def list_symbols(self) -> list[SymbolInfo]:
        return [
            SymbolInfo(
                symbol=sym,
                label=name,
                asset_class=self.asset_class,
                provider=self.name,
            )
            for sym, name in self._SYMBOLS.items()
        ]

    def supports(self, symbol: str) -> bool:
        return symbol in self._SYMBOLS

    async def get_history(self, symbol: str, interval: str) -> list[Candle]:
        interval = normalize_interval(interval)
        return await asyncio.to_thread(self._fetch_history_sync, symbol, interval)

    async def stream(self, symbol: str, interval: str) -> AsyncIterator[dict]:
        interval = normalize_interval(interval)
        last_time: int | None = None
        while True:
            try:
                candles = await asyncio.to_thread(
                    self._fetch_history_sync, symbol, interval, 2
                )
                if candles:
                    latest = candles[-1]
                    # Emit the freshest candle plus a tick for the price flash.
                    yield {"kind": "candle", "candle": latest}
                    if last_time != latest.time:
                        last_time = latest.time
                    yield {"kind": "tick", "price": latest.close, "time": latest.time}
            except Exception:  # noqa: BLE001 - polling must never crash the stream
                pass
            await asyncio.sleep(self.settings.poll_interval_seconds)

    def _fetch_history_sync(
        self, symbol: str, interval: str, limit: int | None = None
    ) -> list[Candle]:
        """Blocking yfinance fetch executed inside a worker thread."""
        import yfinance as yf  # imported lazily to keep startup fast

        yf_interval = self._INTERVAL_MAP[interval]
        period = self._PERIOD_MAP[interval]
        frame = yf.download(
            tickers=symbol,
            period=period,
            interval=yf_interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if frame is None or frame.empty:
            return []

        # yfinance returns a MultiIndex column frame for single tickers in
        # recent versions; flatten it defensively.
        if hasattr(frame.columns, "nlevels") and frame.columns.nlevels > 1:
            frame.columns = frame.columns.get_level_values(0)

        candles: list[Candle] = []
        for ts, row in frame.iterrows():
            candles.append(
                Candle(
                    time=int(ts.timestamp()),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0.0) or 0.0),
                )
            )
        candles.sort(key=lambda c: c.time)
        return candles[-limit:] if limit else candles


# ---------------------------------------------------------------------------
# Registry & resolution
# ---------------------------------------------------------------------------


def _build_registry(settings: Settings) -> list[DataSource]:
    """Instantiate every available data source.

    To plug in a new provider, append its instance here (or load it
    dynamically). Nothing else in the application needs to change.
    """
    return [
        HyperliquidSource(settings),
        YFinanceSource(settings),
    ]


_REGISTRY: list[DataSource] | None = None


def get_registry() -> list[DataSource]:
    """Return the lazily constructed, process-wide source registry."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry(get_settings())
    return _REGISTRY


def resolve_source(symbol: str) -> DataSource:
    """Return the data source that owns ``symbol``.

    Raises:
        ValueError: if no registered source supports the symbol.
    """
    for source in get_registry():
        if source.supports(symbol):
            return source
    raise ValueError(f"No data source registered for symbol '{symbol}'")


def all_symbols() -> list[SymbolInfo]:
    """Aggregate the advertised symbols from every registered source."""
    symbols: list[SymbolInfo] = []
    for source in get_registry():
        symbols.extend(source.list_symbols())
    return symbols
