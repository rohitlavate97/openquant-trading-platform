import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DashboardPage } from './DashboardPage';
import { SystemInfo } from '@/types';

const mockSystemInfo: SystemInfo = {
  platform: 'OpenQuant Algorithmic Trading Platform',
  version: '0.1.0',
  environment: 'development',
  debug: true,
  risk_engine: {
    kill_switch_active: false,
    max_daily_loss_percent: 3.0,
    max_drawdown_percent: 5.0,
    max_position_size_percent: 10.0,
    max_orders_per_second: 10,
  },
  sandbox: {
    max_cpu_seconds: 30,
    max_memory_mb: 512,
    execution_timeout_seconds: 60,
    strict_allowlist_mode: true,
  },
  adapters: [],
};

describe('DashboardPage', () => {
  it('renders risk engine and sandbox metrics', () => {
    render(
      <DashboardPage
        systemInfo={mockSystemInfo}
        killSwitchActive={false}
      />
    );

    expect(screen.getByText('Pre-Trade Risk Engine')).toBeDefined();
    expect(screen.getByText('Strategy Sandbox')).toBeDefined();
    expect(screen.getByText(/Strategy Promotion Gate/i)).toBeDefined();
  });

  it('renders emergency alert banner when Kill Switch is active', () => {
    render(
      <DashboardPage
        systemInfo={mockSystemInfo}
        killSwitchActive={true}
      />
    );

    expect(
      screen.getByText('GLOBAL EMERGENCY KILL SWITCH IS ACTIVE')
    ).toBeDefined();
    expect(screen.getByText('TRADING HALTED')).toBeDefined();
  });
});
