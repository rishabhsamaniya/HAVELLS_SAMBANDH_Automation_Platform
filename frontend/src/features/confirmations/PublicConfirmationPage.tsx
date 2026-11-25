import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AxiosError } from "axios";
import { CheckCircle2, Clock, AlertTriangle, CalendarX2, Loader2 } from "lucide-react";

import { PublicLayout } from "@/layouts/PublicLayout";
import { BrandLogo } from "@/components/shared/BrandLogo";
import { TextInput } from "@/components/ui/TextInput";
import { Button } from "@/components/ui/Button";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { ApiErrorResponse } from "@/types/api";
import {
  AvailableSlotDTO,
  publicConfirmApi,
  PublicLinkMetadata,
  PublicSubmitResult,
} from "./publicConfirmApi";

const EXACT_SUCCESS_MESSAGE =
  "Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM.";

const publicFormSchema = z.object({
  dealer_code: z.string().trim().min(1, "Dealer Code is required."),
  mobile_number: z
    .string()
    .trim()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit Indian mobile number."),
  preferred_date: z.string().min(1, "Please select a preferred date."),
  preferred_time_slot: z.string().min(1, "Please select a preferred time slot."),
});

type PublicFormValues = z.infer<typeof publicFormSchema>;

function formatReadableDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-IN", {
    weekday: "short",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

