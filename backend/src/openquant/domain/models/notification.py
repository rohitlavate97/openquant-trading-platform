"""Domain models for Notification System, Event Bus, and Alert Routing."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
import uuid
from pydantic import BaseModel, Field


class NotificationChannelType(StrEnum):
    """Supported communication delivery channels."""
    TELEGRAM = "TELEGRAM"
    DISCORD = "DISCORD"
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
    IN_APP = "IN_APP"


class NotificationSeverity(StrEnum):
    """Alert criticality classification."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationStatus(StrEnum):
    """Delivery status of a notification dispatch."""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"


class NotificationChannelConfig(BaseModel):
    """Configuration and credentials for an alert channel."""
    channel_id: str = Field(default_factory=lambda: f"chn_{uuid.uuid4().hex[:8]}")
    channel_type: NotificationChannelType
    name: str
    is_enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    subscribed_severities: list[NotificationSeverity] = Field(
        default_factory=lambda: [
            NotificationSeverity.INFO,
            NotificationSeverity.WARNING,
            NotificationSeverity.ERROR,
            NotificationSeverity.CRITICAL,
        ]
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationMessage(BaseModel):
    """Entity representing a dispatched alert message."""
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:10]}")
    channel_type: NotificationChannelType
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str
    content: str
    target_recipient: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    failure_reason: str | None = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = None


class PlatformEvent(BaseModel):
    """Domain event published across the platform event bus."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:10]}")
    event_type: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)
