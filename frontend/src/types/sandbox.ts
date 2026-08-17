export interface SandboxSecurityCheckResult {
  is_safe: boolean;
  violations: string[];
  detected_imports: string[];
  dangerous_nodes: string[];
}

export interface SandboxExecutionResult {
  success: boolean;
  execution_time_seconds: number;
  memory_used_mb: number;
  cpu_time_seconds: number;
  output: any;
  error_message?: string | null;
  resource_limit_exceeded: boolean;
}

export interface StrategyTemplate {
  name: string;
  description: string;
  code: string;
}
