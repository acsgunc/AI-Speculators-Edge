# 09 — Extending: Adding a New Data Source

The backend's pluggable architecture means adding a broker/provider (Binance,
Alpaca, Zerodha, Polygon, …) requires **one new class** and **one registry
line**. Nothing in the routing, models, or frontend changes.

## The contract

Subclass `DataSource` (in `backend/app/data_source.py`) and implement four
members plus two attributes:

```python
class DataSource(ABC):
    name: str                       # stable provider id (shown to UI)
    asset_class: AssetClass         # crypto | indian_stock (extend enum if needed)

    def list_symbols(self) -> list[SymbolInfo]: ...
    def supports(self, symbol: str) -> bool: ...
    async def get_history(self, symbol: str, interval: str) -> list[Candle]: ...
    def stream(self, symbol: str, interval: str) -> AsyncIterator[dict]: ...
```

`stream` is an **async generator** yielding dicts:
- `{"kind": "candle", "candle": Candle}`
- `{"kind": "tick", "price": float, "time": int}`

## Step-by-step

### 1. Pick a transport pattern
- **Has a WebSocket?** Stream natively (like `HyperliquidSource`) with a
  reconnect loop.
- **Only REST / blocking SDK?** Poll on an interval and off-load blocking calls
  with `asyncio.to_thread(...)` (like `YFinanceSource`).

### 2. Write the class

Example: a hypothetical key-free crypto REST provider that you poll.

```python
class ExampleCryptoSource(DataSource):
    name = "example"
    asset_class = AssetClass.CRYPTO

    _SYMBOLS = {"BTCUSDT": "Bitcoin/USDT", "ETHUSDT": "Ethereum/USDT"}

    def list_symbols(self) -> list[SymbolInfo]:
        return [
            SymbolInfo(symbol=s, label=l, asset_class=self.asset_class, provider=self.name)
            for s, l in self._SYMBOLS.items()
        ]

    def supports(self, symbol: str) -> bool:
        return symbol in self._SYMBOLS

    async def get_history(self, symbol: str, interval: str) -> list[Candle]:
        interval = normalize_interval(interval)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.example.com/klines",
                params={"symbol": symbol, "interval": interval, "limit": 500},
            )
            resp.raise_for_status()
            rows = resp.json()
        candles = [
            Candle(
                time=int(r[0]) // 1000,
                open=float(r[1]), high=float(r[2]),
                low=float(r[3]), close=float(r[4]), volume=float(r[5]),
            )
            for r in rows
        ]
        return sorted(candles, key=lambda c: c.time)

    async def stream(self, symbol: str, interval: str):
        interval = normalize_interval(interval)
        while True:
            try:
                candles = await self.get_history(symbol, interval)
                if candles:
                    latest = candles[-1]
                    yield {"kind": "candle", "candle": latest}
                    yield {"kind": "tick", "price": latest.close, "time": latest.time}
            except Exception:
                pass
            await asyncio.sleep(self.settings.poll_interval_seconds)
```

### 3. Register it

In `_build_registry()`:

```python
def _build_registry(settings: Settings) -> list[DataSource]:
    return [
        HyperliquidSource(settings),
        YFinanceSource(settings),
        ExampleCryptoSource(settings),   # <-- add here
    ]
```

That's it. The new symbols appear in `/api/symbols`, `/api/history` resolves to
the new source, and `/ws/stream` streams from it.

## Adding a new asset class

If your provider isn't crypto or Indian stocks:

1. Extend the enum in `backend/app/models.py`:
   ```python
   class AssetClass(str, Enum):
       CRYPTO = "crypto"
       INDIAN_STOCK = "indian_stock"
       US_STOCK = "us_stock"   # new
   ```
2. Mirror it in `frontend/src/app/models/market.ts`:
   ```ts
   export type AssetClass = 'crypto' | 'indian_stock' | 'us_stock';
   export interface SymbolGroups {
     crypto: SymbolInfo[];
     indian_stock: SymbolInfo[];
     us_stock: SymbolInfo[];   // new
   }
   ```
3. Add an `<optgroup>` for it in `chart-pane.html`.
4. The backend's `/api/symbols` grouping (`{ac.value: [] for ac in AssetClass}`)
   picks up the new class automatically.

## Handling API keys (optional providers)

The defaults are key-free, but a paid provider can read keys from env:

1. Add the variable to `Settings` in `config.py`:
   ```python
   alpaca_key: str = field(default_factory=lambda: os.getenv("ALPACA_KEY", ""))
   ```
2. Read `self.settings.alpaca_key` inside your source.
3. Document it in `.env.example` and [06 — Configuration](06-configuration.md).
4. Guard registration so a missing key degrades gracefully:
   ```python
   sources = [HyperliquidSource(settings), YFinanceSource(settings)]
   if settings.alpaca_key:
       sources.append(AlpacaSource(settings))
   return sources
   ```

## Conventions & tips

- Return candles **oldest first** from `get_history`.
- `time` must be **UNIX seconds** (divide ms by 1000).
- Always run `normalize_interval(interval)` at the top of each method.
- Map your provider's interval/period names inside the class (see
  `YFinanceSource._INTERVAL_MAP`).
- Keep `stream` resilient: wrap upstream calls in `try/except` and back off
  before retrying so one bad frame never kills the loop.
- Use `httpx.AsyncClient` for async REST; never call blocking I/O directly on
  the event loop — wrap it in `asyncio.to_thread`.
