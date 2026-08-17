import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { BacktestDashboardPage } from "./BacktestDashboardPage";

describe("BacktestDashboardPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";
      if (url.includes("strategies")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              strategy_id: "strat_ema_1",
              name: "Dual Moving Average Crossover",
              description: "Trend following momentum strategy",
              author_id: "usr_quant",
              source_code: "# EMA strategy",
              parameters: [],
              promotion_stage: "DRAFT",
              state: "INITIALIZED",
              symbols: ["AAPL"],
              timeframes: ["1m"],
              account_id: "acc_main",
              broker_id: "paper_broker",
              total_trades: 0,
              winning_trades: 0,
              total_pnl: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("backtest/run")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            backtest_id: "bt_demo_1",
            strategy_id: "strat_ema_1",
            config: {
              strategy_id: "strat_ema_1",
              symbols: ["AAPL"],
              initial_cash: 100000,
              slippage_bps: 5,
              commission_per_order: 1,
            },
            metrics: {
              initial_equity: 100000,
              final_equity: 108420.5,
              total_net_profit: 8420.5,
              total_return_pct: 8.42,
              cagr_pct: 28.6,
              max_drawdown_pct: 3.85,
              max_drawdown_dollars: 4120.0,
              sharpe_ratio: 2.14,
              sortino_ratio: 3.08,
              profit_factor: 2.45,
              total_trades: 38,
              winning_trades: 26,
              losing_trades: 12,
              win_rate_pct: 68.42,
              average_trade_pnl: 221.59,
              average_win: 410.2,
              average_loss: 187.3,
            },
            equity_curve: [
              { timestamp: new Date().toISOString(), equity: 100000, cash: 100000, drawdown_pct: 0 },
              { timestamp: new Date().toISOString(), equity: 108420.5, cash: 88420.5, drawdown_pct: 1.2 },
            ],
            trades: [
              {
                trade_id: "trd_01",
                symbol: "AAPL",
                side: "BUY_LONG_EXIT",
                entry_time: new Date().toISOString(),
                exit_time: new Date().toISOString(),
                entry_price: 180.0,
                exit_price: 185.0,
                quantity: 10,
                pnl: 48.0,
                return_pct: 2.78,
                commission_paid: 2.0,
                holding_duration_seconds: 3600,
              },
            ],
            created_at: new Date().toISOString(),
          }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders backtesting page and configuration bar", () => {
    render(<BacktestDashboardPage />);

    expect(screen.getByText("Backtesting Engine & Walk-Forward Validation")).toBeDefined();
    expect(screen.getByText("Target Strategy")).toBeDefined();
    expect(screen.getByText("Asset Symbol")).toBeDefined();
    expect(screen.getByText("Initial Capital ($)")).toBeDefined();
    expect(screen.getByRole("button", { name: /Run Backtest/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /Run Walk-Forward/i })).toBeDefined();
  });

  it("allows running a backtest simulation and renders scorecards", async () => {
    render(<BacktestDashboardPage />);

    const runBtn = screen.getByRole("button", { name: /Run Backtest/i });
    await act(async () => {
      fireEvent.click(runBtn);
    });

    expect(screen.getByText("Net Profit")).toBeDefined();
    expect(screen.getByText("Annualized CAGR")).toBeDefined();
    expect(screen.getByText("Sharpe Ratio")).toBeDefined();
    expect(screen.getByText("Max Drawdown")).toBeDefined();
    expect(screen.getByText("Profit Factor")).toBeDefined();
  });
});
