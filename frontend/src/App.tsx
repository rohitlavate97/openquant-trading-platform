import React, { useState, useEffect } from "react";
import { Layout } from "@/components/layout/Layout";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { SystemInfo } from "@/types";

export const App: React.FC = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);

  useEffect(() => {
    // Fetch system info and initial risk configuration
    fetch("/api/v1/system/info")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: SystemInfo | null) => {
        if (data) {
          setSystemInfo(data);
          setKillSwitchActive(data.risk_engine.kill_switch_active);
        }
      })
      .catch(() => {
        // Fallback default state if backend is still starting
        setSystemInfo({
          platform: "OpenQuant Algorithmic Trading Platform",
          version: "0.1.0",
          environment: "development",
          debug: true,
          risk_engine: {
            kill_switch_active: false,
            max_daily_loss_percent: 3.0,
            max_drawdown_percent: 5.0,
            max_position_size_percent: 10.0,
            max_orders_per_second: 10,
          },
          sandbox: {
            max_cpu_seconds: 30,
            max_memory_mb: 512,
            execution_timeout_seconds: 60,
            strict_allowlist_mode: true,
          },
          adapters: [],
        });
      });
  }, []);

  const handleToggleKillSwitch = (activate: boolean, _flatten: boolean) => {
    setKillSwitchActive(activate);
    if (systemInfo) {
      setSystemInfo({
        ...systemInfo,
        risk_engine: {
          ...systemInfo.risk_engine,
          kill_switch_active: activate,
        },
      });
    }
  };

  return (
    <Layout
      killSwitchActive={killSwitchActive}
      onToggleKillSwitch={handleToggleKillSwitch}
    >
      <DashboardPage
        systemInfo={systemInfo}
        killSwitchActive={killSwitchActive}
      />
    </Layout>
  );
};

export default App;
