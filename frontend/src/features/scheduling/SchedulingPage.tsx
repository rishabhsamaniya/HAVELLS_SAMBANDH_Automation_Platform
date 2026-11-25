import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { schedulingApi } from "./schedulingApi";

export const SchedulingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"slots" | "bookings">("bookings");

  const { data: slots = [] } = useQuery({
    queryKey: ["scheduling-slots"],
    queryFn: schedulingApi.listSlots,
  });

  const { data: bookings = [] } = useQuery({
    queryKey: ["scheduling-bookings"],
    queryFn: schedulingApi.listBookings,
  });

  const toggleSlotMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      schedulingApi.updateSlot(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling-slots"] }),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => schedulingApi.cancelBooking(id, "Cancelled by internal team"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduling-bookings"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Schedule Management</h1>
        <p className="text-xs text-ink-secondary mt-1">
          Configure one-hour time slots, capacities, and manage dealer bookings.
        </p>
      </div>

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
        <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
                <th className="py-3 px-4">Time Slot</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Max Capacity</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Toggle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-sm">
              {slots.map((s) => (
                <tr key={s.id}>
                  <td className="py-3 px-4 font-semibold tabular-nums">{s.display_label}</td>
                  <td className="py-3 px-4 tabular-nums">{s.slot_duration} min</td>
                  <td className="py-3 px-4 tabular-nums">{s.max_capacity}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={s.is_active ? "active" : "inactive"} />
                  </td>
                  <td className="py-3 px-4 text-right">
                    <PermissionGate permission="scheduling.edit">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => toggleSlotMutation.mutate({ id: s.id, is_active: !s.is_active })}
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
      )}
    </div>
  );
};
