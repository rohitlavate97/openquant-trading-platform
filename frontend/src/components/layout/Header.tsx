import React from "react";
import { Activity, ShieldCheck, Cpu, User as UserIcon } from "lucide-react";
import { KillSwitch } from "../KillSwitch";
import { Badge } from "../ui/Badge";
import { useAuthStore } from "@/lib/authStore";

interface HeaderProps {
  killSwitchActive: boolean;
  onToggleKillSwitch: (activate: boolean, flatten: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  killSwitchActive,
  onToggleKillSwitch,
}) => {
  const { user } = useAuthStore();

  return (
    <header className="h-16 border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary font-bold font-mono text-sm">
            OQ
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">OpenQuant</h1>
            <p className="text-[10px] text-slate-400 font-mono">v0.1.0 • Enterprise Core</p>
          </div>
        </div>

        <Badge variant="outline" className="hidden sm:inline-flex text-[10px] font-mono">
          Dev Environment
        </Badge>
      </div>

      <div className="flex items-center gap-4">
        {/* System Status Indicators */}
        <div className="hidden lg:flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <Activity className="w-3.5 h-3.5" />
            <span>OMS: Reconciled</span>
          </div>

          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span>Risk Engine: Active</span>
          </div>

          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Sandbox: Strict</span>
          </div>
        </div>

        {/* Global Kill Switch */}
        <KillSwitch
          isActive={killSwitchActive}
          onToggle={onToggleKillSwitch}
        />

        {/* User Profile / Role Badge */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-border/60">
            <div className="w-7 h-7 rounded-full bg-surface-raised border border-border flex items-center justify-center text-slate-300">
              <UserIcon className="w-3.5 h-3.5" />
            </div>
            <div className="hidden md:block text-left">
              <div className="text-xs font-semibold text-white leading-none">{user.full_name}</div>
              <Badge variant="default" className="text-[9px] font-mono mt-0.5 px-1 py-0 uppercase">
                {user.role}
              </Badge>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
