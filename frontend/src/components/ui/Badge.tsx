import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "outline";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  className,
}) => {
  const base = "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium";
  const variants = {
    default: "bg-surface-raised text-slate-300 border border-border",
    success: "bg-success/15 text-emerald-400 border border-success/30",
    warning: "bg-warning/15 text-amber-400 border border-warning/30",
    danger: "bg-danger/15 text-rose-400 border border-danger/30",
    outline: "bg-transparent text-slate-400 border border-border",
  };

  return <span className={cn(base, variants[variant], className)}>{children}</span>;
};
