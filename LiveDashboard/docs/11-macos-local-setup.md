# 11 — Running Locally on a MacBook (Complete Guide)

A step-by-step guide to run the Live Trading Dashboard on macOS from a **clean
machine** to a **running app** — covering Apple Silicon (M1/M2/M3/M4) and Intel
Macs. Nothing is skipped.

> If you just want the short version, see [07 — Local Development](07-development.md).
> This document is the exhaustive macOS walkthrough.

---

## 0. What you'll end up with

- **Backend (FastAPI)** running at <http://localhost:8000>
- **Frontend (Angular)** running at <http://localhost:4200>
- Live crypto charts streaming immediately; Indian stocks working on normal
  home/office networks.

Total time on a fresh Mac: ~15–25 minutes (mostly downloads).

---

## 1. Check your macOS and chip type

1. Click the  (Apple) menu → **About This Mac**.
2. Note the **Chip**:
   - "Apple M1/M2/M3/M4 …" → **Apple Silicon (arm64)**
   - "Intel Core …" → **Intel (x86_64)**
3. macOS 12 (Monterey) or newer is recommended.

You can also check from Terminal:

```bash
uname -m
# arm64  → Apple Silicon
# x86_64 → Intel
```

Open **Terminal** via Spotlight: press `⌘ + Space`, type `Terminal`, press
`Return`.

---

## 2. Install the Xcode Command Line Tools

These provide `git`, a C compiler, and headers many tools rely on.

```bash
xcode-select --install
```

- A dialog appears → click **Install** → **Agree**.
- If it says *"already installed"*, you're good.

Verify:

```bash
git --version
# git version 2.x.x
```

---

## 3. Install Homebrew (package manager)

