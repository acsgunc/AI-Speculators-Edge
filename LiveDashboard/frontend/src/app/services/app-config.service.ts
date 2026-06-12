import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * Resolves the HTTP and WebSocket base URLs at runtime.
 *
 * When the environment bases are empty (production / unified service) the URLs
 * are derived from `window.location`, so the same build works whether the SPA
 * is served by FastAPI or by a dedicated host.
 */
@Injectable({ providedIn: 'root' })
export class AppConfigService {
  /** Absolute base for REST calls, e.g. `http://localhost:8000`. */
  readonly apiBase: string = environment.apiBase || window.location.origin;

  /** Absolute base for WebSocket calls, e.g. `ws://localhost:8000`. */
  readonly wsBase: string = environment.wsBase || this.deriveWsBase();

  private deriveWsBase(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }
}
