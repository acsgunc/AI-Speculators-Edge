# 04 — Frontend

Angular 21 single-page app using standalone components, signals, zoneless change
detection, Tailwind CSS, and TradingView Lightweight Charts.

## Directory

```
frontend/src/
├── environments/
│   ├── environment.ts                 # production (same-origin)
│   └── environment.development.ts     # dev (localhost:8000)
├── app/
│   ├── app.ts                         # root component → <app-dashboard/>
│   ├── app.config.ts                  # providers (HttpClient)
│   ├── models/
│   │   └── market.ts                  # shared TS interfaces & constants
│   ├── services/
│   │   ├── app-config.service.ts      # runtime API/WS base resolution
│   │   ├── market-data.service.ts     # REST client
│   │   ├── stream.service.ts          # WebSocket client
│   │   └── dashboard-state.service.ts # persisted layout state
│   └── components/
│       ├── dashboard/                 # toolbar + responsive grid
│       ├── chart-pane/                # one chart + controls + stream
│       └── ticker-bar/                # flashing price bar
├── index.html
└── styles.css                         # Tailwind + globals
```

## Models — `models/market.ts`

Mirror of the backend Pydantic models, plus UI constants:

```ts
type AssetClass = 'crypto' | 'indian_stock';
interface Candle { time; open; high; low; close; volume; }
interface SymbolInfo { symbol; label; asset_class; provider; }
interface SymbolGroups { crypto: SymbolInfo[]; indian_stock: SymbolInfo[]; }
interface HistoryResponse { symbol; interval; candles: Candle[]; }

const INTERVALS = ['1m','5m','15m','1h','1d'];   type Interval = ...
const CHART_COUNTS = [1,2,4,6,8];                type ChartCount = ...

type StreamMessage = TickMessage | CandleMessage | ErrorMessage;
interface PaneConfig { id; symbol; interval; }
interface DashboardConfig { chartCount; panes: PaneConfig[]; }
```

## Services

### `AppConfigService`
Resolves base URLs at runtime. When `environment` bases are empty (production /
unified service) it derives them from `window.location` (and upgrades `ws:` →
`wss:` on HTTPS).

| Property | Dev value | Prod value |
| --- | --- | --- |
| `apiBase` | `http://localhost:8000` | `window.location.origin` |
| `wsBase` | `ws://localhost:8000` | derived `ws(s)://host` |

### `MarketDataService`
REST client using `HttpClient`.

| Method | Endpoint |
| --- | --- |
| `getSymbols(): Observable<SymbolGroups>` | `GET /api/symbols` |
| `getHistory(symbol, interval): Observable<HistoryResponse>` | `GET /api/history` |

### `StreamService`
Wraps the WebSocket bridge. `connect(symbol, interval)` returns an `Observable`
that opens a socket, sends the subscribe frame on `open`, emits parsed
`StreamMessage`s, and **closes the socket on unsubscribe** (teardown function).

### `DashboardStateService`
Owns the dashboard config in a signal and persists it.

| Member | Description |
| --- | --- |
| `config: Signal<DashboardConfig>` | Reactive source of truth. |
| `setChartCount(count)` | Grows/shrinks the pane list to `count`. |
| `setPaneSymbol(id, symbol)` | Updates one pane's symbol. |
| `setPaneInterval(id, interval)` | Updates one pane's interval. |

Internals:
- `effect()` writes to `localStorage` (`live-dashboard.config.v1`) on any change.
- `load()` restores + validates saved config; falls back to `defaults()`
  (4 charts) when missing/invalid.
- `createPane(index)` assigns a UUID id and a default symbol cycled from a seed
  list.

## Components

### `App` (root)
Minimal shell: `template: '<app-dashboard />'`, `OnPush`.

### `Dashboard`
- Renders the **chart-count selector** (1/2/4/6/8) and a **responsive grid**.
- Loads symbol groups once via `MarketDataService.getSymbols()`.
- `gridClass()` computed signal maps chart count → Tailwind grid classes:

  | Count | Classes |
  | --- | --- |
  | 1 | `grid-cols-1` |
  | 2 | `grid-cols-1 sm:grid-cols-2` |
  | 4 | `grid-cols-1 sm:grid-cols-2` (2×2 via `auto-rows-fr`) |
  | 6 | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` |
  | 8 | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` |

- Iterates `state.config().panes` with `@for (... track pane.id)`.

### `ChartPane`
The most complex component. Inputs: `pane: PaneConfig`, `symbolGroups`.

Responsibilities:
- Creates the Lightweight chart in `afterNextRender()` (DOM-ready).
- `effect()` watches `pane()` symbol/interval → calls `loadAndStream()` on change.
- `loadAndStream()`: unsubscribes any prior stream, fetches history
  (`setData` + `fitContent`), then opens the live stream.
- Live `candle` messages → `series.update(...)`; `tick` messages → `updatePrice()`.
- `updatePrice()` compares to `lastPrice` to set `direction` (`up`/`down`).
- Emits control changes back to `DashboardStateService` (so they persist).
- Cleans up chart + subscription on destroy.

Signals: `price`, `direction`, `loading`, `errorText`, plus `label` computed
from the symbol groups.

### `TickerBar`
Pure presentational, `OnPush`. Inputs: `label`, `price`, `direction`.
- `containerClasses()` → green / red / slate background by direction.
- `formattedPrice()` → locale number with adaptive precision.
- `arrow()` → ▲ / ▼ / •.
- `.flash-transition` (in `styles.css`) animates the background color change.

## Change detection & reactivity

- **Zoneless:** Angular 21 default — no `zone.js`. UI updates are driven by
  **signals** and `OnPush`.
- Each pane is self-contained; there is no shared mutable chart state.
- RxJS subscriptions use `takeUntilDestroyed`/`DestroyRef` to avoid leaks.

## Styling

- Tailwind v3 via PostCSS (`.postcssrc.json`, `tailwind.config.js`).
- `styles.css` imports Tailwind layers and sets a dark theme + the
  `.flash-transition` helper.
- Dark color scheme throughout (`#0b0e11` / `#0f141a`).

## Build output

`npm run build` → `dist/live-dashboard/browser/` (this is the path the backend
serves via `FRONTEND_DIST`).