Homebrew is the standard way to install developer tools on macOS.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts (it may ask for your Mac login password — typing shows
nothing, that's normal — then `Return`).

### 3a. Add Homebrew to your PATH (Apple Silicon only)

On Apple Silicon, Homebrew installs to `/opt/homebrew`. The installer prints two
commands at the end — run them (adjust if your shell differs):

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

> On Intel Macs Homebrew installs to `/usr/local` and is usually already on PATH.

Verify:

```bash
brew --version
# Homebrew 4.x.x
```

> macOS uses **zsh** by default (`~/.zprofile` / `~/.zshrc`). If you use bash,
> substitute `~/.bash_profile`.

---

## 4. Install Python 3.10+ and Node.js 20+

```bash
brew install python@3.12 node@22 git
```

This installs:
- **Python 3.12** (any 3.10+ works) — for the FastAPI backend.
- **Node.js 22** (any 20+ works) — for the Angular frontend.
- **git** — to clone the project (skip if already present).

### 4a. Verify versions

```bash
python3 --version
# Python 3.12.x   (must be >= 3.10)

node --version
# v22.x.x         (must be >= 20)

npm --version
# 10.x or 11.x
```

> If `python3` shows the old system Python (3.9.x), close and reopen Terminal,
> or ensure Homebrew's bin is first on PATH:
> ```bash
> echo 'export PATH="$(brew --prefix)/bin:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> ```

---

## 5. Get the project onto your Mac

Pick a working folder, e.g. your home directory.

**If you have a Git URL:**

```bash
cd ~
git clone <your-repo-url> LiveDashboard
cd LiveDashboard
```

**If you already have the folder** (e.g. copied over), just `cd` into it:

```bash
cd ~/path/to/LiveDashboard
```

Confirm you're in the right place — you should see `backend/`, `frontend/`,
`docs/`, `Dockerfile`:

```bash
ls
# Dockerfile  Procfile  README.md  backend  docs  frontend  render.yaml
```

---

## 6. Set up and run the backend (Terminal window #1)

### 6a. Create and activate a virtual environment

A virtual environment keeps the project's Python packages isolated.

```bash
cd ~/LiveDashboard/backend
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt now starts with `(.venv)`. To leave the venv later, type
`deactivate`.

> **Every new Terminal tab** that runs the backend must re-run
> `source .venv/bin/activate` first.

### 6b. Upgrade pip and install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, websockets, httpx, yfinance, pydantic, and
python-dotenv. It may take a few minutes.

### 6c. (Optional) Create a local `.env`

Defaults work out of the box, so this is optional:

```bash
cp .env.example .env
```

Edit `.env` only if you need to change ports/CORS (see
[06 — Configuration](06-configuration.md)).

### 6d. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

You should see Uvicorn start and `Application startup complete`. Leave this
window running.

- API base: <http://localhost:8000>
- Interactive docs (Swagger UI): <http://localhost:8000/docs>

> **macOS note:** the first time you run it, macOS may pop up
> *"Do you want the application 'Python' to accept incoming network
> connections?"* → click **Allow** (needed for the local servers).

### 6e. Quick backend check (new tab, optional)

Open a new Terminal tab (`⌘ + T`) and run:

```bash
curl http://localhost:8000/api/health
# {"status":"ok"}

curl "http://localhost:8000/api/history?symbol=BTC&interval=1m" | head -c 200
# {"symbol":"BTC","interval":"1m","candles":[ ... ]}
```

If both return data, the backend is healthy.

---

## 7. Set up and run the frontend (Terminal window #2)

Open a **second Terminal window** (`⌘ + N`) — keep the backend running in the
first.

### 7a. Install npm dependencies

```bash
cd ~/LiveDashboard/frontend
npm install
```

This downloads Angular, Tailwind, and Lightweight Charts. First run can take a
few minutes.

> If you ever hit a flaky download (`ECONNRESET`), retry with:
> ```bash
> npm install --maxsockets=2 --fetch-retries=8
> ```

### 7b. Start the Angular dev server

```bash
npm start
```

Wait for `Application bundle generation complete` and a line like
`➜  Local:   http://localhost:4200/`.

### 7c. Open the app

In your browser go to:

```
http://localhost:4200
```

You should see the dashboard with live crypto charts. The dev server talks to
the backend on `localhost:8000` automatically (configured in
`src/environments/environment.development.ts`).

---

## 8. Using the app

- **Number of Charts** selector (top right): choose **1, 2, 4, 6, 8** — the grid
  reshapes responsively.
- **Per chart:**
  - **Symbol dropdown** — grouped into *Crypto* and *Indian Stocks*.
  - **Timeframe** — `1m`, `5m`, `15m`, `1h`, `1d`.
- **Ticker bar** flashes **green** on an uptick and **red** on a downtick.
- Your layout (count + each pane's symbol/timeframe) is saved to `localStorage`
  and restored on reload.

---

## 9. Stopping and restarting

### Stop
- In each Terminal window press `Control + C`.
- Deactivate the backend venv if you want: `deactivate`.

### Restart later (the short version)

**Terminal 1 — backend**
```bash
cd ~/LiveDashboard/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend**
```bash
cd ~/LiveDashboard/frontend
npm start
```

Then open <http://localhost:4200>.

---

## 10. Optional: run it the "production" way (single service)

Test the unified setup where FastAPI serves the built Angular app from **one**
process (no separate dev server).

```bash
# 1. Build the frontend
cd ~/LiveDashboard/frontend
npm run build          # outputs dist/live-dashboard/browser

# 2. Run the backend (serves the built SPA automatically)
cd ~/LiveDashboard/backend
source .venv/bin/activate
uvicorn app.main:app --port 8000
```

Now open <http://localhost:8000> — the whole app (UI + API + WebSocket) runs on
that single port. (`FRONTEND_DIST` already points at the built SPA by default.)

---

## 11. macOS-specific troubleshooting

### "command not found: brew"
Homebrew isn't on PATH. Re-run the Apple Silicon PATH step in **3a**, then open a
new Terminal.

### "command not found: python3" or wrong Python version
Ensure Homebrew's bin is first on PATH:
```bash
echo 'export PATH="$(brew --prefix)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
python3 --version
```

### `python3 -m venv` fails
Reinstall Python and retry:
```bash
brew reinstall python@3.12
```

### "Operation not permitted" creating files
You're likely in a protected folder (Desktop/Documents may need permission, or
you used `sudo` earlier). Work under your home directory (`~/LiveDashboard`) and
don't use `sudo` for `pip`/`npm`.

### macOS firewall keeps prompting
System Settings → **Network** → **Firewall** → allow incoming connections for
Python/Node, or temporarily turn the firewall off for local development.

### Port 8000 or 4200 already in use
Find and stop the process, or use another port:
```bash
lsof -i :8000          # see what's using it
kill -9 <PID>          # stop it
# or run on a different port:
uvicorn app.main:app --reload --port 8001
```
If you change the backend port, update `apiBase`/`wsBase` in
`src/environments/environment.development.ts` and restart `npm start`.

### Indian stocks show no data (`CERTIFICATE_VERIFY_FAILED`)
This happens on networks that intercept TLS (some corporate VPNs/proxies).
`yfinance` can't verify Yahoo's certificate. It works on normal home networks
and in the cloud. Crypto is unaffected. If you must fix it on a corporate
network, install your org's root CA into the trust store:
```bash
pip install certifi
# then point Python at the corporate bundle if required:
export SSL_CERT_FILE="$(python3 -m certifi)"
```
Do **not** disable TLS verification globally. See
[10 — Troubleshooting](10-troubleshooting.md).

### `xcrun: error: invalid active developer path`
The Command Line Tools need a refresh:
```bash
xcode-select --install
```

### npm download errors (`ECONNRESET`)
Retry with reduced concurrency:
```bash
npm install --maxsockets=2 --fetch-retries=8 --fetch-retry-mintimeout=10000
```

---

## 12. Full command cheat-sheet (copy/paste)

Fresh Mac, from zero to running:

```bash
# --- Prerequisites ---
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile   # Apple Silicon
eval "$(/opt/homebrew/bin/brew shellenv)"                          # Apple Silicon
brew install python@3.12 node@22 git

# --- Get the project ---
cd ~
git clone <your-repo-url> LiveDashboard    # or cd into your existing copy

# --- Backend (Terminal 1) ---
cd ~/LiveDashboard/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# --- Frontend (Terminal 2) ---
cd ~/LiveDashboard/frontend
npm install
npm start
# open http://localhost:4200
```

---

## 13. Where to go next

- Configure ports/CORS: [06 — Configuration](06-configuration.md)
- Understand the code: [03 — Backend](03-backend.md), [04 — Frontend](04-frontend.md)
- API contract: [05 — API Reference](05-api-reference.md)
- Add a new data provider: [09 — Extending](09-extending-data-sources.md)
- Deploy to the cloud: [08 — Deployment](08-deployment.md)
