/**
 * Shared market-data domain types.
 *
 * These mirror the Pydantic models exposed by the FastAPI backend so the client
 * and server share a single, fully typed contract.
 */

/** High level asset grouping used by the symbol selector. */
export type AssetClass = 'crypto' | 'indian_stock';

/** A single OHLCV candle. `time` is a UNIX timestamp in seconds. */
export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** Metadata describing a tradable instrument. */
export interface SymbolInfo {
  symbol: string;
  label: string;
  asset_class: AssetClass;
  provider: string;
}

/** `/api/symbols` response: instruments grouped by asset class. */
export interface SymbolGroups {
  crypto: SymbolInfo[];
  indian_stock: SymbolInfo[];
}

/** `/api/history` response payload. */
export interface HistoryResponse {
  symbol: string;
  interval: string;
  candles: Candle[];
}

/** Supported charting intervals. */
export const INTERVALS = ['1m', '5m', '15m', '1h', '1d'] as const;
export type Interval = (typeof INTERVALS)[number];

/** Selectable chart-count options for the dashboard grid. */
export const CHART_COUNTS = [1, 2, 4, 6, 8] as const;
export type ChartCount = (typeof CHART_COUNTS)[number];

// --- WebSocket message envelope -------------------------------------------

export interface TickMessage {
  type: 'tick';
  symbol: string;
  price: number;
  time: number;
}

export interface CandleMessage {
  type: 'candle';
  symbol: string;
  interval: string;
  candle: Candle;
}

export interface ErrorMessage {
  type: 'error';
  detail: string;
}

export type StreamMessage = TickMessage | CandleMessage | ErrorMessage;

/** Per-pane persisted configuration. */
export interface PaneConfig {
  id: string;
  symbol: string;
  interval: Interval;
}

/** Full dashboard layout persisted to localStorage. */
export interface DashboardConfig {
  chartCount: ChartCount;
  panes: PaneConfig[];
}
