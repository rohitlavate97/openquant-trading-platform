import React from "react";
import {
  LayoutDashboard,
  GitBranch,
  KeyRound,
  Key,
  Shield,
  FileText,
  Server,
  Settings,
} from "lucide-react";

export type ActiveTab =
  | "overview"
  | "brokers"
  | "promotion"
  | "secrets"
  | "api-keys"
  | "audit-logs"
  | "risk"
  | "settings";

interface SidebarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: Array<{ id: ActiveTab; name: string; icon: React.ReactNode }> = [
    { id: "overview", name: "Overview", icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: "brokers", name: "Broker Adapters", icon: <Server className="w-4 h-4" /> },
    { id: "promotion", name: "Promotion Gate", icon: <GitBranch className="w-4 h-4" /> },
    { id: "secrets", name: "Broker Secrets Vault", icon: <KeyRound className="w-4 h-4" /> },
    { id: "api-keys", name: "API Keys", icon: <Key className="w-4 h-4" /> },
    { id: "audit-logs", name: "Audit Trail", icon: <FileText className="w-4 h-4" /> },
    { id: "risk", name: "Risk Controls", icon: <Shield className="w-4 h-4" /> },
    { id: "settings", name: "Settings", icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-64 border-r border-border bg-surface/50 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Platform Navigation
        </div>
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-primary text-white shadow-sm shadow-primary/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
              }`}
            >
              {item.icon}
              <span>{item.name}</span>
            </button>
          );
        })}
      </div>

      <div className="p-3 bg-surface-raised rounded-xl border border-border/80 text-xs space-y-2">
        <div className="text-[11px] font-semibold text-slate-300">Capital Safety Guarantees</div>
        <p className="text-[10px] text-slate-400 leading-normal">
          Non-Negotiable Rule 9: Every broker adapter is sandbox-validated and security-audited before live trading.
        </p>
      </div>
    </aside>
  );
};
