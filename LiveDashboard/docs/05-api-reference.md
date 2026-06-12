# 05 — API Reference

Base URL (local dev): `http://localhost:8000`
Interactive docs (Swagger UI): `http://localhost:8000/docs`
OpenAPI schema: `http://localhost:8000/openapi.json`

---

## REST

### `GET /api/health`
Liveness probe used by the frontend and cloud platforms.

**Response `200`**
```json
{ "status": "ok" }
```

---

### `GET /api/symbols`
Returns all tradable instruments grouped by asset class.

**Response `200`**
```json
{
  "crypto": [
    { "symbol": "BTC", "label": "Bitcoin (BTC)", "asset_class": "crypto", "provider": "hyperliquid" }
  ],
  "indian_stock": [
    { "symbol": "RELIANCE.NS", "label": "Reliance Industries", "asset_class": "indian_stock", "provider": "yfinance" }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `symbol` | string | Provider-specific symbol. |
| `label` | string | Human-friendly name. |
| `asset_class` | `crypto` \| `indian_stock` | Grouping. |
| `provider` | string | Source `name` (e.g. `hyperliquid`). |

---

### `GET /api/history`
Historical OHLCV candles for one symbol/interval.

**Query parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `symbol` | string | yes | — | e.g. `BTC`, `RELIANCE.NS`. |
| `interval` | string | no | `1m` | One of `1m`, `5m`, `15m`, `1h`, `1d`. |

**Response `200`**
```json
{
  "symbol": "BTC",
  "interval": "1m",
  "candles": [
    { "time": 1781253420, "open": 63423.0, "high": 63423.0, "low": 63392.0, "close": 63397.0, "volume": 9.23962 }
  ]
}
```

> `time` is a **UNIX timestamp in seconds** (the format Lightweight Charts
> expects). Candles are returned **oldest first**.

**Errors**

| Status | When |
| --- | --- |
| `404` | No data source supports `symbol`. |
| `502` | Upstream provider error. |

**Example**
```bash
curl "http://localhost:8000/api/history?symbol=BTC&interval=1m"
```

---

## WebSocket

### `WS /ws/stream`
Live bridge for a single symbol/interval. **One socket per chart pane.**

**Protocol**

1. Connect to `ws://localhost:8000/ws/stream` (or `wss://` in production).
2. Send a subscribe message:
   ```json
   { "action": "subscribe", "symbol": "BTC", "interval": "1m" }
   ```
3. Receive a stream of messages until you disconnect.

**Outbound message types**

`candle` — full OHLCV update (redraw the latest bar):
```json
{
  "type": "candle",
  "symbol": "BTC",
  "interval": "1m",
  "candle": { "time": 1781253480, "open": 63398, "high": 63438, "low": 63398, "close": 63438, "volume": 10.6 }
}
```

`tick` — bare price update (flash the ticker bar):
```json
{ "type": "tick", "symbol": "BTC", "price": 63438.0, "time": 1781253480 }
```

`error` — problem report (e.g. unknown symbol); socket then closes:
```json
{ "type": "error", "detail": "No data source registered for symbol 'XYZ'" }
```

**Behavior notes**
- Crypto (Hyperliquid) pushes a `candle`+`tick` pair on each upstream candle
  frame, with automatic reconnect on socket drop.
- Indian stocks (yfinance) emit a `candle`+`tick` every `POLL_INTERVAL_SECONDS`.
- Closing the socket cancels the server-side pump task immediately.

**Minimal client example (browser)**
```js
const ws = new WebSocket('ws://localhost:8000/ws/stream');
ws.onopen = () => ws.send(JSON.stringify({ action: 'subscribe', symbol: 'BTC', interval: '1m' }));
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

**Minimal client example (Python)**
```python
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://localhost:8000/ws/stream") as ws:
        await ws.send(json.dumps({"action": "subscribe", "symbol": "BTC", "interval": "1m"}))
        async for raw in ws:
            print(json.loads(raw))

asyncio.run(main())
```
