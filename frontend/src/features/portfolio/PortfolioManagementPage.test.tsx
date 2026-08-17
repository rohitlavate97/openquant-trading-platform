import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { PortfolioManagementPage } from "./PortfolioManagementPage";

describe("PortfolioManagementPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/portfolio/summary")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            account_id: "acc_main",
            total_equity: 105000.0,
            cash_balance: 95000.0,
            margin_used: 10000.0,
            available_margin: 95000.0,
            unrealized_pnl: 1000.0,
            realized_pnl: 4000.0,
            daily_pnl: 1000.0,
            daily_pnl_pct: 1.05,
            peak_equity: 106000.0,
            current_drawdown_pct: 0.94,
            max_drawdown_pct: 2.5,
            active_positions_count: 1,
            win_rate_pct: 70.0,
            profit_factor: 2.2,
            sharpe_ratio: 2.3,
            updated_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes("/portfolio/positions") && !url.includes("close")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              account_id: "acc_main",
              symbol: "AAPL",
              side: "LONG",
              quantity: 20,
              avg_entry_price: 150.0,
              current_price: 155.0,
              market_value: 3100.0,
              unrealized_pnl: 100.0,
              unrealized_pnl_pct: 3.33,
              allocation_pct: 2.95,
              strategy_id: "strat_momentum",
            },
          ],
        });
      }

      if (url.includes("/portfolio/allocation")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { symbol_or_class: "AAPL", market_value: 3100.0, percentage: 2.95 },
            { symbol_or_class: "USD_CASH", market_value: 95000.0, percentage: 97.05 },
          ],
        });
      }

      if (url.includes("/portfolio/performance")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              timestamp: new Date().toISOString(),
              equity: 105000.0,
              drawdown_pct: 0.94,
              daily_return_pct: 1.05,
            },
          ],
        });
      }

      if (url.includes("/portfolio/positions/AAPL/close")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            symbol: "AAPL",
            order_id: "ord_close_mock_1",
            message: "Position for AAPL closed successfully via OMS.",
          }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders portfolio management page and metrics", async () => {
    render(<PortfolioManagementPage />);

    expect(screen.getByText("Portfolio Management & Performance Analytics")).toBeDefined();
    await waitFor(() => {
      expect(screen.getByText(/Total Portfolio Equity/i)).toBeDefined();
      expect(screen.getAllByText("AAPL").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("closes an active position via OMS", async () => {
    render(<PortfolioManagementPage />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeDefined();
    });

    const closeBtn = screen.getByRole("button", { name: /Close/i });
    await act(async () => {
      fireEvent.click(closeBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/Position for AAPL closed!/i)).toBeDefined();
    });
  });
});
