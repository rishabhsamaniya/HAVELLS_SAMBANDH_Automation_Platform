import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, CalendarCheck2, BarChart3 } from "lucide-react";
import { AxiosError } from "axios";

import { BrandLogo } from "@/components/shared/BrandLogo";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextInput";
import { ApiErrorResponse } from "@/types/api";
import { useAuth } from "./AuthContext";
import { authApi } from "./authApi";

const loginSchema = z.object({
  mobile_number: z
    .string()
    .trim()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit Indian mobile number."),
  password: z.string().min(1, "Password is required."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [forgotMode, setForgotMode] = useState(false);
  const [forgotMobile, setForgotMobile] = useState("");
  const [forgotStatus, setForgotStatus] = useState<string | null>(null);
  const [forgotLoading, setForgotLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    try {
      await login(values);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const axiosErr = err as AxiosError<ApiErrorResponse>;
      setServerError(
        axiosErr.response?.data?.error?.message || "Unable to sign in. Please verify your credentials."
      );
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotLoading(true);
    setForgotStatus(null);
    try {
      const msg = await authApi.forgotPassword(forgotMobile);
      setForgotStatus(msg);
    } catch {
      setForgotStatus("Please enter a valid 10-digit mobile number.");
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-bg flex flex-col lg:flex-row">
      {/* Left Brand Panel (Desktop) */}
      <aside className="hidden lg:flex lg:w-[45%] bg-surface-white border-r border-line p-12 flex-col justify-between">
        <div>
          <div className="h-1.5 w-14 bg-brand-primary rounded-full mb-8" />
          <BrandLogo size="lg" subtitle="Enterprise Dealer Engagement & Automation Platform" />
          <p className="mt-6 text-sm text-ink-secondary max-w-md leading-relaxed">
            Centralize dealer outreach, issue secure confirmation links, enforce real-time time-slot
            scheduling, and monitor engagement analytics across every Relationship Manager.
          </p>

          <div className="mt-10 space-y-5">
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-brand-tint text-brand-primary">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-ink-primary">Dynamic Role-Based Governance</h3>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Database-driven permissions with strict RM territory isolation and full audit trails.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-brand-tint text-brand-primary">
                <CalendarCheck2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-ink-primary">Zero-Conflict Slot Scheduling</h3>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Same-month future-only validation and atomic capacity locking prevent overbooking.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-brand-tint text-brand-primary">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-ink-primary">Actionable Channel Analytics</h3>
                <p className="text-xs text-ink-secondary mt-0.5">
                  Live KPI dashboards and permission-scoped Excel/CSV exports on demand.
                </p>
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-ink-secondary">Copyright @ 2007- 2026 Story Experiences Pvt. Ltd.</p>
      </aside>

      {/* Right Auth Card */}
      <main className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-[420px] bg-surface-white border border-line rounded-2xl shadow-modal p-7 sm:p-8">
          <div className="lg:hidden mb-6 text-center">
            <BrandLogo size="lg" subtitle="Dealer Engagement Platform" centered />
          </div>

          {!forgotMode ? (
            <>
              <div className="mb-6">
                <h1 className="text-xl font-bold text-ink-primary">Sign in to your account</h1>
                <p className="text-xs text-ink-secondary mt-1">
                  Enter your registered mobile number and password
                </p>
              </div>

              {serverError && (
                <div className="mb-4">
                  <AlertBanner variant="error" message={serverError} />
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
                <TextInput
                  label="Mobile Number"
                  prefixText="+91"
                  required
                  inputMode="numeric"
                  maxLength={10}
                  autoComplete="tel"
                  placeholder="Enter 10-digit mobile number"
                  error={errors.mobile_number?.message}
                  {...register("mobile_number")}
                />

                <TextInput
                  label="Password"
                  required
                  isPassword
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  error={errors.password?.message}
                  {...register("password")}
                />

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setForgotMode(true);
                      setForgotStatus(null);
                    }}
                    className="text-xs font-medium text-brand-primary hover:text-brand-dark transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>

                <Button
                  type="submit"
                  size="lg"
                  fullWidth
                  isLoading={isSubmitting}
                  loadingText="Signing in..."
                >
                  Sign In
                </Button>
              </form>
            </>
          ) : (
            <>
              <div className="mb-6">
                <h1 className="text-xl font-bold text-ink-primary">Reset your password</h1>
                <p className="text-xs text-ink-secondary mt-1">
                  Enter your registered 10-digit mobile number to request password reset instructions.
                </p>
              </div>

              {forgotStatus && (
                <div className="mb-4">
                  <AlertBanner variant="info" message={forgotStatus} />
                </div>
              )}

              <form onSubmit={handleForgotSubmit} className="space-y-4">
                <TextInput
                  label="Mobile Number"
                  prefixText="+91"
                  required
                  inputMode="numeric"
                  maxLength={10}
                  value={forgotMobile}
                  onChange={(e) => setForgotMobile(e.target.value)}
                  placeholder="Enter 10-digit mobile number"
                />
                <Button type="submit" size="lg" fullWidth isLoading={forgotLoading} loadingText="Sending...">
                  Request Password Reset
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="md"
                  fullWidth
                  onClick={() => setForgotMode(false)}
                >
                  Back to Sign In
                </Button>
              </form>
            </>
          )}
        </div>
      </main>
    </div>
  );
};
