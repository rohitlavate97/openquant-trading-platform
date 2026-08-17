# Milestone 17: Notification System & Event Bus

## Overview
Milestone 17 delivers an enterprise-grade multi-channel notification dispatcher and event-driven pub-sub event bus architecture for OpenQuant. It allows quant traders, algorithmic operators, and risk managers to receive instantaneous alerts on critical trade lifecycles, global kill switch engagements, pre-trade risk halts, reconciliation mismatches, and market feed staleness across Telegram, Discord, Email, Webhooks, and an In-App notification queue.

## Key Deliverables & Architecture

### 1. Domain Models (`src/openquant/domain/models/notification.py`)
- **`NotificationChannelType`**: `TELEGRAM`, `DISCORD`, `EMAIL`, `WEBHOOK`, `IN_APP`.
- **`NotificationSeverity`**: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- **`NotificationStatus`**: `PENDING`, `SENT`, `FAILED`, `DELIVERED`.
- **`NotificationChannelConfig`**: Channel identifier, type, credentials/webhook URLs, enabled state, and subscribed severity levels.
- **`NotificationMessage`**: Entity capturing alert title, formatted content, channel type, delivery state, timestamps, and in-app read receipt.
- **`PlatformEvent`**: Typed domain event schema with event type, severity, source, and payload.

### 2. Domain Ports (`src/openquant/domain/ports/event_bus.py`, `src/openquant/domain/ports/notification_port.py`)
- **`IEventBus`**: Abstract pub-sub bus with topic-level and wildcard subscription handlers.
- **`INotificationDispatcher`**: Multi-channel delivery port with credential connectivity testing (`test_channel`).
- **`INotificationChannelRepository`**: Storage contract for channel configurations.
- **`INotificationLogRepository`**: Storage contract for historical alert logs and unread in-app counters.

### 3. Adapters (`src/openquant/adapters/`)
- **`InMemoryEventBus`**: Asynchronous pub-sub engine handling exact topic (`risk.kill_switch`, `risk.breach`, `reconciliation.mismatch`, `market_data.stale`) and wildcard subscriptions.
- **`NotificationDispatcher`**:
  - **Telegram**: Markdown-formatted bot API dispatcher (`sendMessage`).
  - **Discord**: Rich embed builder with color-coded severity mapping (`0xE11D48` CRITICAL, `0xF43F5E` ERROR, `0xF59E0B` WARNING, `0x3B82F6` INFO).
  - **Email**: SMTP/SES templated delivery.
  - **Webhook**: Signed HTTP JSON POST delivery with timeout resilience.
  - **In-App**: Immediate delivery to notification store.
- **`InMemoryNotificationChannelRepository` & `InMemoryNotificationLogRepository`**: Thread-safe memory stores with default system in-app channel seeding.

### 4. Application & REST APIs (`src/openquant/application/services/notification_service.py`, `src/openquant/interfaces/api/v1/endpoints/notifications.py`)
- **`NotificationService`**: Orchestrates channel CRUD, automated event-bus triggers, broadcast alerts, and in-app read status.
- **REST Endpoints**:
  - `GET /api/v1/notifications/channels`: List configured channels.
  - `POST /api/v1/notifications/channels`: Register new channel.
  - `PUT /api/v1/notifications/channels/{channel_id}`: Update channel config/severities.
  - `DELETE /api/v1/notifications/channels/{channel_id}`: Delete channel.
  - `POST /api/v1/notifications/channels/{channel_id}/test`: 1-Click connectivity ping.
  - `POST /api/v1/notifications/broadcast`: Manual multi-channel broadcast.
  - `GET /api/v1/notifications/logs`: Historical dispatched alerts with status.
  - `GET /api/v1/notifications/in-app`: In-app notification queue and unread counter.
  - `POST /api/v1/notifications/in-app/{notification_id}/read`: Mark alert as read.

### 5. Frontend Notification Center UI (`frontend/src/features/notifications/NotificationCenterPage.tsx`)
- **Top Metrics**: Active Alert Channels, Total Dispatched (24h), Unread In-App Alerts, Event Bus Subscriptions.
- **Channel Matrix Table**: Registered endpoints, severity subscription badges, 1-click Test Ping button, and deletion.
- **Add Channel Drawer/Modal**: Configuration for Discord, Telegram, Email, and Webhook.
- **Manual Broadcast Dispatcher**: High-priority operations alert transmitter.
- **Live Dispatched Alert Feed**: Delivery audit trail and in-app acknowledgement.

## Test Verification
- **Backend**: 135 Unit and Integration tests passing (85% coverage).
- **Frontend**: 37 Vitest tests passing across 17 test files, 0 TypeScript errors, clean production bundle.
