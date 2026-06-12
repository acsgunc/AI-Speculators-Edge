import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AppConfigService } from './app-config.service';
import { StreamMessage } from '../models/market';

/**
 * Thin wrapper around the backend WebSocket bridge (`/ws/stream`).
 *
 * Each call to {@link connect} opens an independent socket scoped to a single
 * symbol/interval, matching the "one stream per chart pane" model. The returned
 * Observable emits parsed {@link StreamMessage} payloads and tears the socket
 * down automatically on unsubscribe.
 */
@Injectable({ providedIn: 'root' })
export class StreamService {
  private readonly config = inject(AppConfigService);

  /** Open a live stream for `symbol`/`interval`. */
  connect(symbol: string, interval: string): Observable<StreamMessage> {
    return new Observable<StreamMessage>((subscriber) => {
      const socket = new WebSocket(`${this.config.wsBase}/ws/stream`);

      socket.addEventListener('open', () => {
        socket.send(JSON.stringify({ action: 'subscribe', symbol, interval }));
      });

      socket.addEventListener('message', (event) => {
        try {
          subscriber.next(JSON.parse(event.data) as StreamMessage);
        } catch {
          /* ignore malformed frames */
        }
      });

      socket.addEventListener('error', () => {
        subscriber.next({ type: 'error', detail: 'WebSocket connection error' });
      });

      // Teardown: close the socket when the consumer unsubscribes.
      return () => {
        if (
          socket.readyState === WebSocket.OPEN ||
          socket.readyState === WebSocket.CONNECTING
        ) {
          socket.close();
        }
      };
    });
  }
}
