import React from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: React.ReactNode;
  killSwitchActive: boolean;
  onToggleKillSwitch: (activate: boolean, flatten: boolean) => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  killSwitchActive,
  onToggleKillSwitch,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-background text-slate-100">
      <Header
        killSwitchActive={killSwitchActive}
        onToggleKillSwitch={onToggleKillSwitch}
      />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
};
