# 10 — Troubleshooting

## Indian stock data is empty / `CERTIFICATE_VERIFY_FAILED`

**Symptom:** `/api/history?symbol=RELIANCE.NS` returns `"candles": []`; logs show
`SSLError(... self-signed certificate in certificate chain ...)` for
`fc.yahoo.com`.

**Cause:** `yfinance` calls Yahoo Finance over HTTPS. On corporate/proxied
networks that intercept TLS with a self-signed root certificate, verification
fails.

**Fix / workaround:**
- The app handles this gracefully (no crash) — it just yields no data.
- It works normally on standard networks and in cloud deployments.
- If you must run behind a TLS-intercepting proxy, install the corporate root
  CA into the system/Python trust store (e.g. via `pip install pip-system-certs`
  or pointing `SSL_CERT_FILE`/`REQUESTS_CA_BUNDLE` at the corporate bundle).
- **Do not** disable TLS verification globally — it's a security risk.
- Crypto data is unaffected.

## `npm install` fails with `ECONNRESET`

**Symptom:** native binary downloads (e.g. `lightningcss`) reset mid-download.

**Cause:** flaky/proxied network dropping large binary fetches.

**Fix:**
- Retry with reduced concurrency and more retries:
  ```bash
  npm install --maxsockets=2 --fetch-retries=8 --fetch-retry-mintimeout=10000
  ```
- This project uses **Tailwind v3** (pure JS, no native `lightningcss` binary)
  specifically to avoid this class of failure.

## Build error: `Cannot find module '../lightningcss.win32-x64-msvc.node'`

**Cause:** Tailwind v4's `lightningcss` native binary wasn't installed.

**Fix:** the project is configured for **Tailwind v3** (`tailwind.config.js`,
`.postcssrc.json` referencing `tailwindcss` + `autoprefixer`). Ensure you have:
```bash
npm ls tailwindcss   # should show 3.x
```
If you see `@tailwindcss/postcss` (v4), remove it and reinstall v3 deps.

## Charts are blank / no live updates

Check, in order:
1. **Backend running?** `curl http://localhost:8000/api/health`.
2. **CORS** — for split hosting, `CORS_ORIGINS` must include the SPA origin.
3. **WebSocket base** — in production behind HTTPS, the client uses `wss:`. Make
   sure the platform terminates TLS and proxies WebSockets.
4. **Browser console** — look for failed `GET /api/history` or WS errors.
5. **Symbol owned?** Unknown symbols return `404` (REST) or an `error` message
   (WS).

## WebSocket connects then drops repeatedly

- Free tiers may recycle idle/long sockets. The crypto source reconnects
  automatically; panes re-subscribe on reconnect.
- Check the platform's WebSocket/idle-timeout settings.

## Build warning: `Unable to initialize JavaScript cache storage` (lmdb)

**Symptom:** `No native build was found ... lmdb` during `ng build`.

**Impact:** none on output — only disables an on-disk build cache, making builds
slightly slower. Safe to ignore.

## Port already in use

```bash
# Change the backend port
uvicorn app.main:app --port 8001
```
Then update `apiBase`/`wsBase` in `environment.development.ts` if you changed it
for local dev.

## Dashboard won't reset / stale layout

The layout is cached in `localStorage` under `live-dashboard.config.v1`. Clear
it via DevTools → Application → Local Storage, or:
```js
localStorage.removeItem('live-dashboard.config.v1');
```

## `python -m app.main` can't find the app

Run it from the `backend/` directory (so `app` is importable), with the venv
activated and dependencies installed.

## Getting more detail

- Increase backend logging: `uvicorn app.main:app --log-level debug`.
- Inspect the live API at `/docs` (Swagger UI).
- Validate the wire contract against [05 — API Reference](05-api-reference.md).
