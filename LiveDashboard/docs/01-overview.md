# 01 — Overview

## What is it?

Live Trading Dashboard is a **local-first web application** that displays a
configurable number of live trading charts (1, 2, 4, 6, or 8) on a responsive
split-screen layout. Each chart pane is fully independent — its own symbol,
timeframe, live price stream, and color-coded ticker.

It requires **no paid API keys** and runs entirely on your machine by default,
while remaining ready for **one-click deployment** to free cloud tiers as a
single unified service.

## Feature list

### Charting & layout
- Selectable chart count: **1, 2, 4, 6, 8**.
- Responsive Tailwind grid that reshapes per selection:
  - 1 → full screen (1×1)
  - 2 → side-by-side (2×1)
  - 4 → 2×2
  - 6 → 3×2
  - 8 → 4×2
- TradingView **Lightweight Charts** candlestick rendering with auto-resize.

### Per-pane controls
- **Symbol selector** — dropdown grouped into *Crypto* and *Indian Stocks*.
- **Timeframe selector** — 1m, 5m, 15m, 1h, 1d toggle group.
- Switching symbol or timeframe transparently reloads history and reconnects
  the live stream.

### Live data
- **Crypto:** real-time prices bridged from **Hyperliquid's public WebSocket**.
- **Indian stocks:** live/recent data from **`yfinance`** via async polling.
- Each pane gets both **candle** updates (chart) and **tick** updates (price).

### Visual indicators
- A **color-coded ticker bar** on top of every pane.
- Flashes **green** on a price increase and **red** on a price decrease, driven
  by incoming live updates.

### Persistence
- Last selected **chart count** and **every pane's symbol/timeframe** are saved
  to `localStorage` and restored on reload.

### Deployment readiness
- Env-driven CORS, host, and port.
- FastAPI can serve the compiled Angular build → single web service.
- `Dockerfile`, `render.yaml`, and `Procfile` included.

## Tech stack

| Layer | Technology | Version | Role |
| --- | --- | --- | --- |
| Frontend framework | Angular | 21 | Standalone components, signals, zoneless change detection |
| Styling | Tailwind CSS | 3.4 | Utility-first responsive layout |
| Charts | TradingView Lightweight Charts | 5 | Candlestick rendering |
| Backend framework | FastAPI | 0.115 | REST + WebSocket routing |
| ASGI server | Uvicorn | 0.34 | Async HTTP/WS server |
| HTTP client | httpx | 0.28 | Async REST calls to providers |
| WS client | websockets | 14 | Upstream crypto socket |
| Stock data | yfinance | 0.2 | Indian equities (NSE) |
| Config | python-dotenv | 1.0 | `.env` loading |
| Validation | Pydantic | 2.10 | Typed wire models |

## Glossary

| Term | Meaning |
| --- | --- |
| **Pane** | A single chart with its own controls, stream, and ticker. |
| **Data source** | A backend class implementing a provider (e.g. Hyperliquid). |
| **Candle** | One OHLCV bar. `time` is a UNIX timestamp in **seconds**. |
| **Tick** | A bare price update used to flash the ticker bar. |
| **Interval / timeframe** | Candle duration: `1m`, `5m`, `15m`, `1h`, `1d`. |
| **Asset class** | High-level grouping: `crypto` or `indian_stock`. |
| **Unified service** | Backend serving the built SPA, so one process runs everything. |

## Supported symbols (defaults)

**Crypto (Hyperliquid):** BTC, ETH, SOL, ARB, AVAX, DOGE, MATIC, LINK

**Indian stocks (yfinance / NSE):** RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS,
ICICIBANK.NS, SBIN.NS, TATAMOTORS.NS, ^NSEI (Nifty 50)

These lists live in `backend/app/data_source.py` and are advertised to the UI
via `GET /api/symbols`.
