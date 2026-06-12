# 06 — Configuration

## Backend environment variables

Loaded by `app/config.py` via `python-dotenv`. Copy `backend/.env.example` to
`backend/.env` for local overrides; cloud platforms inject these directly.

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `HOST` | string | `0.0.0.0` | Bind address for Uvicorn. |
| `PORT` | int | `8000` | Bind port. Most PaaS platforms inject this. |
| `RELOAD` | `0`/`1` | `0` | Auto-reload on code change (dev only). |
| `CORS_ORIGINS` | CSV | `*` | Allowed origins. Use exact origin(s) in prod. |
| `FRONTEND_DIST` | path | `../frontend/dist/live-dashboard/browser` | Built SPA dir; served at `/` when it exists. |
| `HYPERLIQUID_WS_URL` | url | `wss://api.hyperliquid.xyz/ws` | Crypto WebSocket endpoint. |
| `HYPERLIQUID_REST_URL` | url | `https://api.hyperliquid.xyz/info` | Crypto REST endpoint. |
| `POLL_INTERVAL_SECONDS` | float | `5` | yfinance polling cadence. |

### Notes
- **`CORS_ORIGINS`** accepts a comma-separated list, e.g.
  `https://my-app.onrender.com,https://example.com`. `*` is convenient locally.
- **`FRONTEND_DIST`** — set to a non-existent path (e.g. `__none__`) to run the
  backend API-only without serving the SPA.
- **`RELOAD=1`** is for development; keep it `0` in production.

### Example `.env`
```env
HOST=0.0.0.0
PORT=8000
RELOAD=1
CORS_ORIGINS=*
FRONTEND_DIST=../frontend/dist/live-dashboard/browser
HYPERLIQUID_WS_URL=wss://api.hyperliquid.xyz/ws
HYPERLIQUID_REST_URL=https://api.hyperliquid.xyz/info
POLL_INTERVAL_SECONDS=5
```

## Frontend environments

Angular swaps these via `fileReplacements` in `angular.json`.

### `src/environments/environment.ts` (production)
```ts
export const environment = {
  production: true,
  apiBase: '',   // empty → same origin as the served SPA
  wsBase: '',    // empty → derived from window.location at runtime
};
```

### `src/environments/environment.development.ts` (development)
```ts
export const environment = {
  production: false,
  apiBase: 'http://localhost:8000',
  wsBase: 'ws://localhost:8000',
};
```

| Build configuration | File used | Effect |
| --- | --- | --- |
| `ng serve` (development) | `environment.development.ts` | Talks to `localhost:8000`. |
| `ng build` (production) | `environment.ts` | Same-origin; works behind the unified service. |

### Pointing the dev frontend at a different backend
Edit `apiBase`/`wsBase` in `environment.development.ts` (e.g. a remote dev API),
then restart `npm start`.

## Build & tooling config files

| File | Purpose |
| --- | --- |
| `frontend/angular.json` | Build/serve targets, `fileReplacements`, budgets. |
| `frontend/tailwind.config.js` | Tailwind v3 `content` globs. |
| `frontend/.postcssrc.json` | Registers `tailwindcss` + `autoprefixer`. |
| `frontend/tsconfig*.json` | TypeScript compiler options. |
| `backend/requirements.txt` | Pinned Python dependencies. |

## Storage key (frontend)

`DashboardStateService` persists to `localStorage` under:

```
live-dashboard.config.v1
```

Clearing this key (or browser storage) resets the dashboard to defaults
(4 charts). The `.v1` suffix allows future migrations without clobbering.
