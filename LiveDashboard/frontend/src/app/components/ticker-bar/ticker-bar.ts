import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
} from '@angular/core';

/** Direction of the most recent price change, used to drive the flash colour. */
export type PriceDirection = 'up' | 'down' | 'flat';

/**
 * Color-coded price ticker shown atop each chart pane.
 *
 * Flashes green when the price ticks up and red when it ticks down, based on
 * the live `price`/`direction` inputs fed from the WebSocket stream.
 */
@Component({
  selector: 'app-ticker-bar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="flash-transition flex items-center justify-between rounded-t-lg px-3 py-2"
      [class]="containerClasses()"
    >
      <span class="font-semibold tracking-wide">{{ label() }}</span>
      <div class="flex items-center gap-2">
        <span class="text-lg font-bold tabular-nums">{{ formattedPrice() }}</span>
        <span class="text-sm font-medium">{{ arrow() }}</span>
      </div>
    </div>
  `,
})
export class TickerBar {
  /** Display label, e.g. "Bitcoin (BTC)". */
  readonly label = input.required<string>();
  /** Latest price; `null` while loading. */
  readonly price = input<number | null>(null);
  /** Last tick direction. */
  readonly direction = input<PriceDirection>('flat');

  protected readonly formattedPrice = computed(() => {
    const value = this.price();
    if (value === null || Number.isNaN(value)) {
      return '—';
    }
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: value < 10 ? 4 : 2,
    });
  });

  protected readonly arrow = computed(() => {
    switch (this.direction()) {
      case 'up':
        return '▲';
      case 'down':
        return '▼';
      default:
        return '•';
    }
  });

  protected readonly containerClasses = computed(() => {
    switch (this.direction()) {
      case 'up':
        return 'bg-green-600/90 text-white';
      case 'down':
        return 'bg-red-600/90 text-white';
      default:
        return 'bg-slate-700/70 text-slate-100';
    }
  });
}
