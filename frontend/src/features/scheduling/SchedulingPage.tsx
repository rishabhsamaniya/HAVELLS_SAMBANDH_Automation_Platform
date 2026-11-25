import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { extractApiErrorMessage } from "@/utils/errorExtractor";
import { schedulingApi } from "./schedulingApi";

export const SchedulingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"slots" | "bookings">("bookings");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);

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

  const cancelMutation = useMutation({
    mutationFn: (id: string) => schedulingApi.cancelBooking(id, "Cancelled by internal team"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling-bookings"] }),
  });

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
          Configure 24-hour time slots, slot capacities, and manage dealer bookings.
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
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td className="py-3 px-4 font-semibold tabular-nums">{b.dealer_code}</td>
                  <td className="py-3 px-4">{b.campaign_name}</td>
                  <td className="py-3 px-4 tabular-nums">{b.preferred_date}</td>
                  <td className="py-3 px-4 tabular-nums">{b.time_slot_label}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={b.submission_status} />
                  </td>
                  <td className="py-3 px-4 text-right">
                    {b.submission_status === "confirmed" && (
                      <PermissionGate permission="confirmations.edit">
                        <Button variant="ghost" size="sm" onClick={() => cancelMutation.mutate(b.id)}>
                          Cancel
                        </Button>
                      </PermissionGate>
                    )}
                  </td>
                </tr>
              ))}
              {bookings.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-ink-secondary">
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
