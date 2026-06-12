import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  effect,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';
import {
  CandlestickSeries,
  ColorType,
  IChartApi,
  ISeriesApi,
  UTCTimestamp,
  createChart,
} from 'lightweight-charts';

import {
  Candle,
  INTERVALS,
  Interval,
  PaneConfig,
  SymbolGroups,
} from '../../models/market';
import { MarketDataService } from '../../services/market-data.service';
import { StreamService } from '../../services/stream.service';
import { DashboardStateService } from '../../services/dashboard-state.service';
import { PriceDirection, TickerBar } from '../ticker-bar/ticker-bar';

/**
 * A single self-contained trading chart.
 *
 * Owns its own symbol/timeframe selectors, a TradingView Lightweight Chart, a
 * historical data load and a live WebSocket stream. Changing the symbol or
 * interval transparently reloads history and reconnects the stream.
 */
@Component({
  selector: 'app-chart-pane',
  imports: [TickerBar],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './chart-pane.html',
})
export class ChartPane {
  /** Persisted configuration for this pane. */
  readonly pane = input.required<PaneConfig>();
  /** Available symbols grouped by asset class (for the dropdown). */
  readonly symbolGroups = input<SymbolGroups | null>(null);

  private readonly marketData = inject(MarketDataService);
  private readonly stream = inject(StreamService);
  private readonly state = inject(DashboardStateService);
  private readonly destroyRef = inject(DestroyRef);

  private readonly chartContainer =
    viewChild.required<ElementRef<HTMLDivElement>>('chartContainer');

  private chart?: IChartApi;
  private series?: ISeriesApi<'Candlestick'>;
  private streamSub?: Subscription;
  private lastPrice: number | null = null;

  protected readonly intervals = INTERVALS;
  protected readonly price = signal<number | null>(null);
  protected readonly direction = signal<PriceDirection>('flat');
  protected readonly loading = signal(false);
  protected readonly errorText = signal<string | null>(null);

  /** Human friendly label for the active symbol, resolved from the groups. */
  protected readonly label = computed(() => {
    const groups = this.symbolGroups();
    const symbol = this.pane().symbol;
    const all = [...(groups?.crypto ?? []), ...(groups?.indian_stock ?? [])];
    return all.find((s) => s.symbol === symbol)?.label ?? symbol;
  });

  constructor() {
    // Create the chart once the view container is in the DOM.
    afterNextRender(() => this.initChart());

    // Reload history + reconnect whenever symbol or interval changes.
    effect(() => {
      const { symbol, interval } = this.pane();
      // Touch dependencies so the effect re-runs on change.
      void symbol;
      void interval;
      if (this.series) {
        this.loadAndStream();
      }
    });

    this.destroyRef.onDestroy(() => this.teardown());
  }

  protected onSymbolChange(event: Event): void {
    const symbol = (event.target as HTMLSelectElement).value;
    this.state.setPaneSymbol(this.pane().id, symbol);
  }

  protected onIntervalChange(interval: Interval): void {
    this.state.setPaneInterval(this.pane().id, interval);
  }

  // --- Chart lifecycle ----------------------------------------------------

  private initChart(): void {
    const el = this.chartContainer().nativeElement;
    this.chart = createChart(el, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: '#0f141a' },
        textColor: '#cbd5e1',
        fontFamily: "'Inter', system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: 'rgba(148, 163, 184, 0.08)' },
        horzLines: { color: 'rgba(148, 163, 184, 0.08)' },
      },
      rightPriceScale: { borderColor: 'rgba(148, 163, 184, 0.2)' },
      timeScale: {
        borderColor: 'rgba(148, 163, 184, 0.2)',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: 0 },
    });

    this.series = this.chart.addSeries(CandlestickSeries, {
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
    });

    this.loadAndStream();
  }

  /** Load historical candles and (re)open the live stream for the pane. */
  private loadAndStream(): void {
    const { symbol, interval } = this.pane();
    this.streamSub?.unsubscribe();
    this.errorText.set(null);
    this.loading.set(true);
    this.lastPrice = null;
    this.direction.set('flat');

    this.marketData
      .getHistory(symbol, interval)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          this.applyHistory(res.candles);
          this.openStream(symbol, interval);
        },
        error: () => {
          this.loading.set(false);
          this.errorText.set('Failed to load history');
          // Still try the live stream so the pane can recover.
          this.openStream(symbol, interval);
        },
      });
  }

  private applyHistory(candles: Candle[]): void {
    if (!this.series) {
      return;
    }
    this.series.setData(
      candles.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );
    this.chart?.timeScale().fitContent();
    const last = candles.at(-1);
    if (last) {
      this.price.set(last.close);
      this.lastPrice = last.close;
    }
  }

  private openStream(symbol: string, interval: string): void {
    this.streamSub = this.stream.connect(symbol, interval).subscribe((msg) => {
      // Ignore frames for a stale symbol after a quick switch.
      if (this.pane().symbol !== symbol) {
        return;
      }
      if (msg.type === 'candle') {
        this.series?.update({
          time: msg.candle.time as UTCTimestamp,
          open: msg.candle.open,
          high: msg.candle.high,
          low: msg.candle.low,
          close: msg.candle.close,
        });
      } else if (msg.type === 'tick') {
        this.updatePrice(msg.price);
      } else if (msg.type === 'error') {
        this.errorText.set(msg.detail);
      }
    });
  }

  private updatePrice(next: number): void {
    if (this.lastPrice !== null) {
      if (next > this.lastPrice) {
        this.direction.set('up');
      } else if (next < this.lastPrice) {
        this.direction.set('down');
      }
    }
    this.lastPrice = next;
    this.price.set(next);
  }

  private teardown(): void {
    this.streamSub?.unsubscribe();
    this.chart?.remove();
    this.chart = undefined;
    this.series = undefined;
  }
}
