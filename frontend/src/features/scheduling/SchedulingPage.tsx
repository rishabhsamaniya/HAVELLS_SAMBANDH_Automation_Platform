import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Clock } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { extractApiErrorMessage } from "@/utils/errorExtractor";
import {
  BookingActionOptionsDTO,
  BookingDTO,
  ExperienceActionValue,
  schedulingApi,
} from "./schedulingApi";

const FALLBACK_ACTION_OPTIONS: BookingActionOptionsDTO = {
  actions: [
    { value: "experience_completed", label: "Experience Completed" },
    { value: "experience_on_hold", label: "Experience on Hold" },
    { value: "experience_postponed", label: "Experience Postponed" },
  ],
  remarks_by_action: {
    experience_completed: [
      "Experience delivered successfully to dealer",
      "Surprise handed over & photo/video captured",
      "Dealer satisfied & feedback collected",
      "Experience completed at dealer showroom/outlet",
      "Experience completed at dealer residence/venue",
      "Experience completed with RM/team presence",
    ],
    experience_on_hold: [
      "Dealer not reachable / phone switched off",
      "Dealer out of station / travelling",
      "Awaiting dealer confirmation on venue/address",
      "Pending RM / internal approval",
      "Gift / surprise inventory pending dispatch",
      "Dealer requested to hold until further notice",
    ],
    experience_postponed: [
      "Dealer requested new date & time",
      "Dealer busy with personal / family commitment",
      "Dealer shop / showroom closed on scheduled date",
      "Logistics / vendor scheduling delay",
      "Weather / local disruption in dealer area",
      "Rescheduled by RM for better coordination",
    ],
  },
};

const VALID_EXPERIENCE_ACTIONS = new Set<string>([
  "experience_completed",
  "experience_on_hold",
  "experience_postponed",
]);

