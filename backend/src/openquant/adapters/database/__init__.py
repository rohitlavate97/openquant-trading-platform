"""Database persistence adapters."""

from openquant.adapters.database.session import (
    Base,
    engine,
    async_session_factory,
    get_db_session,
)
from openquant.adapters.database.models import (
    UserModel,
    APIKeyModel,
    BrokerCredentialModel,
    OrderModel,
    PositionModel,
    StrategyModel,
    PromotionRecordModel,
    AuditLogModel,
)
from openquant.adapters.database.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyAPIKeyRepository,
    SQLAlchemyCredentialVaultRepository,
    SQLAlchemyOrderRepository,
    SQLAlchemyPositionRepository,
    SQLAlchemyStrategyRepository,
    SQLAlchemyAuditLogRepository,
)

__all__ = [
    "Base",
    "engine",
    "async_session_factory",
    "get_db_session",
    "UserModel",
    "APIKeyModel",
    "BrokerCredentialModel",
    "OrderModel",
    "PositionModel",
    "StrategyModel",
    "PromotionRecordModel",
    "AuditLogModel",
    "SQLAlchemyUserRepository",
    "SQLAlchemyAPIKeyRepository",
    "SQLAlchemyCredentialVaultRepository",
    "SQLAlchemyOrderRepository",
    "SQLAlchemyPositionRepository",
    "SQLAlchemyStrategyRepository",
    "SQLAlchemyAuditLogRepository",
]
