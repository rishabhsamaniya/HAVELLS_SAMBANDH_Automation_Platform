import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextInput";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AlertBanner } from "@/components/ui/AlertBanner";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { rolesApi } from "@/features/roles/rolesApi";
import { extractApiErrorMessage } from "@/utils/errorExtractor";
import { usersApi } from "./usersApi";

export const UsersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [fullName, setFullName] = useState("");
  const [mobile, setMobile] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
  });

  const { data: roles = [] } = useQuery({
    queryKey: ["roles"],
    queryFn: rolesApi.listRoles,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      usersApi.create({
        full_name: fullName,
        mobile_number: mobile,
        email: email || undefined,
        password,
        role_ids: roleId ? [roleId] : [],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setShowModal(false);
      setFullName("");
      setMobile("");
      setEmail("");
      setPassword("");
      setRoleId("");
      setFormError(null);
    },
    onError: (err) => {
      setFormError(extractApiErrorMessage(err, "Failed to create user."));
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? usersApi.deactivate(id) : usersApi.activate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">User Management</h1>
          <p className="text-xs text-ink-secondary mt-1">
            Create internal users (Admin, Management, RM, MIS Executive) and manage role access.
          </p>
        </div>
        <PermissionGate permission={["users.add", "users.manage"]}>
          <Button size="md" leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowModal(true)}>
            Add User
          </Button>
        </PermissionGate>
      </div>

      <div className="bg-surface-white border border-line rounded-xl shadow-card overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-bg border-b border-line text-xs font-semibold uppercase tracking-wider text-ink-secondary">
              <th className="py-3 px-4">Full Name</th>
              <th className="py-3 px-4">Mobile Number</th>
              <th className="py-3 px-4">Email</th>
              <th className="py-3 px-4">Role(s)</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line text-sm">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-ink-secondary">
                  Loading users...
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="hover:bg-surface-bg/60">
                  <td className="py-3 px-4 font-semibold text-ink-primary">{u.full_name}</td>
                  <td className="py-3 px-4 tabular-nums">+91 {u.mobile_number}</td>
                  <td className="py-3 px-4 text-ink-secondary">{u.email || "—"}</td>
                  <td className="py-3 px-4">
                    {u.roles.length > 0 ? u.roles.map((r) => r.name).join(", ") : "—"}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={u.is_active ? "active" : "inactive"} />
                  </td>
                  <td className="py-3 px-4 text-right">
                    <PermissionGate permission="users.manage">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => toggleMutation.mutate({ id: u.id, active: u.is_active })}
                      >
                        {u.is_active ? "Deactivate" : "Activate"}
                      </Button>
                    </PermissionGate>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface-white rounded-2xl shadow-modal max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink-primary">Create New User</h2>
              <button type="button" onClick={() => setShowModal(false)} className="text-ink-secondary">
                <X className="h-5 w-5" />
              </button>
            </div>
            {formError && <AlertBanner variant="error" message={formError} />}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate();
              }}
              className="space-y-3.5"
            >
              <TextInput label="Full Name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
              <TextInput
                label="Mobile Number"
                prefixText="+91"
                required
                maxLength={10}
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
              />
              <TextInput label="Email (Optional)" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              <TextInput
                label="Password"
                required
                isPassword
                helperText="Min 8 characters, mix of letters & numbers (e.g. Havells@123)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-ink-primary">Role</label>
                <select
                  value={roleId}
                  onChange={(e) => setRoleId(e.target.value)}
                  className="w-full h-[42px] px-3 text-sm rounded-lg border border-line bg-surface-white"
                >
                  <option value="">Select Role</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createMutation.isPending}>
                  Create User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
