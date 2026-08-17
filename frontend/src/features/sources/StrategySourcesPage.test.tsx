import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StrategySourcesPage } from "./StrategySourcesPage";

describe("StrategySourcesPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/sources/mt5/status")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            state: "CONNECTED",
            connected_eas_count: 2,
            messages_processed: 120,
            latency_ms: 1.5,
          }),
        });
      }

      if (url.includes("/sources/tradingview/webhook")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            success: true,
            order_id: "ord_tv_mock_1",
            message: "Order successfully submitted via TradingView alert",
            executed_at: new Date().toISOString(),
          }),
        });
      }

      if (url.includes("/sources/sheets/parse")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            total_rows: 2,
            valid_rows_count: 2,
            invalid_rows_count: 0,
            rows: [
              {
                row_index: 1,
                timestamp: "2026-08-17T12:00:00Z",
                symbol: "AAPL",
                signal_type: "BUY",
                quantity: 10,
                strategy_tag: "sheets_trend",
                is_valid: true,
              },
            ],
            parsed_orders: [
              { symbol: "AAPL", side: "BUY", quantity: 10, strategy_tag: "sheets_trend" },
            ],
          }),
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "success" }),
      });
    }));
  });

  it("renders strategy sources page and navigates tabs", async () => {
    render(<StrategySourcesPage />);

    expect(screen.getByText("Additional Strategy Sources")).toBeDefined();
    expect(screen.getByText("TradingView Webhook Ingestion")).toBeDefined();
    expect(screen.getByText("MetaTrader 5 Bridge")).toBeDefined();
    expect(screen.getByText("Structured CSV / Sheets Parser")).toBeDefined();
  });

  it("dispatches test tradingview webhook alert", async () => {
    render(<StrategySourcesPage />);

    const dispatchBtn = screen.getByRole("button", { name: /Dispatch Test Webhook Alert/i });
    await act(async () => {
      fireEvent.click(dispatchBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/TradingView Alert Executed/i)).toBeDefined();
    });
  });

  it("switches to sheets tab and parses CSV", async () => {
    render(<StrategySourcesPage />);

    const sheetsTab = screen.getByText("Structured CSV / Sheets Parser");
    await act(async () => {
      fireEvent.click(sheetsTab);
    });

    const validateBtn = screen.getByRole("button", { name: /Validate CSV Rows/i });
    await act(async () => {
      fireEvent.click(validateBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/Parsed 2 row/i)).toBeDefined();
    });
  });
});
