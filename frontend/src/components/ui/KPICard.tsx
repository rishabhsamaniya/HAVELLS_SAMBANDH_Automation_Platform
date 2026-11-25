import React from "react";

interface KPICardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  caption?: string;
}

export const KPICard: React.FC<KPICardProps> = ({ label, value, icon, caption }) => {
  return (
    <div className="bg-surface-white border border-line rounded-xl p-5 shadow-card hover:shadow-card-hover transition-shadow">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-ink-secondary">{label}</span>
        <div className="h-9 w-9 rounded-lg bg-brand-tint text-brand-primary flex items-center justify-center shrink-0">
          {icon}
        </div>
      </div>
      <div className="mt-3 text-[28px] font-bold text-ink-primary leading-tight tabular-nums">
        {value}
      </div>
      {caption && <p className="mt-1 text-xs text-ink-secondary">{caption}</p>}
    </div>
  );
};
