import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { CHART_COUNTS, ChartCount, SymbolGroups } from '../../models/market';
import { MarketDataService } from '../../services/market-data.service';
import { DashboardStateService } from '../../services/dashboard-state.service';
import { ChartPane } from '../chart-pane/chart-pane';

/**
 * Top-level dashboard: a chart-count selector plus a responsive grid of
 * independent {@link ChartPane} instances. Layout adapts to the selected count
 * and the selection is persisted via {@link DashboardStateService}.
 */
@Component({
  selector: 'app-dashboard',
  imports: [ChartPane],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dashboard.html',
})
export class Dashboard {
  private readonly marketData = inject(MarketDataService);
  protected readonly state = inject(DashboardStateService);

  protected readonly chartCounts = CHART_COUNTS;
  protected readonly symbolGroups = signal<SymbolGroups | null>(null);

  /** Responsive Tailwind grid template for the active chart count. */
  protected readonly gridClass = computed(() => {
    switch (this.state.config().chartCount) {
      case 1:
        return 'grid-cols-1';
      case 2:
        return 'grid-cols-1 sm:grid-cols-2';
      case 4:
        return 'grid-cols-1 sm:grid-cols-2';
      case 6:
        return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
      case 8:
        return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4';
      default:
        return 'grid-cols-1 sm:grid-cols-2';
    }
  });

  constructor() {
    this.marketData
      .getSymbols()
      .pipe(takeUntilDestroyed())
      .subscribe({
        next: (groups) => this.symbolGroups.set(groups),
        error: () => this.symbolGroups.set({ crypto: [], indian_stock: [], us_stock: [] }),
      });
  }

  protected setChartCount(count: ChartCount): void {
    this.state.setChartCount(count);
  }
}
