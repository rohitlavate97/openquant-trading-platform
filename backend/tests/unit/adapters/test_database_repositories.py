"""Unit tests for SQLAlchemy 2.x async database repositories."""

from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from openquant.adapters.database.session import Base
from openquant.adapters.database.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyAPIKeyRepository,
    SQLAlchemyCredentialVaultRepository,
    SQLAlchemyOrderRepository,
    SQLAlchemyPositionRepository,
    SQLAlchemyStrategyRepository,
    SQLAlchemyAuditLogRepository,
)
from openquant.domain.models.auth import User, UserRole, Permission, APIKey, BrokerCredentialVaultItem
from openquant.domain.models.order import Order, OrderSide, OrderType, OrderStatus, TimeInForce
from openquant.domain.models.position import Position, PositionSide
from openquant.domain.models.promotion import StrategyEntity, StrategySourceType, StrategyPromotionStage, PromotionGateRecord


@pytest.fixture
async def db_session_factory():
    """Create in-memory SQLite async engine and initialize schema."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_user_repository(db_session_factory):
    """Verify user persistence, lookup by email/id, and update."""
    repo = SQLAlchemyUserRepository(db_session_factory)

    user = User(
        user_id="usr_db_1",
        email="trader.db@openquant.org",
        hashed_password="hashed_pw_123",
        full_name="Database Trader",
        role=UserRole.TRADER,
    )
    await repo.save(user)

    fetched = await repo.get_by_id("usr_db_1")
    assert fetched is not None
    assert fetched.email == "trader.db@openquant.org"
    assert fetched.role == UserRole.TRADER

    by_email = await repo.get_by_email("trader.db@openquant.org")
    assert by_email is not None
    assert by_email.user_id == "usr_db_1"

    # Update role
    user.role = UserRole.QUANT_DEVELOPER
    await repo.save(user)
    updated = await repo.get_by_id("usr_db_1")
    assert updated.role == UserRole.QUANT_DEVELOPER


@pytest.mark.asyncio
async def test_sqlalchemy_order_repository_idempotency_and_lookup(db_session_factory):
    """Verify order persistence, lookup by idempotency key, and status update."""
    repo = SQLAlchemyOrderRepository(db_session_factory)

    order = Order(
        order_id="ord_db_1",
        idempotency_key="idemp_db_key_999",
        strategy_id="strat_1",
        account_id="acc_main",
        broker_id="zerodha",
        symbol="RELIANCE",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("50"),
        price=Decimal("2900.00"),
        status=OrderStatus.SUBMITTED,
    )
    await repo.save(order)

    fetched = await repo.get_by_idempotency_key("idemp_db_key_999", "acc_main")
    assert fetched is not None
    assert fetched.order_id == "ord_db_1"
    assert fetched.quantity == Decimal("50")

    # Update filled status
    order.status = OrderStatus.FILLED
    order.filled_quantity = Decimal("50")
    order.average_fill_price = Decimal("2900.00")
    await repo.save(order)

    updated = await repo.get_by_id("ord_db_1")
    assert updated.status == OrderStatus.FILLED
    assert updated.is_terminal is True


@pytest.mark.asyncio
async def test_sqlalchemy_position_repository(db_session_factory):
    """Verify position save, retrieval, and PnL updates."""
    repo = SQLAlchemyPositionRepository(db_session_factory)

    pos = Position(
        position_id="pos_db_1",
        account_id="acc_main",
        strategy_id="strat_1",
        broker_id="zerodha",
        symbol="INFY",
        side=PositionSide.LONG,
        quantity=Decimal("100"),
        entry_price=Decimal("1500.00"),
        current_price=Decimal("1500.00"),
    )
    await repo.save(pos)

    fetched = await repo.get_position("acc_main", "INFY")
    assert fetched is not None
    assert fetched.quantity == Decimal("100")

    # Update market price
    pos.update_market_price(Decimal("1550.00"))
    await repo.save(pos)

    updated = await repo.get_position("acc_main", "INFY")
    assert updated.unrealized_pnl == Decimal("5000.00")


@pytest.mark.asyncio
async def test_sqlalchemy_audit_log_repository(db_session_factory):
    """Verify append-only audit logging and filtering."""
    repo = SQLAlchemyAuditLogRepository(db_session_factory)

    log_id1 = await repo.record_event(
        event_type="KILL_SWITCH_ACTIVATED",
        actor_id="usr_admin",
        entity_type="SYSTEM",
        entity_id="GLOBAL",
        action="HALT_TRADING",
        payload={"reason": "Manual operator intervention"},
        severity="CRITICAL",
    )

    log_id2 = await repo.record_event(
        event_type="ORDER_SUBMITTED",
        actor_id="strat_1",
        entity_type="ORDER",
        entity_id="ord_1",
        action="PLACE_ORDER",
        payload={"symbol": "AAPL", "quantity": 10},
        severity="INFO",
    )

    assert log_id1.startswith("aud_")
    assert log_id2.startswith("aud_")

    all_logs = await repo.list_logs(limit=10)
    assert len(all_logs) == 2

    critical_logs = await repo.list_logs(severity="CRITICAL")
    assert len(critical_logs) == 1
    assert critical_logs[0]["event_type"] == "KILL_SWITCH_ACTIVATED"


@pytest.mark.asyncio
async def test_sqlalchemy_strategy_repository_and_promotion_history(db_session_factory):
    """Verify strategy persistence and promotion audit records."""
    # First save author user for foreign key constraint
    user_repo = SQLAlchemyUserRepository(db_session_factory)
    await user_repo.save(User(
        user_id="usr_author_1",
        email="author@openquant.org",
        hashed_password="hash",
        full_name="Quant Author",
        role=UserRole.QUANT_DEVELOPER,
    ))

    strat_repo = SQLAlchemyStrategyRepository(db_session_factory)
    strategy = StrategyEntity(
        strategy_id="strat_db_1",
        name="StatArb Mean Reversion",
        source_type=StrategySourceType.PYTHON_CODE,
        author_id="usr_author_1",
        current_stage=StrategyPromotionStage.DRAFT,
    )
    await strat_repo.save(strategy)

    fetched = await strat_repo.get_by_id("strat_db_1")
    assert fetched is not None
    assert fetched.name == "StatArb Mean Reversion"
    assert fetched.current_stage == StrategyPromotionStage.DRAFT

    # Record promotion event
    record = PromotionGateRecord(
        strategy_id="strat_db_1",
        from_stage=StrategyPromotionStage.DRAFT,
        to_stage=StrategyPromotionStage.SANDBOXED_CODE_REVIEW,
        approved_by="usr_admin",
        reason="AST static analysis passed cleanly with 0 violations",
        metrics={"violations_count": 0, "is_safe": True},
    )
    await strat_repo.record_promotion_event(record)
