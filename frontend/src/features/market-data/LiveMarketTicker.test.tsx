import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LiveMarketTicker } from "./LiveMarketTicker";

describe("LiveMarketTicker", () => {
  it("renders live ticker header and symbols", () => {
    render(<LiveMarketTicker />);

    expect(screen.getByText("Live L1 Market Stream & Telemetry")).toBeDefined();
    expect(screen.getByText("AAPL")).toBeDefined();
    expect(screen.getByText("MSFT")).toBeDefined();
    expect(screen.getByText("NVDA")).toBeDefined();
    expect(screen.getByText("RELIANCE")).toBeDefined();
  });

  it("allows adding and tracking a new symbol", async () => {
    render(<LiveMarketTicker />);

    const input = screen.getByPlaceholderText("Add symbol (e.g. TSLA)");
    const trackBtn = screen.getByRole("button", { name: /Track/i });

    await act(async () => {
      fireEvent.change(input, { target: { value: "TSLA" } });
      fireEvent.click(trackBtn);
    });

    expect(screen.getByText("TSLA")).toBeDefined();
  });
});
