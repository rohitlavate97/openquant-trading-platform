import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { PaperTradingPage } from "./PaperTradingPage";

describe("PaperTradingPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/accounts")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              account_id: "acc_paper_default",
              name: "Alpha Paper Virtual Fund",
              initial_balance: 100000,
              current_cash: 94820.5,
              margin_used: 12400.0,
              portfolio_value: 107220.5,
              currency: "USD",
              created_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("/gate-status")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            session_id: "psess_demo_1",
            strategy_id: "strat_ema_1",
            days_active: 15,
            required_days: 14,
            trades_count: 34,
            required_trades: 30,
            current_drawdown_pct: 3.4,
            max_allowed_drawdown_pct: 10.0,
            eligible_for_promotion: true,
            requirements_met: [
              "Minimum 14 live paper trading days satisfied (15 days)",
              "Minimum 30 executed paper trades satisfied (34 trades)",
            ],
            requirements_pending: [],
          }),
        });
      }

      if (url.includes("/sessions")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              session_id: "psess_demo_1",
              strategy_id: "strat_ema_1",
              account_id: "acc_paper_default",
              status: "ACTIVE",
              execution_config: { latency_ms: 80, slippage_bps: 2.0, partial_fills_enabled: false, fill_ratio: 1.0 },
              symbols: ["AAPL"],
              started_at: new Date(Date.now() - 86400000 * 15).toISOString(),
              total_trades: 34,
              winning_trades: 23,
              realized_pnl: 7220.5,
              unrealized_pnl: 840.0,
              peak_portfolio_value: 108500.0,
              max_drawdown_pct: 3.4,
            },
          ],
        });
      }

      if (url.includes("/strategies")) {
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
              promotion_stage: "PAPER_TRADING",
              state: "RUNNING",
              symbols: ["AAPL"],
              timeframes: ["1m"],
              account_id: "acc_main",
              broker_id: "paper_broker",
              total_trades: 34,
              winning_trades: 23,
              total_pnl: 7220.5,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders paper trading page and virtual accounts", async () => {
    render(<PaperTradingPage />);

    expect(screen.getByText("Paper Trading Mode & Stage 5 Promotion Gate")).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText("Paper Portfolio Value")).toBeDefined();
      expect(screen.getByText("Virtual Available Cash")).toBeDefined();
    });

    expect(screen.getByRole("button", { name: /Launch Paper Session/i })).toBeDefined();
  });

  it("opens launch paper session modal upon clicking Launch button", async () => {
    render(<PaperTradingPage />);

    const launchBtn = screen.getByRole("button", { name: /Launch Paper Session/i });
    await act(async () => {
      fireEvent.click(launchBtn);
    });

    expect(screen.getByText("Launch Live Paper Trading Session")).toBeDefined();
    expect(screen.getByText("Initialize & Run")).toBeDefined();
  });
});
