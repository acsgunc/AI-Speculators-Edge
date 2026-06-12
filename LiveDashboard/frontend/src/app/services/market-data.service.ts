import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AppConfigService } from './app-config.service';
import { HistoryResponse, SymbolGroups } from '../models/market';

/**
 * REST client for the FastAPI backend: symbol discovery and historical candles.
 */
@Injectable({ providedIn: 'root' })
export class MarketDataService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(AppConfigService);

  /** Fetch all tradable symbols grouped by asset class. */
  getSymbols(): Observable<SymbolGroups> {
    return this.http.get<SymbolGroups>(`${this.config.apiBase}/api/symbols`);
  }

  /** Fetch historical OHLCV candles for a symbol/interval pair. */
  getHistory(symbol: string, interval: string): Observable<HistoryResponse> {
    const params = new HttpParams().set('symbol', symbol).set('interval', interval);
    return this.http.get<HistoryResponse>(`${this.config.apiBase}/api/history`, { params });
  }
}
