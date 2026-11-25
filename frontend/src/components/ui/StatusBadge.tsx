import React from "react";

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  active: { bg: "bg-[#F0FDF4]", text: "text-[#15803D]", dot: "bg-status-success" },
  confirmed: { bg: "bg-[#F0FDF4]", text: "text-[#15803D]", dot: "bg-status-success" },
  completed: { bg: "bg-[#F0FDF4]", text: "text-[#15803D]", dot: "bg-status-success" },
  pending: { bg: "bg-[#FFFBEB]", text: "text-[#B45309]", dot: "bg-status-warning" },
  shared: { bg: "bg-[#FFFBEB]", text: "text-[#B45309]", dot: "bg-status-warning" },
  rescheduled: { bg: "bg-[#FFFBEB]", text: "text-[#B45309]", dot: "bg-status-warning" },
  inactive: { bg: "bg-[#FEF2F2]", text: "text-status-error", dot: "bg-status-error" },
  expired: { bg: "bg-[#FEF2F2]", text: "text-status-error", dot: "bg-status-error" },
  deactivated: { bg: "bg-[#FEF2F2]", text: "text-status-error", dot: "bg-status-error" },
  cancelled: { bg: "bg-[#FEF2F2]", text: "text-status-error", dot: "bg-status-error" },
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const key = status.toLowerCase();
  const style = STATUS_STYLES[key] || {
    bg: "bg-surface-muted",
    text: "text-ink-primary",
    dot: "bg-ink-secondary",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${style.bg} ${style.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {status}
    </span>
  );
};
