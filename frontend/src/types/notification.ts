export type NotificationChannelType = "TELEGRAM" | "DISCORD" | "EMAIL" | "WEBHOOK" | "IN_APP";

export type NotificationSeverity = "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export type NotificationStatus = "PENDING" | "SENT" | "FAILED" | "DELIVERED";

export interface NotificationChannelConfig {
  channel_id: string;
  channel_type: NotificationChannelType;
  name: string;
  is_enabled: boolean;
  config: Record<string, any>;
  subscribed_severities: NotificationSeverity[];
  created_at: string;
  updated_at: string;
}

export interface NotificationMessage {
  notification_id: string;
  channel_type: NotificationChannelType;
  severity: NotificationSeverity;
  title: string;
  content: string;
  target_recipient?: string | null;
  metadata?: Record<string, any>;
  status: NotificationStatus;
  failure_reason?: string | null;
  is_read: boolean;
  created_at: string;
  sent_at?: string | null;
}

export interface InAppNotificationsResponse {
  unread_count: number;
  notifications: NotificationMessage[];
}
