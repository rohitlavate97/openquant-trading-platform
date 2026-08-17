import React from "react";
import {
  LayoutDashboard,
  GitBranch,
  Shield,
  Layers,
  PieChart,
  Link2,
  Terminal,
  Settings,
} from "lucide-react";

interface NavItem {
  name: string;
  icon: React.ReactNode;
  active?: boolean;
}

export const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    { name: "Overview", icon: <LayoutDashboard className="w-4 h-4" />, active: true },
    { name: "Promotion Gate", icon: <GitBranch className="w-4 h-4" /> },
    { name: "Risk Controls", icon: <Shield className="w-4 h-4" /> },
    { name: "Strategies", icon: <Layers className="w-4 h-4" /> },
    { name: "Portfolio & OMS", icon: <PieChart className="w-4 h-4" /> },
    { name: "Broker Adapters", icon: <Link2 className="w-4 h-4" /> },
    { name: "Strategy Sandbox", icon: <Terminal className="w-4 h-4" /> },
    { name: "Settings", icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <aside className="w-60 border-r border-border bg-surface/50 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Trading Control
        </div>
        {navItems.map((item) => (
          <button
            key={item.name}
            type="button"
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              item.active
                ? "bg-primary text-white shadow-sm shadow-primary/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
            }`}
          >
            {item.icon}
            <span>{item.name}</span>
          </button>
        ))}
      </div>

      <div className="p-3 bg-surface-raised rounded-xl border border-border/80 text-xs space-y-2">
        <div className="text-[11px] font-semibold text-slate-300">Capital Safety Rules</div>
        <p className="text-[10px] text-slate-400 leading-normal">
          All orders strictly gated by Pre-Trade Risk Engine and mandatory Strategy Promotion Gate.
        </p>
      </div>
    </aside>
  );
};