export const PublicConfirmationPage: React.FC = () => {
  const { token = "" } = useParams<{ token: string }>();

  const [linkMeta, setLinkMeta] = useState<PublicLinkMetadata | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [fatalError, setFatalError] = useState<{ code: string; message: string } | null>(null);

  const [slots, setSlots] = useState<AvailableSlotDTO[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotNotice, setSlotNotice] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedResult, setSubmittedResult] = useState<PublicSubmitResult | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    getValues,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<PublicFormValues>({
    resolver: zodResolver(publicFormSchema),
    defaultValues: {
      dealer_code: "",
      mobile_number: "",
      preferred_date: "",
      preferred_time_slot: "",
    },
  });

  const selectedDate = watch("preferred_date");

  useEffect(() => {
    let active = true;
    (async () => {
      setPageLoading(true);
      setFatalError(null);
      try {
        const meta = await publicConfirmApi.getLinkInfo(token);
        if (active) {
          setLinkMeta(meta);
          if (meta.dealer_code) setValue("dealer_code", meta.dealer_code);
          if (meta.mobile_number) setValue("mobile_number", meta.mobile_number);
          if (meta.default_slots && meta.default_slots.length > 0) {
            setSlots(meta.default_slots);
          }
        }
      } catch (err) {
        const axiosErr = err as AxiosError<ApiErrorResponse>;
        const errData = axiosErr.response?.data?.error;
        if (active) {
          setFatalError({
            code: errData?.code || "INVALID_CONFIRMATION_TOKEN",
            message: errData?.message || "This confirmation link is invalid or unavailable.",
          });
        }
      } finally {
        if (active) setPageLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, setValue]);

  useEffect(() => {
    if (!token) return;
    if (!selectedDate) {
      setSlotNotice(null);
      if (linkMeta?.default_slots) {
        setSlots(linkMeta.default_slots);
      }
      return;
    }
    let active = true;
    setSlotNotice(null);
    (async () => {
      setSlotsLoading(true);
      try {
        const available = await publicConfirmApi.getSlotsForDate(token, selectedDate);
        if (!active) return;
        setSlots(available);
        const currentSlotId = getValues("preferred_time_slot");
        if (currentSlotId && !available.some((s) => s.id === currentSlotId)) {
          setValue("preferred_time_slot", "");
          setSlotNotice("Your previously selected time slot is unavailable for this date. Please choose another slot.");
        }
      } catch (err) {
        if (!active) return;
        const axiosErr = err as AxiosError<ApiErrorResponse>;
        const msg =
          axiosErr.response?.data?.error?.message ||
          "Unable to load time slots for the selected date. Please try again.";
        setSlots([]);
        setValue("preferred_time_slot", "");
        setSlotNotice(msg);
      } finally {
        if (active) setSlotsLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [selectedDate, token, setValue, getValues, linkMeta]);

  const onSubmit = async (values: PublicFormValues) => {
    setSubmitError(null);
    try {
      const result = await publicConfirmApi.submit(token, {
        dealer_code: values.dealer_code.trim().toUpperCase(),
        mobile_number: values.mobile_number.trim(),
        preferred_date: values.preferred_date,
        preferred_time_slot: values.preferred_time_slot,
      });
      setSubmittedResult(result);
    } catch (err) {
      const axiosErr = err as AxiosError<ApiErrorResponse>;
      const errData = axiosErr.response?.data?.error;
      setSubmitError(
        errData?.message || "Unable to submit confirmation right now. Please try again."
      );
      if (errData?.code === "TIME_SLOT_UNAVAILABLE" && selectedDate) {
        const refreshed = await publicConfirmApi.getSlotsForDate(token, selectedDate).catch(() => []);
        setSlots(refreshed);
        setValue("preferred_time_slot", "");
      }
    }
  };

  // Loading state
  if (pageLoading) {
    return (
      <PublicLayout>
        <div className="py-12 flex flex-col items-center justify-center gap-3 text-ink-secondary">
          <Loader2 className="h-7 w-7 animate-spin text-brand-primary" />
          <p className="text-sm">Validating your confirmation link...</p>
        </div>
      </PublicLayout>
    );
  }

  // Success Confirmation Screen (Exact Approved Message)
  if (submittedResult) {
    return (
      <PublicLayout>
        <div className="text-center space-y-5">
          <div className="flex justify-center">
            <BrandLogo size="sm" centered />
          </div>
          <div className="mx-auto h-16 w-16 rounded-full bg-[#F0FDF4] flex items-center justify-center">
            <CheckCircle2 className="h-9 w-9 text-status-success" />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-ink-primary">Confirmation Received</h1>
            <p className="text-sm text-ink-primary leading-relaxed">
              {submittedResult.confirmation_message || EXACT_SUCCESS_MESSAGE}
            </p>
          </div>
          <div className="bg-surface-bg border border-line rounded-xl p-4 text-left space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-ink-secondary">Dealer Code</span>
              <span className="font-semibold text-ink-primary tabular-nums">
                {submittedResult.dealer_code}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-secondary">Preferred Date</span>
              <span className="font-semibold text-ink-primary tabular-nums">
                {formatReadableDate(submittedResult.preferred_date)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-secondary">Preferred Time Slot</span>
              <span className="font-semibold text-ink-primary tabular-nums">
                {submittedResult.preferred_time_slot}
              </span>
            </div>
          </div>
        </div>
      </PublicLayout>
    );
  }

  // Fatal Link States (Expired / Invalid / Deactivated / Already Submitted)
  if (fatalError) {
    const isExpired = fatalError.code === "LINK_EXPIRED";
    const isDuplicate = fatalError.code === "DUPLICATE_SUBMISSION";
    return (
      <PublicLayout>
        <div className="text-center space-y-4 py-4">
          <div className="flex justify-center">
            <BrandLogo size="sm" centered />
          </div>
          <div className="mx-auto h-14 w-14 rounded-full bg-brand-tint flex items-center justify-center">
            {isExpired ? (
              <Clock className="h-7 w-7 text-brand-primary" />
            ) : isDuplicate ? (
              <CheckCircle2 className="h-7 w-7 text-status-success" />
            ) : (
              <AlertTriangle className="h-7 w-7 text-status-error" />
            )}
          </div>
          <h1 className="text-lg font-bold text-ink-primary">
            {isExpired
              ? "Confirmation Link Expired"
              : isDuplicate
              ? "Already Confirmed"
              : "Link Unavailable"}
          </h1>
          <p className="text-sm text-ink-secondary leading-relaxed">{fatalError.message}</p>
        </div>
      </PublicLayout>
    );
  }

  return (
    <PublicLayout>
      {/* Branded Header */}
      <div className="text-center pb-5 border-b border-line">
        <BrandLogo size="lg" centered />
        <h1 className="text-xl font-bold text-ink-primary mt-5">Date Confirmation Form</h1>
        <p className="text-xs text-ink-secondary mt-1.5">
          Please fill in your details and confirm your preferred date and time.
        </p>
      </div>

      {/* No Remaining Dates in Allowed Month Edge Case */}
      {linkMeta && !linkMeta.has_available_dates ? (
        <div className="py-8 text-center space-y-3">
          <div className="mx-auto h-12 w-12 rounded-full bg-[#FFFBEB] flex items-center justify-center">
            <CalendarX2 className="h-6 w-6 text-status-warning" />
          </div>
          <h2 className="text-base font-semibold text-ink-primary">No Available Dates Remaining</h2>
          <p className="text-xs text-ink-secondary leading-relaxed">
            There are no remaining future dates available for {linkMeta.allowed_month}. Please connect
            with your RM for assistance.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          {submitError && <AlertBanner variant="error" message={submitError} />}

          {/* Field 1: Dealer Code (Auto-filled from personalized link) */}
          <TextInput
            label="Dealer Code"
            required
            readOnly
            placeholder="Dealer Code"
            className="bg-surface-bg text-ink-primary font-semibold tabular-nums cursor-default"
            error={errors.dealer_code?.message}
            {...register("dealer_code")}
          />

          {/* Field 2: Mobile Number (Auto-filled from personalized link) */}
          <TextInput
            label="Mobile Number"
            prefixText="+91"
            required
            readOnly
            inputMode="numeric"
            maxLength={10}
            placeholder="10-digit Mobile Number"
            className="bg-surface-bg text-ink-primary font-semibold tabular-nums cursor-default"
            error={errors.mobile_number?.message}
            {...register("mobile_number")}
          />

          {/* Field 3: Preferred Date (Strictly Same-Month Future Dates from Backend) */}
          <div className="space-y-1.5">
            <label htmlFor="preferred-date" className="block text-sm font-medium text-ink-primary">
              Preferred Date<span className="text-brand-primary ml-0.5">*</span>
            </label>
            <select
              id="preferred-date"
              className={[
                "w-full h-[42px] px-3.5 text-sm text-ink-primary bg-surface-white border rounded-lg transition-colors",
                "focus:outline-none focus:ring-2",
                errors.preferred_date
                  ? "border-status-error focus:border-status-error focus:ring-red-100"
                  : "border-line focus:border-brand-primary focus:ring-brand-primary/15",
              ].join(" ")}
              {...register("preferred_date")}
            >
              <option value="">Select Preferred Date</option>
              {linkMeta?.available_dates.map((isoDate) => (
                <option key={isoDate} value={isoDate}>
                  {formatReadableDate(isoDate)}
                </option>
              ))}
            </select>
            {errors.preferred_date ? (
              <p role="alert" className="text-xs text-status-error">
                {errors.preferred_date.message}
              </p>
            ) : (
              <p className="text-xs text-ink-secondary">
                Only upcoming dates in {linkMeta?.allowed_month} are eligible.
              </p>
            )}
          </div>

          {/* Field 4: Preferred Time Slot (24-Hour Configurable 1-Hour AM/PM Slots) */}
          <div className="space-y-1.5">
            <label htmlFor="preferred-time-slot" className="block text-sm font-medium text-ink-primary">
              Preferred Time Slot<span className="text-brand-primary ml-0.5">*</span>
            </label>
            <select
              id="preferred-time-slot"
              disabled={slotsLoading}
              className={[
                "w-full h-[42px] px-3.5 text-sm text-ink-primary bg-surface-white border rounded-lg transition-colors",
                "focus:outline-none focus:ring-2 disabled:bg-surface-muted disabled:text-ink-secondary",
                errors.preferred_time_slot
                  ? "border-status-error focus:border-status-error focus:ring-red-100"
                  : "border-line focus:border-brand-primary focus:ring-brand-primary/15",
              ].join(" ")}
              {...register("preferred_time_slot")}
            >
              <option value="">
                {slotsLoading
                  ? "Loading available time slots..."
                  : selectedDate && slots.length === 0
                  ? "No time slots available for this date"
                  : "Select a Time Slot"}
              </option>
              {slots.map((slot) => (
                <option key={slot.id} value={slot.id}>
                  {slot.label}
                </option>
              ))}
            </select>
            {errors.preferred_time_slot ? (
              <p role="alert" className="text-xs text-status-error">
                {errors.preferred_time_slot.message}
              </p>
            ) : slotNotice ? (
              <p role="alert" className="text-xs text-status-warning">
                {slotNotice}
              </p>
            ) : null}
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              loadingText="Confirming..."
            >
              Confirm
            </Button>
          </div>
        </form>
      )}
    </PublicLayout>
  );
};