export const SchedulingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"slots" | "bookings">("bookings");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [rowDrafts, setRowDrafts] = useState<Record<string, { action: string; remarks: string }>>({});

  const [openingTime, setOpeningTime] = useState("00:00");
  const [closingTime, setClosingTime] = useState("00:00");
  const [defaultCapacity, setDefaultCapacity] = useState(1);
  const [allowSameDay, setAllowSameDay] = useState(false);

  const { data: config } = useQuery({
    queryKey: ["scheduling-config"],
    queryFn: schedulingApi.getConfig,
  });

  useEffect(() => {
    if (config) {
      setOpeningTime(config.opening_time.slice(0, 5));
      setClosingTime(config.closing_time.slice(0, 5));
      setDefaultCapacity(config.default_capacity);
      setAllowSameDay(config.allow_same_day_booking);
    }
  }, [config]);

  const { data: slots = [] } = useQuery({
    queryKey: ["scheduling-slots"],
    queryFn: schedulingApi.listSlots,
  });

  const { data: bookings = [] } = useQuery({
    queryKey: ["scheduling-bookings"],
    queryFn: schedulingApi.listBookings,
  });

  const { data: actionOptions = FALLBACK_ACTION_OPTIONS } = useQuery({
    queryKey: ["scheduling-booking-action-options"],
    queryFn: schedulingApi.getBookingActionOptions,
  });

  const saveConfigMutation = useMutation({
    mutationFn: (payload: {
      opening_time: string;
      closing_time: string;
      slot_duration: number;
      default_capacity: number;
      allow_same_day_booking: boolean;
    }) => schedulingApi.updateConfig(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling-config"] });
      queryClient.invalidateQueries({ queryKey: ["scheduling-slots"] });
      setFeedback({ type: "success", msg: "Operating hours updated and time slots synchronized." });
    },
    onError: (err) => {
      setFeedback({ type: "error", msg: extractApiErrorMessage(err, "Failed to update operating hours.") });
    },
  });

  const updateSlotMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { is_active?: boolean; max_capacity?: number } }) =>
      schedulingApi.updateSlot(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling-slots"] });
      setFeedback(null);
    },
    onError: (err) => {
      setFeedback({ type: "error", msg: extractApiErrorMessage(err, "Failed to update time slot.") });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({
      id,
      action,
      remarks,
    }: {
      id: string;
      action: ExperienceActionValue;
      remarks: string;
    }) => schedulingApi.updateBookingStatus(id, { action, remarks }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["scheduling-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-analytics"] });
      setRowDrafts((prev) => {
        const next = { ...prev };
        delete next[updated.id];
        return next;
      });
      setFeedback({
        type: "success",
        msg: `${updated.dealer_code} updated to ${updated.submission_status_label || updated.submission_status.replace(/_/g, " ")}.`,
      });
    },
    onError: (err) => {
      setFeedback({
        type: "error",
        msg: extractApiErrorMessage(err, "Failed to update booking status."),
      });
    },
  });

  const getRowState = (b: BookingDTO) => {
    const draft = rowDrafts[b.id];
    const savedAction = VALID_EXPERIENCE_ACTIONS.has(b.submission_status) ? b.submission_status : "";
    const savedRemarks = b.remarks || "";
    const action = draft ? draft.action : savedAction;
    const remarks = draft ? draft.remarks : savedRemarks;
    const isDirty = action !== savedAction || remarks !== savedRemarks;
    return { action, remarks, isDirty };
  };

  const handleActionChange = (b: BookingDTO, nextAction: string) => {
    setRowDrafts((prev) => ({
      ...prev,
      [b.id]: { action: nextAction, remarks: "" },
    }));
  };

  const handleRemarksChange = (b: BookingDTO, currentAction: string, nextRemarks: string) => {
    setRowDrafts((prev) => ({
      ...prev,
      [b.id]: { action: currentAction, remarks: nextRemarks },
    }));
  };

  const handleGenerate24Hours = () => {
    setOpeningTime("00:00");
    setClosingTime("00:00");
    saveConfigMutation.mutate({
      opening_time: "00:00",
      closing_time: "00:00",
      slot_duration: 60,
      default_capacity: Math.max(1, defaultCapacity),
      allow_same_day_booking: allowSameDay,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Schedule Management</h1>
        <p className="text-xs text-ink-secondary mt-1">
          Configure 24-hour time slots, slot capacities, and track dealer experience status with action-based remarks.
        </p>
      </div>

      {feedback && (
        <AlertBanner
          variant={feedback.type}
          message={feedback.msg}
        />
      )}

      <div className="flex gap-2 border-b border-line pb-2">
        <Button variant={tab === "bookings" ? "primary" : "ghost"} size="sm" onClick={() => setTab("bookings")}>
          Bookings ({bookings.length})
        </Button>
        <Button variant={tab === "slots" ? "primary" : "ghost"} size="sm" onClick={() => setTab("slots")}>
          Time Slots ({slots.length})
        </Button>
      </div>

      {tab === "bookings" ? (
        <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">Dealer Code</th>
                <th className="py-3 px-4">Campaign</th>
                <th className="py-3 px-4">Preferred Date</th>
                <th className="py-3 px-4">Time Slot</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {bookings.map((b) => {
                const { action, remarks, isDirty } = getRowState(b);
                const remarksOptions = action
                  ? actionOptions.remarks_by_action[action as ExperienceActionValue] || []
                  : [];
                const canSave =
                  Boolean(action) &&
                  Boolean(remarks) &&
                  isDirty &&
                  !(updateStatusMutation.isPending && updateStatusMutation.variables?.id === b.id);

                return (
                  <tr key={b.id} className="hover:bg-surface-bg/40">
                    <td className="py-3 px-4 font-semibold tabular-nums whitespace-nowrap">{b.dealer_code}</td>
                    <td className="py-3 px-4 whitespace-nowrap">{b.campaign_name}</td>
                    <td className="py-3 px-4 tabular-nums whitespace-nowrap">{b.preferred_date}</td>
                    <td className="py-3 px-4 tabular-nums whitespace-nowrap">{b.time_slot_label}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={b.submission_status} />
                    </td>
                    <td className="py-3 px-4">
                      <PermissionGate
                        permission="confirmations.edit"
                        fallback={
                          <span className="text-xs text-ink-secondary">
                            {b.submission_status_label || b.submission_status.replace(/_/g, " ")}
                          </span>
                        }
                      >
                        <select
                          aria-label={`Action for ${b.dealer_code}`}
                          value={action}
                          onChange={(e) => handleActionChange(b, e.target.value)}
                          className="h-9 min-w-[185px] px-2.5 text-xs font-medium text-ink-primary bg-surface-white border border-line rounded-lg focus:outline-none focus:border-brand-primary"
                        >
                          <option value="">Select Action</option>
                          {actionOptions.actions.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </PermissionGate>
                    </td>
                    <td className="py-3 px-4">
                      <PermissionGate
                        permission="confirmations.edit"
                        fallback={<span className="text-xs text-ink-secondary">{b.remarks || "—"}</span>}
                      >
                        <div className="flex items-center gap-2">
                          <select
                            aria-label={`Remarks for ${b.dealer_code}`}
                            value={remarks}
                            disabled={!action}
                            onChange={(e) => handleRemarksChange(b, action, e.target.value)}
                            className="h-9 min-w-[240px] max-w-[300px] px-2.5 text-xs text-ink-primary bg-surface-white border border-line rounded-lg focus:outline-none focus:border-brand-primary disabled:bg-surface-muted disabled:text-ink-secondary"
                          >
                            <option value="">
                              {action ? "Select Remark" : "Select Action first"}
                            </option>
                            {remarksOptions.map((rem) => (
                              <option key={rem} value={rem}>
                                {rem}
                              </option>
                            ))}
                          </select>
                          <Button
                            size="sm"
                            variant={canSave ? "primary" : "secondary"}
                            disabled={!canSave}
                            isLoading={
                              updateStatusMutation.isPending &&
                              updateStatusMutation.variables?.id === b.id
                            }
                            leftIcon={<Check className="h-3.5 w-3.5" />}
                            onClick={() =>
                              updateStatusMutation.mutate({
                                id: b.id,
                                action: action as ExperienceActionValue,
                                remarks,
                              })
                            }
                          >
                            Save
                          </Button>
                        </div>
                      </PermissionGate>
                    </td>
                  </tr>
                );
              })}
              {bookings.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ink-secondary">
                    No bookings recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="space-y-4">
          <PermissionGate permission="scheduling.manage">
            <div className="bg-surface-white border border-line rounded-xl p-4 shadow-card space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-brand-primary" />
                  <div>
                    <h2 className="text-sm font-semibold text-ink-primary">Operating Hours & 24-Hour Slots</h2>
                    <p className="text-xs text-ink-secondary">
                      Set 00:00 to 00:00 for full 24-hour hourly slots (12:00 AM – 12:00 AM).
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  isLoading={saveConfigMutation.isPending}
                  onClick={handleGenerate24Hours}
                >
                  Enable All 24-Hour Slots
                </Button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
                <div>
                  <label className="block text-xs font-medium text-ink-secondary mb-1">Opening Time</label>
                  <input
                    type="time"
                    value={openingTime}
                    onChange={(e) => setOpeningTime(e.target.value)}
                    className="w-full h-10 px-3 text-sm bg-surface-white border border-line rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-secondary mb-1">Closing Time (00:00 = 24h)</label>
                  <input
                    type="time"
                    value={closingTime}
                    onChange={(e) => setClosingTime(e.target.value)}
                    className="w-full h-10 px-3 text-sm bg-surface-white border border-line rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-secondary mb-1">Default Capacity</label>
                  <input
                    type="number"
                    min={1}
                    value={defaultCapacity}
                    onChange={(e) => setDefaultCapacity(Math.max(1, Number(e.target.value) || 1))}
                    className="w-full h-10 px-3 text-sm bg-surface-white border border-line rounded-lg"
                  />
                </div>
                <label className="flex items-center gap-2 h-10 text-xs font-medium text-ink-primary cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowSameDay}
                    onChange={(e) => setAllowSameDay(e.target.checked)}
                    className="accent-brand-primary"
                  />
                  Allow Same-Day Booking
                </label>
                <Button
                  size="sm"
                  isLoading={saveConfigMutation.isPending}
                  onClick={() =>
                    saveConfigMutation.mutate({
                      opening_time: openingTime,
                      closing_time: closingTime,
                      slot_duration: 60,
                      default_capacity: defaultCapacity,
                      allow_same_day_booking: allowSameDay,
                    })
                  }
                >
                  Save & Sync Slots
                </Button>
              </div>
            </div>
          </PermissionGate>

          <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                  <th className="py-3 px-4">Time Slot</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">Max Capacity</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-sm">
                {slots.map((s) => (
                  <tr key={s.id}>
                    <td className="py-3 px-4 font-semibold tabular-nums">{s.display_label}</td>
                    <td className="py-3 px-4 tabular-nums">{s.slot_duration} min</td>
                    <td className="py-3 px-4 tabular-nums">
                      <PermissionGate permission="scheduling.edit" fallback={<span>{s.max_capacity}</span>}>
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            type="button"
                            disabled={s.max_capacity <= 1 || updateSlotMutation.isPending}
                            onClick={() =>
                              updateSlotMutation.mutate({
                                id: s.id,
                                payload: { max_capacity: Math.max(1, s.max_capacity - 1) },
                              })
                            }
                            className="h-7 w-7 rounded border border-line text-ink-primary hover:bg-surface-bg disabled:opacity-40"
                          >
                            -
                          </button>
                          <span className="w-6 text-center font-semibold">{s.max_capacity}</span>
                          <button
                            type="button"
                            disabled={updateSlotMutation.isPending}
                            onClick={() =>
                              updateSlotMutation.mutate({
                                id: s.id,
                                payload: { max_capacity: s.max_capacity + 1 },
                              })
                            }
                            className="h-7 w-7 rounded border border-line text-ink-primary hover:bg-surface-bg disabled:opacity-40"
                          >
                            +
                          </button>
                        </div>
                      </PermissionGate>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={s.is_active ? "active" : "inactive"} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <PermissionGate permission="scheduling.edit">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() =>
                            updateSlotMutation.mutate({ id: s.id, payload: { is_active: !s.is_active } })
                          }
                        >
                          {s.is_active ? "Deactivate" : "Activate"}
                        </Button>
                      </PermissionGate>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
