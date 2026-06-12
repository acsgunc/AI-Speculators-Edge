# 03 — Backend

FastAPI service that bridges market data providers to the Angular client over
REST and WebSockets.

## Directory

```
backend/
├── app/
│   ├── __init__.py        # package marker + version
│   ├── config.py          # env-driven Settings (python-dotenv)
│   ├── models.py          # Pydantic wire models
│   ├── data_source.py     # pluggable async provider architecture
│   └── main.py            # FastAPI app: REST, WebSocket, static serving
├── requirements.txt
└── .env.example
```

## `app/config.py`

Loads environment variables (optionally from `.env`) into a frozen, typed
`Settings` dataclass.

```python
@dataclass(frozen=True)
class Settings:
    host: str                     # HOST, default 0.0.0.0
    port: int                     # PORT, default 8000
    cors_origins: list[str]       # CORS_ORIGINS (CSV), default ["*"]
    frontend_dist: str            # FRONTEND_DIST, path to built SPA
    hyperliquid_ws_url: str       # HYPERLIQUID_WS_URL
    hyperliquid_rest_url: str     # HYPERLIQUID_REST_URL
    poll_interval_seconds: float  # POLL_INTERVAL_SECONDS, default 5
```

- `get_settings()` is `@lru_cache`d → a single process-wide instance.
- `_split_csv()` parses comma-separated origin lists.
- `load_dotenv()` runs at import time; missing `.env` is harmless (cloud
  platforms inject real env vars).

See [06 — Configuration](06-configuration.md) for every variable.

## `app/models.py`

Pydantic models defining the wire format. These mirror the TypeScript
interfaces in the frontend.

| Model | Purpose |
| --- | --- |
| `AssetClass` (enum) | `crypto` \| `indian_stock`. |
| `Candle` | OHLCV bar; `time` = UNIX seconds. |
| `SymbolInfo` | Symbol metadata (symbol, label, asset_class, provider). |
| `HistoryResponse` | REST payload for `/api/history`. |
| `SubscribeRequest` | Inbound WS subscribe message. |
| `TickMessage` | Outbound price tick (`type: "tick"`). |
| `CandleMessage` | Outbound candle update (`type: "candle"`). |
| `ErrorMessage` | Outbound error (`type: "error"`). |

## `app/data_source.py`

The heart of the backend. See [09 — Extending](09-extending-data-sources.md)
for the full provider-authoring guide.

### Interval helpers

```python
INTERVAL_SECONDS = {"1m":60, "5m":300, "15m":900, "1h":3600, "1d":86400}
normalize_interval(interval) -> str   # falls back to "1m" if unknown
```

### `DataSource` (abstract base class)

| Member | Type | Description |
| --- | --- | --- |
| `name` | `str` | Stable provider id surfaced to the UI. |
| `asset_class` | `AssetClass` | Grouping for the symbol selector. |
| `list_symbols()` | `-> list[SymbolInfo]` | Instruments served. |
| `supports(symbol)` | `-> bool` | Does this source own the symbol? |
| `get_history(symbol, interval)` | `async -> list[Candle]` | Historical candles, oldest first. |
| `stream(symbol, interval)` | `async iterator[dict]` | Yields `{"kind":"candle"\|"tick", ...}`. |

### `HyperliquidSource` (crypto)

- **History:** `POST` to the Hyperliquid `info` endpoint with a
  `candleSnapshot` request (~500 candles window). Parses `t/o/h/l/c/v`.
- **Stream:** subscribes to the public `candle` channel over WebSocket inside a
  **reconnect loop** (`ping_interval=20`, 2s backoff on failure). Each candle
  frame yields both a `candle` and a `tick` update.

### `YFinanceSource` (Indian stocks)

- **History:** `asyncio.to_thread(_fetch_history_sync, ...)` so blocking
  `yfinance.download()` never blocks the loop.
- **Interval map:** `1h → 60m`; others pass through. Period caps per interval
  respect Yahoo's intraday look-back limits.
- **Stream:** polls the latest 2 candles every `POLL_INTERVAL_SECONDS`, yielding
  a `candle` + `tick`. Defensive `try/except` keeps the poll loop alive.
- Flattens yfinance's MultiIndex columns for single-ticker frames.

### Registry & resolution

```python
get_registry()        -> list[DataSource]   # lazily built, process-wide
resolve_source(symbol)-> DataSource          # raises ValueError if unknown
all_symbols()         -> list[SymbolInfo]    # union across sources
```

Providers are instantiated in `_build_registry()`. **To add one, append its
instance there.**

## `app/main.py`

### App setup
- Creates the `FastAPI` app with title/description/version.
- Adds `CORSMiddleware` from `settings.cors_origins`.

### REST endpoints

| Method | Path | Handler | Notes |
| --- | --- | --- | --- |
| GET | `/api/health` | `health` | `{"status":"ok"}`. |
| GET | `/api/symbols` | `symbols` | Grouped by asset class. |
| GET | `/api/history` | `history` | 404 if symbol unknown, 502 on upstream error. |

### WebSocket: `/ws/stream`
1. `accept()` the socket.
2. Receive + validate a `SubscribeRequest`.
3. Resolve the source; on unknown symbol send `ErrorMessage` and close.
4. Spawn `_pump(...)` as a background task that forwards `stream()` updates as
   `CandleMessage` / `TickMessage`.
5. Keep the socket alive on `receive_text()`; on disconnect, cancel the pump
   task cleanly (`asyncio.CancelledError` suppressed).

### Static frontend (optional)
If `settings.frontend_dist` is an existing directory, the compiled SPA is
mounted at `/` via `StaticFiles(..., html=True)`. Mounted **after** the API
routes so `/api/*` and `/ws/*` always take precedence.

### Entry point
`run()` launches Uvicorn with `host`, `port`, and `reload` (from `RELOAD`).
Invoked by `python -m app.main`.

## Request lifecycle (history example)

```
GET /api/history?symbol=BTC&interval=1m
  → normalize_interval("1m")
  → resolve_source("BTC")            # HyperliquidSource
  → await source.get_history(...)    # httpx POST candleSnapshot
  → HistoryResponse(symbol, interval, candles=[...])
```

## Error handling

| Condition | Response |
| --- | --- |
| Unknown symbol (REST) | `404` with detail. |
| Upstream provider error (REST) | `502` with detail. |
| Unknown symbol (WS) | `ErrorMessage` then close. |
| Provider exception mid-stream | Swallowed by the source's loop (keeps streaming). |
| Client disconnect | Pump task cancelled, socket cleaned up. |
