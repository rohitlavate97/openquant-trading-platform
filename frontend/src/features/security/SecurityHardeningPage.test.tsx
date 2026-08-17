import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { SecurityHardeningPage } from "./SecurityHardeningPage";

describe("SecurityHardeningPage", () => {
  it("renders security audit score, status, and verification matrix", () => {
    render(<SecurityHardeningPage />);
    expect(screen.getByText("Security Hardening & Penetration Audit")).toBeDefined();
    expect(screen.getByText("Rule-Enforced Guardrails")).toBeDefined();
    expect(screen.getByText("100%")).toBeDefined();
    expect(screen.getByText("AST Static Sandbox Escape Defense")).toBeDefined();
    expect(screen.getByText("AES-Fernet Secrets PBKDF2 Vault Integrity")).toBeDefined();
    expect(screen.getByText("HMAC-SHA256 & Nonce Replay Prevention")).toBeDefined();
  });

  it("allows triggering live penetration test execution", async () => {
    render(<SecurityHardeningPage />);
    const runBtn = screen.getByText("Run Live Penetration Test");
    expect(runBtn).toBeDefined();

    await act(async () => {
      fireEvent.click(runBtn);
    });

    expect(screen.getByText("Penetration Diagnostic Verification Matrix")).toBeDefined();
  });
});
