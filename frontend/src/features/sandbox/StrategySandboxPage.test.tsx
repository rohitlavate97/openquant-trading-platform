import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StrategySandboxPage } from "./StrategySandboxPage";

describe("StrategySandboxPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((url: string) => {
      if (url.includes("/validate")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            is_safe: true,
            violations: [],
            detected_imports: ["math"],
            dangerous_nodes: [],
          }),
        });
      }
      if (url.includes("/execute")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            success: true,
            execution_time_seconds: 0.005,
            memory_used_mb: 14.5,
            cpu_time_seconds: 0.004,
            output: {
              symbol: "AAPL",
              signal: "BUY",
              _logs: "Evaluated AAPL -> Signal=BUY\n",
            },
            resource_limit_exceeded: false,
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({}),
      });
    }));
  });

  it("renders code editor, AST scan button, and execute button", () => {
    render(<StrategySandboxPage />);

    expect(screen.getByText("Strategy Execution Sandbox & AST Static Analysis")).toBeDefined();
    expect(screen.getByText("Python Strategy Source Code")).toBeDefined();
    expect(screen.getByText("Scan AST Security")).toBeDefined();
    expect(screen.getByText("Execute in Sandbox")).toBeDefined();
  });

  it("allows scanning AST security and displaying safe audit banner", async () => {
    render(<StrategySandboxPage />);

    const scanBtn = screen.getByRole("button", { name: /Scan AST Security/i });
    await act(async () => {
      fireEvent.click(scanBtn);
    });

    expect(screen.getByText(/All AST checks passed/i)).toBeDefined();
  });

  it("allows executing strategy in sandbox and displaying output", async () => {
    render(<StrategySandboxPage />);

    const execBtn = screen.getByRole("button", { name: /Execute in Sandbox/i });
    await act(async () => {
      fireEvent.click(execBtn);
    });

    expect(screen.getByText("SUCCESS")).toBeDefined();
    expect(screen.getByText(/Evaluated AAPL -> Signal=BUY/i)).toBeDefined();
  });
});
