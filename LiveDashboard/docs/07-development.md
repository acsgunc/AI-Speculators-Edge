# 07 — Local Development

## Prerequisites

| Tool | Version | Check |
| --- | --- | --- |
| Python | 3.10+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 9+ | `npm --version` |

> The project was built and verified with Python 3.13, Node 22, npm 11, and
> Angular CLI 21.

## First-time setup

### Backend
```bash
cd backend
python -m venv .venv

# Activate the venv
.venv\Scripts\activate         # Windows (cmd/PowerShell)
source .venv/bin/activate       # macOS / Linux / Git Bash

pip install -r requirements.txt
cp .env.example .env            # optional — defaults work out of the box
```

### Frontend
```bash
cd frontend
npm install
```

## Run (two terminals)

**Terminal 1 — backend**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>

**Terminal 2 — frontend**
```bash
cd frontend
npm start
```
- App: <http://localhost:4200> (proxies data calls to `localhost:8000`).

## Common commands

### Frontend
| Command | Description |
| --- | --- |
| `npm start` | Dev server with HMR (`environment.development.ts`). |
| `npm run build` | Production build → `dist/live-dashboard/browser/`. |
| `npm run watch` | Rebuild on change (development config). |

### Backend
| Command | Description |
| --- | --- |
| `uvicorn app.main:app --reload --port 8000` | Dev server, auto-reload. |
| `python -m app.main` | Run via the module entry point (uses env `HOST`/`PORT`/`RELOAD`). |

## Verifying the stack

```bash
# Health
curl http://localhost:8000/api/health

# Symbols
curl http://localhost:8000/api/symbols

# Crypto history (live)
curl "http://localhost:8000/api/history?symbol=BTC&interval=1m"
```

WebSocket smoke test (Python):
```python
import asyncio, json, websockets
async def main():
    async with websockets.connect("ws://localhost:8000/ws/stream") as ws:
        await ws.send(json.dumps({"action":"subscribe","symbol":"BTC","interval":"1m"}))
        for _ in range(3):
            print(json.loads(await ws.recv()))
asyncio.run(main())
```

## Running the unified service locally

To test the production layout (FastAPI serving the built SPA from one process):

```bash
cd frontend && npm run build          # produces dist/live-dashboard/browser
cd ../backend && uvicorn app.main:app --port 8000
```

Open <http://localhost:8000> — the SPA is served at `/` and the API at `/api/*`.
(`FRONTEND_DIST` defaults to the built SPA path.)

## Project layout recap

```
LiveDashboard/
├── backend/      # FastAPI service
├── frontend/     # Angular SPA
├── docs/         # this documentation
├── Dockerfile    # unified-service image
├── render.yaml   # Render blueprint
└── Procfile      # Railway/Heroku-style
```

## Coding conventions

- **Python:** full type hints, async/await throughout, docstrings on public
  members.
- **TypeScript:** strict typing, standalone components, signals over
  observables for view state, `OnPush` change detection.
- **No secrets in code** — everything sensitive comes from env vars.
