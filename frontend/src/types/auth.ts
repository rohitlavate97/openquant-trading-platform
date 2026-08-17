export type UserRole =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "QUANT_DEVELOPER"
  | "TRADER"
  | "VIEWER";

export type Permission =
  | "SYSTEM_ADMIN"
  | "KILL_SWITCH_TRIGGER"
  | "STRATEGY_CREATE"
  | "STRATEGY_APPROVE"
  | "LIVE_TRADING_ENABLE"
  | "BROKER_MANAGE"
  | "ORDER_MANAGE"
  | "READ_ONLY";

export interface UserProfile {
  user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  permissions: Permission[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse extends AuthTokens {
  user: UserProfile;
}

export interface APIKeySummary {
  key_id: string;
  name: string;
  prefix: string;
  permissions: Permission[];
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface CreateAPIKeyResponse {
  key_id: string;
  name: string;
  prefix: string;
  raw_api_key: string;
  permissions: Permission[];
  expires_at: string | null;
}

export interface MaskedBrokerCredential {
  credential_id: string;
  broker_id: string;
  account_id: string;
  masked_fields: Record<string, string>;
  key_version: number;
  created_at: string;
  updated_at: string;
}
