import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={cn(
        "bg-surface border border-border rounded-xl p-5 shadow-sm hover:border-slate-700/60 transition-colors",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
