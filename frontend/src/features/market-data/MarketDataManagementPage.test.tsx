import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { MarketDataManagementPage } from "./MarketDataManagementPage";

describe("MarketDataManagementPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        overall_status: "HEALTHY",
        max_staleness_ms: 3000,
        is_trading_paused: false,
        stale_symbols_count: 0,
        symbols: {},
        timestamp: new Date().toISOString(),
      }),
    }));
  });

  it("renders staleness engine metrics and symbol freshness table", () => {
    render(<MarketDataManagementPage />);

    expect(screen.getByText("Market Data Ingestion & Staleness Engine")).toBeDefined();
    expect(screen.getByText("Feed Health State")).toBeDefined();
    expect(screen.getByText("Staleness Limit")).toBeDefined();
  });

  it("toggles synthetic replay generator", async () => {
    render(<MarketDataManagementPage />);

    const startBtn = screen.getByRole("button", { name: /Start Generator/i });
    await act(async () => {
      fireEvent.click(startBtn);
    });

    expect(screen.getByRole("button", { name: /Stop Generator/i })).toBeDefined();
  });
});
