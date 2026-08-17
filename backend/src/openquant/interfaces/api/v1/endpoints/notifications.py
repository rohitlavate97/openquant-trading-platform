"""REST API Endpoints for Notification System, Alert Routing, Channel Configs, and Event Bus Logs."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from openquant.domain.models.auth import Permission, User
from openquant.domain.models.notification import (
    NotificationChannelConfig,
    NotificationChannelType,
    NotificationMessage,
    NotificationSeverity,
)
from openquant.application.services.notification_service import (
    NotificationService,
    notification_service,
)
from openquant.interfaces.api.dependencies import require_permissions

router = APIRouter(prefix="/notifications", tags=["Notification System & Event Bus"])


class CreateChannelRequest(BaseModel):
    name: str
    channel_type: NotificationChannelType
    config: dict[str, Any] = Field(default_factory=dict)
    subscribed_severities: list[NotificationSeverity] = Field(
        default_factory=lambda: [
            NotificationSeverity.INFO,
            NotificationSeverity.WARNING,
            NotificationSeverity.ERROR,
            NotificationSeverity.CRITICAL,
        ]
    )


class UpdateChannelRequest(BaseModel):
    is_enabled: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    subscribed_severities: Optional[list[NotificationSeverity]] = None


class TestChannelResponse(BaseModel):
    channel_id: str
    success: bool
    message: str


class BroadcastAlertRequest(BaseModel):
    title: str
    content: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    target_channel_type: Optional[NotificationChannelType] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InAppNotificationsResponse(BaseModel):
    unread_count: int
    notifications: list[NotificationMessage]


@router.get("/channels", response_model=list[NotificationChannelConfig])
async def list_channels_endpoint(
    only_enabled: bool = Query(default=False),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: NotificationService = Depends(lambda: notification_service),
) -> list[NotificationChannelConfig]:
    """List all registered notification channels (Telegram, Discord, Email, Webhook, In-App)."""
    return await service.list_channels(only_enabled=only_enabled)


@router.post("/channels", response_model=NotificationChannelConfig, status_code=status.HTTP_201_CREATED)
async def create_channel_endpoint(
    payload: CreateChannelRequest,
    current_user: User = Depends(require_permissions(Permission.BROKER_MANAGE)),
    service: NotificationService = Depends(lambda: notification_service),
) -> NotificationChannelConfig:
    """Register and configure a new alert notification channel."""
    return await service.register_channel(
        name=payload.name,
        channel_type=payload.channel_type,
        config=payload.config,
        subscribed_severities=payload.subscribed_severities,
    )


@router.put("/channels/{channel_id}", response_model=NotificationChannelConfig)
async def update_channel_endpoint(
    channel_id: str,
    payload: UpdateChannelRequest,
    current_user: User = Depends(require_permissions(Permission.BROKER_MANAGE)),
    service: NotificationService = Depends(lambda: notification_service),
) -> NotificationChannelConfig:
    """Update channel state, credentials, or subscribed severity tiers."""
    try:
        return await service.update_channel(
            channel_id=channel_id,
            is_enabled=payload.is_enabled,
            config=payload.config,
            subscribed_severities=payload.subscribed_severities,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_endpoint(
    channel_id: str,
    current_user: User = Depends(require_permissions(Permission.BROKER_MANAGE)),
    service: NotificationService = Depends(lambda: notification_service),
) -> None:
    """Remove a configured notification channel."""
    deleted = await service.delete_channel(channel_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")


@router.post("/channels/{channel_id}/test", response_model=TestChannelResponse)
async def test_channel_endpoint(
    channel_id: str,
    current_user: User = Depends(require_permissions(Permission.BROKER_MANAGE)),
    service: NotificationService = Depends(lambda: notification_service),
) -> TestChannelResponse:
    """Send an automated test ping message to verify recipient credentials and reachability."""
    try:
        success, msg = await service.test_channel(channel_id)
        return TestChannelResponse(channel_id=channel_id, success=success, message=msg)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/broadcast", response_model=list[NotificationMessage])
async def broadcast_alert_endpoint(
    payload: BroadcastAlertRequest,
    current_user: User = Depends(require_permissions(Permission.ORDER_MANAGE)),
    service: NotificationService = Depends(lambda: notification_service),
) -> list[NotificationMessage]:
    """Broadcast an alert message to all eligible subscribed channels."""
    return await service.broadcast_alert(
        title=payload.title,
        content=payload.content,
        severity=payload.severity,
        target_channel_type=payload.target_channel_type,
        metadata=payload.metadata,
        actor_id=current_user.user_id,
    )


@router.get("/logs", response_model=list[NotificationMessage])
async def list_notification_logs_endpoint(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    channel_type: Optional[NotificationChannelType] = None,
    severity: Optional[NotificationSeverity] = None,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: NotificationService = Depends(lambda: notification_service),
) -> list[NotificationMessage]:
    """List historical alert notifications with delivery status and timestamps."""
    return await service.list_notification_logs(
        limit=limit,
        offset=offset,
        channel_type=channel_type,
        severity=severity,
    )


@router.get("/in-app", response_model=InAppNotificationsResponse)
async def get_in_app_notifications_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: NotificationService = Depends(lambda: notification_service),
) -> InAppNotificationsResponse:
    """Fetch in-app notifications stream and unread alert count."""
    notifications = await service.list_in_app_notifications(limit=limit, offset=offset)
    unread_count = await service.get_unread_in_app_count()
    return InAppNotificationsResponse(
        unread_count=unread_count,
        notifications=notifications,
    )


@router.post("/in-app/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_in_app_notification_read_endpoint(
    notification_id: str,
    current_user: User = Depends(require_permissions(Permission.READ_ONLY)),
    service: NotificationService = Depends(lambda: notification_service),
) -> dict[str, bool]:
    """Mark an in-app alert as acknowledged/read."""
    marked = await service.mark_notification_read(notification_id)
    return {"success": marked}
