# Live Trading Dashboard

A local-first, configurable **split-screen live trading dashboard**. Display 1–8
independent charts, each with its own symbol and timeframe, streaming live prices
over WebSockets (crypto) and async HTTP polling (Indian equities). No API keys
required.

- **Frontend:** Angular 21 (standalone, signals) · Tailwind CSS · TradingView Lightweight Charts
- **Backend:** FastAPI · Uvicorn · native WebSockets · async HTTP
- **Data (key-free):** Hyperliquid public WebSocket (crypto) · `yfinance` (Indian stocks)

> 📚 **Full documentation** lives in [`docs/`](docs/README.md) — architecture,
> backend/frontend internals, API reference, configuration, deployment, and a
> guide to adding new data providers.

---

## Project structure

```
LiveDashboard/
├── backend/                     # FastAPI service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # env-driven settings (python-dotenv)
│   │   ├── models.py            # typed Pydantic wire models
│   │   ├── data_source.py       # pluggable async provider architecture
│   │   └── main.py              # REST + WebSocket bridge + static serving
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # Angular SPA
│   └── src/app/
│       ├── models/market.ts     # shared TypeScript interfaces
│       ├── services/            # REST, WebSocket, config, persisted state
│       └── components/          # dashboard, chart-pane, ticker-bar
├── Dockerfile                   # multi-stage unified-service build
├── render.yaml                  # Render one-click blueprint
├── Procfile                     # Railway / Heroku-style process def
└── README.md
```

---

## Run locally

You need **Python 3.10+** and **Node.js 20+**.

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env            # optional; sensible defaults are built in

# Start the API (auto-reload)
uvicorn app.main:app --reload --port 8000
```

The API is now at <http://localhost:8000> (interactive docs at `/docs`).

### 2. Frontend (Angular)

In a second terminal:

```bash
cd frontend
npm install
npm start
```

Open <http://localhost:4200>. The dev server talks to the backend on
`http://localhost:8000` (configured in
`src/environments/environment.development.ts`).

---

## How it works

### Pluggable async data architecture (`backend/app/data_source.py`)

Every provider implements the same async `DataSource` contract:

| Method          | Purpose                                   |
| --------------- | ----------------------------------------- |
| `supports`      | Does this source own a given symbol?      |
| `list_symbols`  | Advertise its instruments to the UI.      |
| `get_history`   | Async fetch of historical OHLCV candles.  |
| `stream`        | Async generator of live tick/candle data. |

**Adding a new broker/provider** (Alpaca, Binance, Zerodha, Polygon, …) only
requires writing one new `DataSource` subclass and appending it to the registry
in `_build_registry()`. Nothing else in the app changes.

- **Crypto** — `HyperliquidSource` uses FastAPI's native WebSocket routing to
  bridge Hyperliquid's public socket to the browser, with REST for history.
- **Indian stocks** — `YFinanceSource` runs blocking `yfinance` calls in a
  thread pool and emulates streaming via interval polling.

### Frontend

- **Dynamic grid** — a "Number of Charts" selector (1 / 2 / 4 / 6 / 8) reshapes
  a responsive Tailwind grid (full-screen, 2×1, 2×2, 3×2, 4×2).
- **State persistence** — chart count and every pane's symbol/interval are saved
  to `localStorage` and restored on reload.
- **Independent panes** — each chart has its own symbol dropdown (grouped into
  Crypto / Indian Stocks) and timeframe toggle (1m, 5m, 15m, 1h, 1d).
- **Flashing ticker bar** — the bar atop each chart flashes **green** on an
  uptick and **red** on a downtick from live updates.

---

## Cloud deployment (free tiers)

The backend can serve the compiled Angular bundle, so the whole app runs as a
**single web service** — ideal for free tiers that allow only one instance.

### Environment variables (backend)

| Variable                | Default                          | Description                                  |
| ----------------------- | -------------------------------- | -------------------------------------------- |
| `HOST`                  | `0.0.0.0`                        | Bind address.                                |
| `PORT`                  | `8000`                           | Bind port (platforms usually inject this).   |
| `CORS_ORIGINS`          | `*`                              | Comma-separated allowed origins.             |
| `FRONTEND_DIST`         | `../frontend/dist/.../browser`   | Path to the built SPA; served at `/` if set. |
| `POLL_INTERVAL_SECONDS` | `5`                              | yfinance polling cadence.                    |
| `RELOAD`                | `0`                              | Set `1` for auto-reload in dev.              |

### Option A — Docker (Render, Fly.io, Hugging Face Spaces)

The multi-stage [`Dockerfile`](Dockerfile) builds the Angular SPA, installs the
backend, and serves both from one container:

```bash
docker build -t live-dashboard .
docker run -p 8000:8000 live-dashboard
```

Open <http://localhost:8000>.

### Option B — Render blueprint

Push the repo and point Render at [`render.yaml`](render.yaml) for a one-click
deploy (Docker runtime, free plan, health check on `/api/health`).

### Option C — Procfile (Railway / Heroku-style)

[`Procfile`](Procfile) runs Uvicorn bound to the platform's `$PORT`. Build the
frontend first (`cd frontend && npm run build`) so the backend can serve it.

---

## API reference

| Method | Path                                   | Description                              |
| ------ | -------------------------------------- | ---------------------------------------- |
| `GET`  | `/api/health`                          | Liveness probe.                          |
| `GET`  | `/api/symbols`                         | Symbols grouped by asset class.          |
| `GET`  | `/api/history?symbol=&interval=`       | Historical OHLCV candles.                |
| `WS`   | `/ws/stream`                           | Live bridge; subscribe then receive ticks/candles. |

WebSocket protocol: send `{"action":"subscribe","symbol":"BTC","interval":"1m"}`,
then receive `{"type":"candle",...}` and `{"type":"tick",...}` messages.

---

## Notes & troubleshooting

- **Indian stock data on restricted networks:** `yfinance` calls Yahoo Finance
  over HTTPS. On corporate networks that intercept TLS with a self-signed root
  certificate you may see `CERTIFICATE_VERIFY_FAILED` and empty results. The app
  handles this gracefully (no crash) and it works normally on standard networks
  and in cloud deployments. Crypto data is unaffected.
- No paid API keys are required for any of the default feeds.
