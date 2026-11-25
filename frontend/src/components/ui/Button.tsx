import React from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "outline-red" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  loadingText?: string;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: "bg-brand-primary text-white hover:bg-brand-dark focus-visible:ring-brand-primary/40",
  secondary: "bg-surface-white text-ink-primary border border-line hover:bg-surface-bg focus-visible:ring-brand-primary/30",
  "outline-red": "bg-surface-white text-brand-primary border border-brand-primary hover:bg-brand-tint focus-visible:ring-brand-primary/40",
  ghost: "bg-transparent text-ink-primary hover:bg-surface-muted focus-visible:ring-brand-primary/30",
  danger: "bg-status-error text-white hover:bg-red-700 focus-visible:ring-status-error/40",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-[34px] px-3 text-xs",
  md: "h-[40px] px-4 text-sm",
  lg: "h-[46px] px-6 text-sm",
};

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  isLoading = false,
  loadingText,
  fullWidth = false,
  leftIcon,
  disabled,
  className = "",
  children,
  ...props
}) => {
  return (
    <button
      disabled={disabled || isLoading}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variantStyles[variant],
        sizeStyles[size],
        fullWidth ? "w-full" : "",
        className,
      ].join(" ")}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>{loadingText || children}</span>
        </>
      ) : (
        <>
          {leftIcon}
          <span>{children}</span>
        </>
      )}
    </button>
  );
};
