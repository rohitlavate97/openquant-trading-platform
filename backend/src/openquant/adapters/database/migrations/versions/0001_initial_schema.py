"""Initial database schema with users, api keys, broker credentials, orders, positions, strategies, and audit logs.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-17 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), default="TRADER", nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_user_id", "users", ["user_id"])

    # 2. API Keys Table
    op.create_table(
        "api_keys",
        sa.Column("key_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("hashed_key", sa.String(128), unique=True, nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_hashed_key", "api_keys", ["hashed_key"])

    # 3. Broker Credentials Vault Table
    op.create_table(
        "broker_credentials",
        sa.Column("credential_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_id", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(128), nullable=False),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("key_version", sa.Integer(), default=1, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_broker_credentials_user_broker", "broker_credentials", ["user_id", "broker_id"], unique=True)

    # 4. Orders Table
    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(64), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("strategy_id", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(128), nullable=False),
        sa.Column("broker_id", sa.String(64), nullable=False),
        sa.Column("broker_order_id", sa.String(128), nullable=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(16), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 8), nullable=False),
        sa.Column("filled_quantity", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("price", sa.Numeric(18, 8), nullable=True),
        sa.Column("stop_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("average_fill_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("time_in_force", sa.String(16), default="DAY", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("tag", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_account_idempotency", "orders", ["account_id", "idempotency_key"], unique=True)
    op.create_index("ix_orders_strategy_id", "orders", ["strategy_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    # 5. Positions Table
    op.create_table(
        "positions",
        sa.Column("position_id", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.String(128), nullable=False),
        sa.Column("strategy_id", sa.String(64), nullable=False),
        sa.Column("broker_id", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(16), default="FLAT", nullable=False),
        sa.Column("quantity", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("entry_price", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("current_price", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("realized_pnl", sa.Numeric(18, 8), default=0, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_positions_account_symbol", "positions", ["account_id", "symbol"], unique=True)

    # 6. Strategies Table
    op.create_table(
        "strategies",
        sa.Column("strategy_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("current_stage", sa.String(32), default="DRAFT", nullable=False),
        sa.Column("is_live_enabled", sa.Boolean(), default=False, nullable=False),
        sa.Column("author_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Strategy Promotion History Table
    op.create_table(
        "strategy_promotion_records",
        sa.Column("record_id", sa.String(64), primary_key=True),
        sa.Column("strategy_id", sa.String(64), sa.ForeignKey("strategies.strategy_id"), nullable=False),
        sa.Column("from_stage", sa.String(32), nullable=False),
        sa.Column("to_stage", sa.String(32), nullable=False),
        sa.Column("approved_by", sa.String(64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_promo_strat_time", "strategy_promotion_records", ["strategy_id", "timestamp"])

    # 8. Immutable Audit Logs Table
    op.create_table(
        "audit_logs",
        sa.Column("log_id", sa.String(64), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), default="INFO", nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("client_ip", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), default="SUCCESS", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_logs_event_time", "audit_logs", ["event_type", "timestamp"])
    op.create_index("ix_audit_logs_actor_time", "audit_logs", ["actor_id", "timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("strategy_promotion_records")
    op.drop_table("strategies")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("broker_credentials")
    op.drop_table("api_keys")
    op.drop_table("users")
