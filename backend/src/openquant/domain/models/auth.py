"""Domain models for multi-tenant Authentication, Role-Based Access Control, and Secrets Vault."""

from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, EmailStr, Field


class UserRole(StrEnum):
    """Hierarchical user roles within the platform."""
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    QUANT_DEVELOPER = "QUANT_DEVELOPER"
    TRADER = "TRADER"
    VIEWER = "VIEWER"


class Permission(StrEnum):
    """Granular capabilities enforced across domain services and API endpoints."""
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    KILL_SWITCH_TRIGGER = "KILL_SWITCH_TRIGGER"
    STRATEGY_CREATE = "STRATEGY_CREATE"
    STRATEGY_APPROVE = "STRATEGY_APPROVE"
    LIVE_TRADING_ENABLE = "LIVE_TRADING_ENABLE"
    BROKER_MANAGE = "BROKER_MANAGE"
    ORDER_MANAGE = "ORDER_MANAGE"
    READ_ONLY = "READ_ONLY"


# Strict Role-to-Permissions Capability Mapping
ROLE_PERMISSIONS_MAP: dict[UserRole, set[Permission]] = {
    UserRole.SUPER_ADMIN: {
        Permission.SYSTEM_ADMIN,
        Permission.KILL_SWITCH_TRIGGER,
        Permission.STRATEGY_CREATE,
        Permission.STRATEGY_APPROVE,
        Permission.LIVE_TRADING_ENABLE,
        Permission.BROKER_MANAGE,
        Permission.ORDER_MANAGE,
        Permission.READ_ONLY,
    },
    UserRole.ADMIN: {
        Permission.KILL_SWITCH_TRIGGER,
        Permission.STRATEGY_CREATE,
        Permission.STRATEGY_APPROVE,
        Permission.LIVE_TRADING_ENABLE,
        Permission.BROKER_MANAGE,
        Permission.ORDER_MANAGE,
        Permission.READ_ONLY,
    },
    UserRole.QUANT_DEVELOPER: {
        Permission.STRATEGY_CREATE,
        Permission.KILL_SWITCH_TRIGGER,
        Permission.ORDER_MANAGE,
        Permission.READ_ONLY,
    },
    UserRole.TRADER: {
        Permission.KILL_SWITCH_TRIGGER,
        Permission.ORDER_MANAGE,
        Permission.READ_ONLY,
    },
    UserRole.VIEWER: {
        Permission.READ_ONLY,
    },
}


class User(BaseModel):
    """Domain Entity representing an authenticated platform user."""
    user_id: str
    email: EmailStr
    hashed_password: str
    full_name: str
    role: UserRole = UserRole.TRADER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def permissions(self) -> set[Permission]:
        """Resolve all granular permissions associated with the user's role."""
        return ROLE_PERMISSIONS_MAP.get(self.role, {Permission.READ_ONLY})

    def has_permission(self, permission: Permission) -> bool:
        """Check if user holds a specific permission."""
        return permission in self.permissions


class APIKey(BaseModel):
    """Domain Entity representing a programmatic API key."""
    key_id: str
    user_id: str
    name: str
    prefix: str = Field(..., description="First 8 characters of key for display (e.g. oq_live_1234)")
    hashed_key: str = Field(..., description="Cryptographic SHA-256 hash of the full secret key")
    permissions: set[Permission] = Field(default_factory=set)
    is_active: bool = True
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        """Check if API key is active and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class BrokerCredentialVaultItem(BaseModel):
    """Domain Entity representing encrypted broker secrets stored at rest."""
    credential_id: str
    user_id: str
    broker_id: str
    account_id: str
    encrypted_payload: str = Field(..., description="Authenticated ciphertext containing credentials")
    key_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
