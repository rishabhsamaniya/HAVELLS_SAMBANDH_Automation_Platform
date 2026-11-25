import React, { useState } from "react";
import { AlertCircle, Eye, EyeOff } from "lucide-react";

export interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  prefixText?: string;
  isPassword?: boolean;
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, helperText, prefixText, isPassword = false, required, id, className = "", type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const inputId = id || `input-${label.toLowerCase().replace(/\s+/g, "-")}`;
    const resolvedType = isPassword ? (showPassword ? "text" : "password") : type || "text";

    return (
      <div className="space-y-1.5">
        <label htmlFor={inputId} className="block text-sm font-medium text-ink-primary">
          {label}
          {required && <span className="text-brand-primary ml-0.5">*</span>}
        </label>
        <div className="relative flex items-center">
          {prefixText && (
            <span className="inline-flex items-center h-[42px] px-3 rounded-l-lg border border-r-0 border-line bg-surface-muted text-sm text-ink-secondary font-medium select-none">
              {prefixText}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            type={resolvedType}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : undefined}
            className={[
              "w-full h-[42px] px-3.5 text-sm text-ink-primary bg-surface-white border transition-colors duration-150",
              "placeholder:text-ink-secondary/70 focus:outline-none focus:ring-2",
              "disabled:bg-surface-muted disabled:text-ink-secondary disabled:cursor-not-allowed",
              prefixText ? "rounded-r-lg" : "rounded-lg",
              isPassword ? "pr-10" : "",
              error
                ? "border-status-error focus:border-status-error focus:ring-red-100"
                : "border-line focus:border-brand-primary focus:ring-brand-primary/15",
              className,
            ].join(" ")}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 text-ink-secondary hover:text-ink-primary transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>
        {error ? (
          <p id={`${inputId}-error`} role="alert" className="flex items-center gap-1.5 text-xs text-status-error">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </p>
        ) : helperText ? (
          <p className="text-xs text-ink-secondary">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

TextInput.displayName = "TextInput";
