import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { NotificationCenterPage } from "./NotificationCenterPage";

describe("NotificationCenterPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: any) => {
      const url = typeof input === "string" ? input : input?.url || "";

      if (url.includes("/notifications/channels") && !url.includes("test")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              channel_id: "chn_discord_test",
              channel_type: "DISCORD",
              name: "Quant Ops Discord",
              is_enabled: true,
              config: { webhook_url: "https://discord.mock/alerts" },
              subscribed_severities: ["CRITICAL", "ERROR", "WARNING"],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("/notifications/channels/chn_discord_test/test")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            channel_id: "chn_discord_test",
            success: true,
            message: "Successfully delivered test ping to Quant Ops Discord.",
          }),
        });
      }

      if (url.includes("/notifications/logs")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              notification_id: "notif_mock_1",
              channel_type: "DISCORD",
              severity: "CRITICAL",
              title: "GLOBAL KILL SWITCH ENGAGED",
              content: "Kill Switch active due to risk stop.",
              status: "DELIVERED",
              is_read: false,
              created_at: new Date().toISOString(),
              sent_at: new Date().toISOString(),
            },
          ],
        });
      }

      if (url.includes("/notifications/in-app")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            unread_count: 1,
            notifications: [
              {
                notification_id: "notif_mock_1",
                channel_type: "IN_APP",
                severity: "CRITICAL",
                title: "GLOBAL KILL SWITCH ENGAGED",
                content: "Kill Switch active due to risk stop.",
                status: "DELIVERED",
                is_read: false,
                created_at: new Date().toISOString(),
                sent_at: new Date().toISOString(),
              },
            ],
          }),
        });
      }

      if (url.includes("/notifications/broadcast")) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            {
              notification_id: "notif_bcast_1",
              channel_type: "DISCORD",
              severity: "WARNING",
              title: "Maintenance Notice",
              content: "Server upgrade at 22:00 UTC",
              status: "DELIVERED",
              is_read: false,
              created_at: new Date().toISOString(),
            },
          ],
        });
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({ success: true }),
      });
    }));
  });

  it("renders notification center and channels", async () => {
    render(<NotificationCenterPage />);

    expect(screen.getByText("Notification System & Event Bus")).toBeDefined();
    await waitFor(() => {
      expect(screen.getByText("Quant Ops Discord")).toBeDefined();
      expect(screen.getByText(/GLOBAL KILL SWITCH ENGAGED/i)).toBeDefined();
    });
  });

  it("tests channel connectivity ping", async () => {
    render(<NotificationCenterPage />);

    await waitFor(() => {
      expect(screen.getByText("Test Ping")).toBeDefined();
    });

    const pingBtn = screen.getByRole("button", { name: /Test Ping/i });
    await act(async () => {
      fireEvent.click(pingBtn);
    });

    await waitFor(() => {
      expect(screen.getByText(/Successfully delivered test ping/i)).toBeDefined();
    });
  });
});
