# Live Trading Dashboard — Documentation

Complete technical documentation for the Live Trading Dashboard: a local-first,
key-free, configurable split-screen live charting application.

## Table of contents

| Document | Description |
| --- | --- |
| [01 — Overview](01-overview.md) | What the app is, feature list, tech stack, and glossary. |
| [02 — Architecture](02-architecture.md) | System design, data flow, diagrams, and design decisions. |
| [03 — Backend](03-backend.md) | FastAPI service: modules, classes, lifecycle, and internals. |
| [04 — Frontend](04-frontend.md) | Angular app: components, services, signals, and state. |
| [05 — API Reference](05-api-reference.md) | REST endpoints and the WebSocket protocol. |
| [06 — Configuration](06-configuration.md) | Every environment variable and config file. |
| [07 — Local Development](07-development.md) | Setup, run, build, and developer workflow. |
| [08 — Deployment](08-deployment.md) | Docker, Render, Railway, Fly.io, Hugging Face Spaces. |
| [09 — Extending: New Data Sources](09-extending-data-sources.md) | Step-by-step guide to plug in a new provider. |
| [10 — Troubleshooting](10-troubleshooting.md) | Common issues, causes, and fixes. |
| [11 — macOS Local Setup](11-macos-local-setup.md) | Exhaustive MacBook walkthrough from a clean machine. |

## Quick links

- **Run locally:** [07 — Local Development](07-development.md)
- **Run on a MacBook (full step-by-step):** [11 — macOS Setup](11-macos-local-setup.md)
- **Add Binance / Alpaca / Zerodha:** [09 — Extending](09-extending-data-sources.md)
- **Deploy free:** [08 — Deployment](08-deployment.md)
- **API contract:** [05 — API Reference](05-api-reference.md)

## At a glance

```
Angular 21 SPA  ──HTTP──▶  FastAPI  ──REST/WS──▶  Hyperliquid (crypto)
   (browser)    ──WS────▶  (Uvicorn)             yfinance (Indian stocks)
```

- **Frontend:** Angular 21 (standalone components, signals, zoneless), Tailwind CSS, TradingView Lightweight Charts.
- **Backend:** FastAPI, Uvicorn, native WebSockets, async HTTP (`httpx`), `yfinance`.
- **No API keys required.** Runs entirely locally; deploys as a single unified service.



Two environment notes
Tailwind v4 → v3: Your network kept resetting (ECONNRESET) on the v4 lightningcss native Windows binary, so I used the pure-JS Tailwind v3 toolchain (no native dep). Layout/features are unaffected.
Indian stocks (yfinance) returned empty here due to a corporate TLS-intercepting proxy (CERTIFICATE_VERIFY_FAILED against Yahoo) — the same network condition above. The code handles it gracefully and works on standard networks and cloud deploys. I deliberately did not disable SSL verification (security). Crypto is unaffected and fully working.


File	Contents
README.md	Index + quick links
01-overview.md	Features, tech stack, glossary, supported symbols
02-architecture.md	System design, data-flow, Mermaid diagrams, design decisions, concurrency model
03-backend.md	Every module/class, request lifecycle, error handling
04-frontend.md	Components, services, signals, state, styling, build output
05-api-reference.md	REST endpoints + WebSocket protocol with examples
06-configuration.md	Every env var and config file
07-development.md	Setup, run, build, verification commands
08-deployment.md	Docker, Render, Railway, Fly.io, HF Spaces, split hosting
09-extending-data-sources.md	Step-by-step guide to plug in Binance/Alpaca/Zerodha/etc.
10-troubleshooting.md	Common issues (incl. the yfinance TLS and npm ECONNRESET cases) and fixes
