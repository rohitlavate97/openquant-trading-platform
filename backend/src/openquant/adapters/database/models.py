"""SQLAlchemy 2.x Async ORM Models for OpenQuant Enterprise Platform."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from openquant.adapters.database.session import Base
from openquant.domain.models.auth import UserRole
from openquant.domain.models.order import OrderSide, OrderStatus, OrderType, TimeInForce
from openquant.domain.models.position import PositionSide
from openquant.domain.models.promotion import StrategyPromotionStage, StrategySourceType

# JSON type fallback for cross-database support (PostgreSQL JSONB / SQLite JSON)
JsonType = JSON().with_variant(JSONB, "postgresql")


class UserModel(Base):
    """User accounts table."""
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=UserRole.TRADER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    api_keys: Mapped[list["APIKeyModel"]] = relationship("APIKeyModel", back_populates="user", cascade="all, delete-orphan")
    credentials: Mapped[list["BrokerCredentialModel"]] = relationship(
        "BrokerCredentialModel", back_populates="user", cascade="all, delete-orphan"
    )


class APIKeyModel(Base):
    """Programmatic API Keys table."""
    __tablename__ = "api_keys"

    key_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JsonType, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="api_keys")


class BrokerCredentialModel(Base):
    """Encrypted Broker Credentials Vault table."""
    __tablename__ = "broker_credentials"

    credential_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    broker_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="credentials")

    __table_args__ = (
        Index("ix_broker_credentials_user_broker", "user_id", "broker_id", unique=True),
    )


class OrderModel(Base):
    """Orders table enforcing idempotency and status indexing."""
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    broker_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    broker_order_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    average_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    time_in_force: Mapped[str] = mapped_column(String(16), default="DAY", nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_orders_account_idempotency", "account_id", "idempotency_key", unique=True),
    )


class PositionModel(Base):
    """Positions table tracking real-time reconciled positions."""
    __tablename__ = "positions"

    position_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    account_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    broker_id: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(16), default="FLAT", nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("0"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_positions_account_symbol", "account_id", "symbol", unique=True),
    )


class StrategyModel(Base):
    """Strategies table tracking promotion gate state."""
    __tablename__ = "strategies"

    strategy_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(32), default=StrategyPromotionStage.DRAFT.value, nullable=False)
    is_live_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True, nullable=False)
    criteria: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    promotion_history: Mapped[list["PromotionRecordModel"]] = relationship(
        "PromotionRecordModel", back_populates="strategy", cascade="all, delete-orphan"
    )


class PromotionRecordModel(Base):
    """Immutable promotion lifecycle transition records."""
    __tablename__ = "strategy_promotion_records"

    record_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), ForeignKey("strategies.strategy_id"), index=True, nullable=False)
    from_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    strategy: Mapped["StrategyModel"] = relationship("StrategyModel", back_populates="promotion_history")


class AuditLogModel(Base):
    """Immutable Append-Only Audit Log Table for all critical system events."""
    __tablename__ = "audit_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="INFO", index=True, nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="SUCCESS", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_event_time", "event_type", "timestamp"),
        Index("ix_audit_logs_actor_time", "actor_id", "timestamp"),
    )
