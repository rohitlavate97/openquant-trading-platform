"""Market Data Ingestion, OHLCV Candles, and Staleness Detection Endpoints."""

from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, status
from openquant.domain.models.auth import Permission, User
from openquant.domain.models.market_data import (
    Tick,
    Candle,
    CandleTimeframe,
    MarketDataStalenessReport,
)
from openquant.interfaces.api.dependencies import require_permissions
from openquant.application.services.market_data_service import market_data_service

router = APIRouter(prefix="/market-data", tags=["Market Data & Staleness Engine"])


@router.get("/ticks/latest", summary="Get Latest Market Ticks")
async def get_latest_ticks(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    symbol: str | None = Query(default=None, description="Specific symbol to query"),
) -> dict[str, Any]:
    """Retrieve the latest L1 tick for all or a specific instrument."""
    if symbol:
        tick = await market_data_service.get_latest_tick(symbol)
        return {"symbol": symbol.upper(), "tick": tick.model_dump() if tick else None}
    ticks = await market_data_service.get_all_latest_ticks()
    return {"ticks": {sym: t.model_dump() for sym, t in ticks.items()}}


@router.get("/candles", summary="Get Aggregated OHLCV Candles")
async def get_candles(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    symbol: str = Query(description="Instrument symbol, e.g. AAPL"),
    timeframe: CandleTimeframe = Query(default=CandleTimeframe.M1, description="Candle bar timeframe"),
    limit: int = Query(default=100, ge=1, le=500, description="Max candle count"),
) -> list[dict[str, Any]]:
    """Retrieve aggregated OHLCV candles for charting and quantitative analysis."""
    candles = await market_data_service.get_candles(symbol, timeframe, limit)
    return [c.model_dump() for c in candles]


@router.get("/staleness", summary="Get Market Data Staleness & Feed Health Report")
async def get_staleness_report(
    current_user: Annotated[User, Depends(require_permissions(Permission.READ_ONLY))],
    max_staleness_ms: int = Query(default=3000, ge=500, le=30000, description="Staleness threshold in ms"),
) -> dict[str, Any]:
    """Evaluate market data feed freshness across all symbols against the 3000ms hard stop limit."""
    report = await market_data_service.get_staleness_report(max_staleness_ms)
    return report.model_dump()


@router.post("/ticks", status_code=status.HTTP_201_CREATED, summary="Ingest Market Tick")
async def ingest_tick(
    tick: Tick,
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
) -> dict[str, Any]:
    """Ingest a market tick from an external feed or gateway bridge."""
    await market_data_service.ingest_tick(tick)
    return {"status": "success", "symbol": tick.symbol, "timestamp": tick.timestamp.isoformat()}


@router.post("/replay/start", summary="Start Synthetic Market Replay Feed")
async def start_replay(
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
    interval_sec: float = Query(default=0.5, ge=0.05, le=5.0, description="Tick emission interval in seconds"),
) -> dict[str, Any]:
    """Start synthetic market data generator simulating realistic tick streams."""
    market_data_service.start_synthetic_feed(interval_sec)
    return {"status": "started", "interval_sec": interval_sec, "is_running": True}


@router.post("/replay/stop", summary="Stop Synthetic Market Replay Feed")
async def stop_replay(
    current_user: Annotated[User, Depends(require_permissions(Permission.ORDER_MANAGE))],
) -> dict[str, Any]:
    """Stop synthetic market data generator."""
    market_data_service.stop_synthetic_feed()
    return {"status": "stopped", "is_running": False}
