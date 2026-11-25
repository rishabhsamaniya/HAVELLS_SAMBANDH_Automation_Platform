import React from "react";
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from "lucide-react";

type AlertVariant = "success" | "warning" | "error" | "info";

interface AlertBannerProps {
  variant?: AlertVariant;
  title?: string;
  message: string;
}

const styles: Record<AlertVariant, { container: string; icon: React.ReactNode }> = {
  success: {
    container: "bg-[#F0FDF4] border-[#BBF7D0] text-[#15803D]",
    icon: <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-status-success" />,
  },
  warning: {
    container: "bg-[#FFFBEB] border-[#FDE68A] text-[#B45309]",
    icon: <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-status-warning" />,
  },
  error: {
    container: "bg-[#FEF2F2] border-[#FECACA] text-status-error",
    icon: <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-status-error" />,
  },
  info: {
    container: "bg-surface-muted border-line text-ink-primary",
    icon: <Info className="h-4 w-4 shrink-0 mt-0.5 text-ink-secondary" />,
  },
};

export const AlertBanner: React.FC<AlertBannerProps> = ({ variant = "error", title, message }) => {
  const { container, icon } = styles[variant];
  return (
    <div role="alert" className={`flex items-start gap-2.5 p-3.5 rounded-lg border text-xs leading-relaxed ${container}`}>
      {icon}
      <div>
        {title && <p className="font-semibold mb-0.5">{title}</p>}
        <p>{message}</p>
      </div>
    </div>
  );
};
