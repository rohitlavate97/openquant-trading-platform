import React, { useState, useEffect } from "react";
import { Layout } from "@/components/layout/Layout";
import { ActiveTab } from "@/components/layout/Sidebar";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { StrategyManagementPage } from "@/features/strategies/StrategyManagementPage";
import { BacktestDashboardPage } from "@/features/backtesting/BacktestDashboardPage";
import { PaperTradingPage } from "@/features/paper-trading/PaperTradingPage";
import { StrategySandboxPage } from "@/features/sandbox/StrategySandboxPage";
import { OrderManagementPage } from "@/features/orders/OrderManagementPage";
import { MarketDataManagementPage } from "@/features/market-data/MarketDataManagementPage";
import { BrokerAdaptersPage } from "@/features/brokers/BrokerAdaptersPage";
import { BrokerCredentialsVault } from "@/features/secrets/BrokerCredentialsVault";
import { APIKeyManagement } from "@/features/api-keys/APIKeyManagement";
import { AuditLogViewer } from "@/features/audit/AuditLogViewer";
import { PromotionGateOverview } from "@/features/promotion-gate/PromotionGateOverview";
import { RiskManagementPage } from "@/features/risk/RiskManagementPage";
import { SystemInfo } from "@/types";

export const App: React.FC = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");

  const syncSystemAndRiskState = () => {
    fetch("/api/v1/system/info")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: SystemInfo | null) => {
        if (data) {
          setSystemInfo(data);
        }
      })
      .catch(() => {});

    fetch("/api/v1/risk/config")
      .then((res) => (res.ok ? res.json() : null))
      .then((cfg) => {
        if (cfg && cfg.kill_switch) {
          setKillSwitchActive(cfg.kill_switch.is_active);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    syncSystemAndRiskState();
  }, []);

  const handleToggleKillSwitch = async (activate: boolean, flatten: boolean) => {
    setKillSwitchActive(activate);
    try {
      if (activate) {
        await fetch("/api/v1/risk/kill-switch/activate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            level: "GLOBAL",
            reason: "Top-bar Emergency Kill Switch Triggered",
            flatten_positions: flatten,
          }),
        });
      } else {
        await fetch("/api/v1/risk/kill-switch/deactivate", { method: "POST" });
      }
    } catch {}
  };

  const renderContent = () => {
    switch (activeTab) {
      case "strategies":
        return <StrategyManagementPage />;
      case "backtesting":
        return <BacktestDashboardPage />;
      case "paper-trading":
        return <PaperTradingPage />;
      case "sandbox":
        return <StrategySandboxPage />;
      case "risk":
        return <RiskManagementPage />;
      case "orders":
        return <OrderManagementPage />;
      case "market-data":
        return <MarketDataManagementPage />;
      case "brokers":
        return <BrokerAdaptersPage />;
      case "audit-logs":
        return <AuditLogViewer />;
      case "secrets":
        return <BrokerCredentialsVault />;
      case "api-keys":
        return <APIKeyManagement />;
      case "promotion":
        return (
          <div className="space-y-6">
            <h2 className="text-lg font-bold text-white">Strategy Promotion Lifecycle</h2>
            <PromotionGateOverview currentActiveStage="DRAFT" />
          </div>
        );
      case "overview":
      default:
        return (
          <DashboardPage
            systemInfo={systemInfo}
            killSwitchActive={killSwitchActive}
          />
        );
    }
  };

  return (
    <Layout
      killSwitchActive={killSwitchActive}
      onToggleKillSwitch={handleToggleKillSwitch}
      activeTab={activeTab}
      onSelectTab={setActiveTab}
    >
      {renderContent()}
    </Layout>
  );
};

export default App;
