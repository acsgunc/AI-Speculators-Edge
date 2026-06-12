import { Injectable, effect, signal } from '@angular/core';
import {
  CHART_COUNTS,
  ChartCount,
  DashboardConfig,
  Interval,
  PaneConfig,
} from '../models/market';

const STORAGE_KEY = 'live-dashboard.config.v1';

/** Default symbols cycled through when new panes are created. */
const DEFAULT_SYMBOLS = ['BTC', 'ETH', 'SOL', 'RELIANCE.NS', 'INFY.NS', 'TCS.NS', 'AVAX', 'HDFCBANK.NS'];

/**
 * Owns the dashboard layout (chart count + per-pane config) and transparently
 * persists every change to `localStorage`, so the user's last setup is restored
 * on reload.
 */
@Injectable({ providedIn: 'root' })
export class DashboardStateService {
  /** Reactive dashboard configuration. */
  readonly config = signal<DashboardConfig>(this.load());

  constructor() {
    // Persist on any change to the configuration.
    effect(() => this.persist(this.config()));
  }

  /** Change the number of visible charts, growing/shrinking the pane list. */
  setChartCount(count: ChartCount): void {
    this.config.update((cfg) => {
      const panes = [...cfg.panes];
      while (panes.length < count) {
        panes.push(this.createPane(panes.length));
      }
      panes.length = count;
      return { chartCount: count, panes };
    });
  }

  /** Update the symbol for a single pane. */
  setPaneSymbol(id: string, symbol: string): void {
    this.updatePane(id, (pane) => ({ ...pane, symbol }));
  }

  /** Update the interval for a single pane. */
  setPaneInterval(id: string, interval: Interval): void {
    this.updatePane(id, (pane) => ({ ...pane, interval }));
  }

  private updatePane(id: string, fn: (pane: PaneConfig) => PaneConfig): void {
    this.config.update((cfg) => ({
      ...cfg,
      panes: cfg.panes.map((pane) => (pane.id === id ? fn(pane) : pane)),
    }));
  }

  private createPane(index: number): PaneConfig {
    return {
      id: `pane-${index}-${crypto.randomUUID()}`,
      symbol: DEFAULT_SYMBOLS[index % DEFAULT_SYMBOLS.length],
      interval: '1m',
    };
  }

  private load(): DashboardConfig {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as DashboardConfig;
        if (this.isValid(parsed)) {
          return parsed;
        }
      }
    } catch {
      /* fall through to defaults */
    }
    return this.defaults();
  }

  private isValid(cfg: DashboardConfig): boolean {
    return (
      !!cfg &&
      (CHART_COUNTS as readonly number[]).includes(cfg.chartCount) &&
      Array.isArray(cfg.panes) &&
      cfg.panes.length === cfg.chartCount
    );
  }

  private defaults(): DashboardConfig {
    const chartCount: ChartCount = 4;
    return {
      chartCount,
      panes: Array.from({ length: chartCount }, (_, i) => this.createPane(i)),
    };
  }

  private persist(cfg: DashboardConfig): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
    } catch {
      /* storage may be unavailable (private mode); ignore */
    }
  }
}
