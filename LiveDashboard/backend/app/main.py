"""FastAPI application entry point.

Exposes:

* ``GET  /api/health``                       -- liveness probe.
* ``GET  /api/symbols``                       -- instruments grouped by asset class.
* ``GET  /api/history?symbol=&interval=``     -- historical OHLCV candles.
* ``WS   /ws/stream``                         -- live price/candle bridge.

When a compiled Angular build is present it is also served as static files,
allowing the whole stack to run as a single unified web service in free cloud
tiers that only permit one web instance.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import suppress

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .data_source import all_symbols, normalize_interval, resolve_source
from .models import (
    AssetClass,
    CandleMessage,
    ErrorMessage,
    HistoryResponse,
    SubscribeRequest,
    SymbolInfo,
    TickMessage,
)

settings = get_settings()

app = FastAPI(
    title="Live Trading Dashboard API",
    description="Key-free live market data bridge for crypto and Indian equities.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, str]:
    """Simple health check used by cloud platforms and the frontend."""
    return {"status": "ok"}


@app.get("/api/symbols", tags=["market-data"])
async def symbols() -> dict[str, list[SymbolInfo]]:
    """Return all tradable symbols grouped by asset class for the UI selector."""
    grouped: dict[str, list[SymbolInfo]] = {ac.value: [] for ac in AssetClass}
    for info in all_symbols():
        grouped[info.asset_class.value].append(info)
    return grouped


@app.get("/api/history", response_model=HistoryResponse, tags=["market-data"])
async def history(
    symbol: str = Query(..., description="Provider symbol, e.g. 'BTC' or 'RELIANCE.NS'"),
    interval: str = Query("1m", description="One of 1m, 5m, 15m, 1h, 1d"),
) -> HistoryResponse:
    """Return historical candles for a symbol/interval pair."""
    interval = normalize_interval(interval)
    try:
        source = resolve_source(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        candles = await source.get_history(symbol, interval)
    except Exception as exc:  # noqa: BLE001 - surface provider errors as 502
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}") from exc

    return HistoryResponse(symbol=symbol, interval=interval, candles=candles)


# ---------------------------------------------------------------------------
# WebSocket bridge
# ---------------------------------------------------------------------------


@app.websocket("/ws/stream")
async def stream(websocket: WebSocket) -> None:
    """Bridge a single chart pane to its upstream data source.

    Protocol:
        1. Client connects and sends a :class:`SubscribeRequest` JSON message.
        2. Server streams :class:`CandleMessage` and :class:`TickMessage`
           updates until the client disconnects.
    """
    await websocket.accept()
    pump_task: asyncio.Task | None = None
    try:
        raw = await websocket.receive_json()
        request = SubscribeRequest.model_validate(raw)
        interval = normalize_interval(request.interval)

        try:
            source = resolve_source(request.symbol)
        except ValueError as exc:
            await websocket.send_json(ErrorMessage(detail=str(exc)).model_dump())
            await websocket.close()
            return

        pump_task = asyncio.create_task(
            _pump(websocket, source, request.symbol, interval)
        )

        # Keep the connection alive until the client disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        with suppress(Exception):
            await websocket.send_json(ErrorMessage(detail=str(exc)).model_dump())
    finally:
        if pump_task is not None:
            pump_task.cancel()
            with suppress(asyncio.CancelledError):
                await pump_task


async def _pump(websocket: WebSocket, source, symbol: str, interval: str) -> None:
    """Forward upstream updates from a data source to the connected client."""
    async for update in source.stream(symbol, interval):
        if update["kind"] == "candle":
            message = CandleMessage(
                symbol=symbol, interval=interval, candle=update["candle"]
            )
        else:  # tick
            message = TickMessage(
                symbol=symbol, price=update["price"], time=update["time"]
            )
        await websocket.send_json(message.model_dump())


# ---------------------------------------------------------------------------
# Optional static frontend (single unified service)
# ---------------------------------------------------------------------------

_dist = settings.frontend_dist
if _dist and os.path.isdir(_dist):
    # Mounted last so the API routes above always take precedence.
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")


def run() -> None:
    """Console entry point used by ``python -m app.main``."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=bool(int(os.getenv("RELOAD", "0"))),
    )


if __name__ == "__main__":
    run()
