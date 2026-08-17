"""Central API v1 router mounting all sub-resources."""

from fastapi import APIRouter
from openquant.interfaces.api.v1.endpoints.health import router as health_router
from openquant.interfaces.api.v1.endpoints.system import router as system_router
from openquant.interfaces.api.v1.endpoints.auth import router as auth_router
from openquant.interfaces.api.v1.endpoints.api_keys import router as api_keys_router
from openquant.interfaces.api.v1.endpoints.secrets import router as secrets_router
from openquant.interfaces.api.v1.endpoints.audit_logs import router as audit_logs_router
from openquant.interfaces.api.v1.endpoints.brokers import router as brokers_router
from openquant.interfaces.api.v1.endpoints.stream import router as stream_router
from openquant.interfaces.api.v1.endpoints.market_data import router as market_data_router
from openquant.interfaces.api.v1.endpoints.orders import router as orders_router
from openquant.interfaces.api.v1.endpoints.risk import router as risk_router
from openquant.interfaces.api.v1.endpoints.sandbox import router as sandbox_router
from openquant.interfaces.api.v1.endpoints.strategies import router as strategies_router
from openquant.interfaces.api.v1.endpoints.backtest import router as backtest_router
from openquant.interfaces.api.v1.endpoints.paper_trading import router as paper_trading_router
from openquant.interfaces.api.v1.endpoints.reconciliation import router as reconciliation_router
from openquant.interfaces.api.v1.endpoints.strategy_sources import router as strategy_sources_router
from openquant.interfaces.api.v1.endpoints.ai_advisory import router as ai_advisory_router
from openquant.interfaces.api.v1.endpoints.portfolio import router as portfolio_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(api_keys_router)
api_v1_router.include_router(secrets_router)
api_v1_router.include_router(audit_logs_router)
api_v1_router.include_router(brokers_router)
api_v1_router.include_router(stream_router)
api_v1_router.include_router(market_data_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(sandbox_router)
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(backtest_router)
api_v1_router.include_router(paper_trading_router)
api_v1_router.include_router(reconciliation_router)
api_v1_router.include_router(strategy_sources_router)
api_v1_router.include_router(ai_advisory_router)
api_v1_router.include_router(portfolio_router)


