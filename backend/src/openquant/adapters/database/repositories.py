"""SQLAlchemy 2.x Async Repositories implementing Domain Ports."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from openquant.domain.models.auth import User, UserRole, Permission, APIKey, BrokerCredentialVaultItem
from openquant.domain.models.order import Order, OrderSide, OrderType, OrderStatus, TimeInForce
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.models.promotion import (
    StrategyEntity,
    StrategyPromotionStage,
    StrategySourceType,
    PromotionCriteria,
    PromotionGateRecord,
)
from openquant.domain.ports.user_repository import (
    IUserRepository,
    IAPIKeyRepository,
    ICredentialVaultRepository,
)
from openquant.domain.ports.repositories import (
    IOrderRepository,
    IPositionRepository,
    IStrategyRepository,
    IAuditLogRepository,
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


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy async implementation of IUserRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_id(self, user_id: str) -> User | None:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return User(
                user_id=model.user_id,
                email=model.email,
                hashed_password=model.hashed_password,
                full_name=model.full_name,
                role=UserRole(model.role),
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

    async def get_by_email(self, email: str) -> User | None:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.email == email.lower())
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return User(
                user_id=model.user_id,
                email=model.email,
                hashed_password=model.hashed_password,
                full_name=model.full_name,
                role=UserRole(model.role),
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )

    async def save(self, user: User) -> None:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.user_id == user.user_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if model:
                model.email = str(user.email).lower()
                model.hashed_password = user.hashed_password
                model.full_name = user.full_name
                model.role = user.role.value
                model.is_active = user.is_active
                model.updated_at = datetime.now(timezone.utc)
            else:
                model = UserModel(
                    user_id=user.user_id,
                    email=str(user.email).lower(),
                    hashed_password=user.hashed_password,
                    full_name=user.full_name,
                    role=user.role.value,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                )
                session.add(model)
            await session.commit()

    async def list_users(self) -> list[User]:
        async with self._session_factory() as session:
            stmt = select(UserModel)
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                User(
                    user_id=m.user_id,
                    email=m.email,
                    hashed_password=m.hashed_password,
                    full_name=m.full_name,
                    role=UserRole(m.role),
                    is_active=m.is_active,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in models
            ]


class SQLAlchemyAPIKeyRepository(IAPIKeyRepository):
    """SQLAlchemy async implementation of IAPIKeyRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_id(self, key_id: str) -> APIKey | None:
        async with self._session_factory() as session:
            stmt = select(APIKeyModel).where(APIKeyModel.key_id == key_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return APIKey(
                key_id=m.key_id,
                user_id=m.user_id,
                name=m.name,
                prefix=m.prefix,
                hashed_key=m.hashed_key,
                permissions={Permission(p) for p in m.permissions},
                is_active=m.is_active,
                expires_at=m.expires_at,
                last_used_at=m.last_used_at,
                created_at=m.created_at,
            )

    async def get_by_hashed_key(self, hashed_key: str) -> APIKey | None:
        async with self._session_factory() as session:
            stmt = select(APIKeyModel).where(APIKeyModel.hashed_key == hashed_key)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return APIKey(
                key_id=m.key_id,
                user_id=m.user_id,
                name=m.name,
                prefix=m.prefix,
                hashed_key=m.hashed_key,
                permissions={Permission(p) for p in m.permissions},
                is_active=m.is_active,
                expires_at=m.expires_at,
                last_used_at=m.last_used_at,
                created_at=m.created_at,
            )

    async def save(self, api_key: APIKey) -> None:
        async with self._session_factory() as session:
            stmt = select(APIKeyModel).where(APIKeyModel.key_id == api_key.key_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            perms = [p.value for p in api_key.permissions]
            if m:
                m.name = api_key.name
                m.permissions = perms
                m.is_active = api_key.is_active
                m.expires_at = api_key.expires_at
                m.last_used_at = api_key.last_used_at
            else:
                m = APIKeyModel(
                    key_id=api_key.key_id,
                    user_id=api_key.user_id,
                    name=api_key.name,
                    prefix=api_key.prefix,
                    hashed_key=api_key.hashed_key,
                    permissions=perms,
                    is_active=api_key.is_active,
                    expires_at=api_key.expires_at,
                    last_used_at=api_key.last_used_at,
                    created_at=api_key.created_at,
                )
                session.add(m)
            await session.commit()

    async def list_by_user(self, user_id: str) -> list[APIKey]:
        async with self._session_factory() as session:
            stmt = select(APIKeyModel).where(APIKeyModel.user_id == user_id, APIKeyModel.is_active == True)
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                APIKey(
                    key_id=m.key_id,
                    user_id=m.user_id,
                    name=m.name,
                    prefix=m.prefix,
                    hashed_key=m.hashed_key,
                    permissions={Permission(p) for p in m.permissions},
                    is_active=m.is_active,
                    expires_at=m.expires_at,
                    last_used_at=m.last_used_at,
                    created_at=m.created_at,
                )
                for m in models
            ]

    async def revoke(self, key_id: str) -> bool:
        async with self._session_factory() as session:
            stmt = update(APIKeyModel).where(APIKeyModel.key_id == key_id).values(is_active=False)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0


class SQLAlchemyCredentialVaultRepository(ICredentialVaultRepository):
    """SQLAlchemy async implementation of ICredentialVaultRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_credential(self, user_id: str, broker_id: str) -> BrokerCredentialVaultItem | None:
        async with self._session_factory() as session:
            stmt = select(BrokerCredentialModel).where(
                BrokerCredentialModel.user_id == user_id,
                BrokerCredentialModel.broker_id == broker_id,
            )
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return BrokerCredentialVaultItem(
                credential_id=m.credential_id,
                user_id=m.user_id,
                broker_id=m.broker_id,
                account_id=m.account_id,
                encrypted_payload=m.encrypted_payload,
                key_version=m.key_version,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )

    async def save_credential(self, item: BrokerCredentialVaultItem) -> None:
        async with self._session_factory() as session:
            stmt = select(BrokerCredentialModel).where(
                BrokerCredentialModel.user_id == item.user_id,
                BrokerCredentialModel.broker_id == item.broker_id,
            )
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.account_id = item.account_id
                m.encrypted_payload = item.encrypted_payload
                m.key_version = item.key_version
                m.updated_at = datetime.now(timezone.utc)
            else:
                m = BrokerCredentialModel(
                    credential_id=item.credential_id,
                    user_id=item.user_id,
                    broker_id=item.broker_id,
                    account_id=item.account_id,
                    encrypted_payload=item.encrypted_payload,
                    key_version=item.key_version,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
                session.add(m)
            await session.commit()

    async def delete_credential(self, user_id: str, broker_id: str) -> bool:
        async with self._session_factory() as session:
            stmt = delete(BrokerCredentialModel).where(
                BrokerCredentialModel.user_id == user_id,
                BrokerCredentialModel.broker_id == broker_id,
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    async def list_user_credentials(self, user_id: str) -> list[BrokerCredentialVaultItem]:
        async with self._session_factory() as session:
            stmt = select(BrokerCredentialModel).where(BrokerCredentialModel.user_id == user_id)
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                BrokerCredentialVaultItem(
                    credential_id=m.credential_id,
                    user_id=m.user_id,
                    broker_id=m.broker_id,
                    account_id=m.account_id,
                    encrypted_payload=m.encrypted_payload,
                    key_version=m.key_version,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                )
                for m in models
            ]


class SQLAlchemyOrderRepository(IOrderRepository):
    """SQLAlchemy async implementation of IOrderRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_id(self, order_id: str) -> Order | None:
        async with self._session_factory() as session:
            stmt = select(OrderModel).where(OrderModel.order_id == order_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return Order(
                order_id=m.order_id,
                idempotency_key=m.idempotency_key,
                strategy_id=m.strategy_id,
                account_id=m.account_id,
                broker_id=m.broker_id,
                broker_order_id=m.broker_order_id,
                symbol=m.symbol,
                side=OrderSide(m.side),
                order_type=OrderType(m.order_type),
                status=OrderStatus(m.status),
                quantity=m.quantity,
                filled_quantity=m.filled_quantity,
                price=m.price,
                stop_price=m.stop_price,
                average_fill_price=m.average_fill_price,
                time_in_force=TimeInForce(m.time_in_force),
                rejection_reason=m.rejection_reason,
                created_at=m.created_at,
                updated_at=m.updated_at,
                tag=m.tag,
            )

    async def get_by_idempotency_key(self, idempotency_key: str, account_id: str) -> Order | None:
        async with self._session_factory() as session:
            stmt = select(OrderModel).where(
                OrderModel.idempotency_key == idempotency_key,
                OrderModel.account_id == account_id,
            )
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return Order(
                order_id=m.order_id,
                idempotency_key=m.idempotency_key,
                strategy_id=m.strategy_id,
                account_id=m.account_id,
                broker_id=m.broker_id,
                broker_order_id=m.broker_order_id,
                symbol=m.symbol,
                side=OrderSide(m.side),
                order_type=OrderType(m.order_type),
                status=OrderStatus(m.status),
                quantity=m.quantity,
                filled_quantity=m.filled_quantity,
                price=m.price,
                stop_price=m.stop_price,
                average_fill_price=m.average_fill_price,
                time_in_force=TimeInForce(m.time_in_force),
                rejection_reason=m.rejection_reason,
                created_at=m.created_at,
                updated_at=m.updated_at,
                tag=m.tag,
            )

    async def save(self, order: Order) -> None:
        async with self._session_factory() as session:
            stmt = select(OrderModel).where(OrderModel.order_id == order.order_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.status = order.status.value
                m.broker_order_id = order.broker_order_id
                m.filled_quantity = order.filled_quantity
                m.average_fill_price = order.average_fill_price
                m.rejection_reason = order.rejection_reason
                m.updated_at = datetime.now(timezone.utc)
            else:
                m = OrderModel(
                    order_id=order.order_id,
                    idempotency_key=order.idempotency_key,
                    strategy_id=order.strategy_id,
                    account_id=order.account_id,
                    broker_id=order.broker_id,
                    broker_order_id=order.broker_order_id,
                    symbol=order.symbol,
                    side=order.side.value,
                    order_type=order.order_type.value,
                    status=order.status.value,
                    quantity=order.quantity,
                    filled_quantity=order.filled_quantity,
                    price=order.price,
                    stop_price=order.stop_price,
                    average_fill_price=order.average_fill_price,
                    time_in_force=order.time_in_force.value,
                    rejection_reason=order.rejection_reason,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    tag=order.tag,
                )
                session.add(m)
            await session.commit()

    async def list_open_orders(self, account_id: str) -> list[Order]:
        async with self._session_factory() as session:
            terminal_statuses = [
                OrderStatus.FILLED.value,
                OrderStatus.CANCELLED.value,
                OrderStatus.REJECTED.value,
                OrderStatus.RISK_REJECTED.value,
                OrderStatus.EXPIRED.value,
            ]
            stmt = select(OrderModel).where(
                OrderModel.account_id == account_id,
                ~OrderModel.status.in_(terminal_statuses),
            )
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                Order(
                    order_id=m.order_id,
                    idempotency_key=m.idempotency_key,
                    strategy_id=m.strategy_id,
                    account_id=m.account_id,
                    broker_id=m.broker_id,
                    broker_order_id=m.broker_order_id,
                    symbol=m.symbol,
                    side=OrderSide(m.side),
                    order_type=OrderType(m.order_type),
                    status=OrderStatus(m.status),
                    quantity=m.quantity,
                    filled_quantity=m.filled_quantity,
                    price=m.price,
                    stop_price=m.stop_price,
                    average_fill_price=m.average_fill_price,
                    time_in_force=TimeInForce(m.time_in_force),
                    rejection_reason=m.rejection_reason,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                    tag=m.tag,
                )
                for m in models
            ]


class SQLAlchemyPositionRepository(IPositionRepository):
    """SQLAlchemy async implementation of IPositionRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_position(self, account_id: str, symbol: str) -> Position | None:
        async with self._session_factory() as session:
            stmt = select(PositionModel).where(
                PositionModel.account_id == account_id,
                PositionModel.symbol == symbol,
            )
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return Position(
                position_id=m.position_id,
                account_id=m.account_id,
                strategy_id=m.strategy_id,
                broker_id=m.broker_id,
                symbol=m.symbol,
                side=PositionSide(m.side),
                quantity=m.quantity,
                entry_price=m.entry_price,
                current_price=m.current_price,
                unrealized_pnl=m.unrealized_pnl,
                realized_pnl=m.realized_pnl,
                updated_at=m.updated_at,
            )

    async def list_positions(self, account_id: str) -> list[Position]:
        async with self._session_factory() as session:
            stmt = select(PositionModel).where(PositionModel.account_id == account_id)
            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                Position(
                    position_id=m.position_id,
                    account_id=m.account_id,
                    strategy_id=m.strategy_id,
                    broker_id=m.broker_id,
                    symbol=m.symbol,
                    side=PositionSide(m.side),
                    quantity=m.quantity,
                    entry_price=m.entry_price,
                    current_price=m.current_price,
                    unrealized_pnl=m.unrealized_pnl,
                    realized_pnl=m.realized_pnl,
                    updated_at=m.updated_at,
                )
                for m in models
            ]

    async def save(self, position: Position) -> None:
        async with self._session_factory() as session:
            stmt = select(PositionModel).where(
                PositionModel.account_id == position.account_id,
                PositionModel.symbol == position.symbol,
            )
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.side = position.side.value
                m.quantity = position.quantity
                m.entry_price = position.entry_price
                m.current_price = position.current_price
                m.unrealized_pnl = position.unrealized_pnl
                m.realized_pnl = position.realized_pnl
                m.updated_at = datetime.now(timezone.utc)
            else:
                m = PositionModel(
                    position_id=position.position_id,
                    account_id=position.account_id,
                    strategy_id=position.strategy_id,
                    broker_id=position.broker_id,
                    symbol=position.symbol,
                    side=position.side.value,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    current_price=position.current_price,
                    unrealized_pnl=position.unrealized_pnl,
                    realized_pnl=position.realized_pnl,
                    updated_at=position.updated_at,
                )
                session.add(m)
            await session.commit()


class SQLAlchemyStrategyRepository(IStrategyRepository):
    """SQLAlchemy async implementation of IStrategyRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_by_id(self, strategy_id: str) -> StrategyEntity | None:
        async with self._session_factory() as session:
            stmt = select(StrategyModel).where(StrategyModel.strategy_id == strategy_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return StrategyEntity(
                strategy_id=m.strategy_id,
                name=m.name,
                source_type=StrategySourceType(m.source_type),
                current_stage=StrategyPromotionStage(m.current_stage),
                is_live_enabled=m.is_live_enabled,
                author_id=m.author_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
                criteria=PromotionCriteria(**m.criteria) if m.criteria else PromotionCriteria(),
            )

    async def save(self, strategy: StrategyEntity) -> None:
        async with self._session_factory() as session:
            stmt = select(StrategyModel).where(StrategyModel.strategy_id == strategy.strategy_id)
            res = await session.execute(stmt)
            m = res.scalar_one_or_none()
            criteria_dict = {k: str(v) if isinstance(v, Decimal) else v for k, v in strategy.criteria.model_dump().items()}
            if m:
                m.name = strategy.name
                m.current_stage = strategy.current_stage.value
                m.is_live_enabled = strategy.is_live_enabled
                m.criteria = criteria_dict
                m.updated_at = datetime.now(timezone.utc)
            else:
                m = StrategyModel(
                    strategy_id=strategy.strategy_id,
                    name=strategy.name,
                    source_type=strategy.source_type.value,
                    current_stage=strategy.current_stage.value,
                    is_live_enabled=strategy.is_live_enabled,
                    author_id=strategy.author_id,
                    criteria=criteria_dict,
                    created_at=strategy.created_at,
                    updated_at=strategy.updated_at,
                )
                session.add(m)
            await session.commit()

    async def record_promotion_event(self, record: PromotionGateRecord) -> None:
        async with self._session_factory() as session:
            m = PromotionRecordModel(
                record_id=f"rec_{uuid.uuid4().hex[:12]}",
                strategy_id=record.strategy_id,
                from_stage=record.from_stage.value,
                to_stage=record.to_stage.value,
                approved_by=record.approved_by,
                reason=record.reason,
                metrics=record.metrics,
                timestamp=record.timestamp,
            )
            session.add(m)
            await session.commit()


class SQLAlchemyAuditLogRepository(IAuditLogRepository):
    """SQLAlchemy async append-only implementation of IAuditLogRepository."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def record_event(
        self,
        event_type: str,
        actor_id: str,
        entity_id: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        entity_type: str = "SYSTEM",
        action: str = "EXECUTE",
        client_ip: str | None = None,
        status: str = "SUCCESS",
        reason: str | None = None,
    ) -> str:
        """Append an immutable audit entry to the database."""
        log_id = f"aud_{uuid.uuid4().hex[:14]}"
        async with self._session_factory() as session:
            m = AuditLogModel(
                log_id=log_id,
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                severity=severity,
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload=payload,
                client_ip=client_ip,
                status=status,
                reason=reason,
            )
            session.add(m)
            await session.commit()
            return log_id

    async def list_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: str | None = None,
        actor_id: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query audit log entries with flexible filtering."""
        async with self._session_factory() as session:
            stmt = select(AuditLogModel).order_by(AuditLogModel.timestamp.desc())
            if event_type:
                stmt = stmt.where(AuditLogModel.event_type == event_type)
            if actor_id:
                stmt = stmt.where(AuditLogModel.actor_id == actor_id)
            if severity:
                stmt = stmt.where(AuditLogModel.severity == severity)
            stmt = stmt.limit(limit).offset(offset)

            res = await session.execute(stmt)
            models = res.scalars().all()
            return [
                {
                    "log_id": m.log_id,
                    "timestamp": m.timestamp.isoformat(),
                    "event_type": m.event_type,
                    "severity": m.severity,
                    "actor_id": m.actor_id,
                    "entity_type": m.entity_type,
                    "entity_id": m.entity_id,
                    "action": m.action,
                    "payload": m.payload,
                    "client_ip": m.client_ip,
                    "status": m.status,
                    "reason": m.reason,
                }
                for m in models
            ]
