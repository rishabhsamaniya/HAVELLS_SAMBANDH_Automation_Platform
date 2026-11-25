import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shield, Check } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PermissionGate } from "@/components/ui/PermissionGate";
import { rolesApi, RoleDTO } from "./rolesApi";

export const RolesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedRole, setSelectedRole] = useState<RoleDTO | null>(null);
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>([]);
  const [savedNotice, setSavedNotice] = useState(false);

  const { data: roles = [] } = useQuery({
    queryKey: ["roles"],
    queryFn: rolesApi.listRoles,
  });

  const { data: allPermissions = [] } = useQuery({
    queryKey: ["permissions"],
    queryFn: rolesApi.listPermissions,
  });

  const savePermsMutation = useMutation({
    mutationFn: () => rolesApi.assignRolePermissions(selectedRole!.id, selectedPermIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] });
      setSavedNotice(true);
      setTimeout(() => setSavedNotice(false), 2500);
    },
  });

  const handleSelectRole = (role: RoleDTO) => {
    setSelectedRole(role);
    setSelectedPermIds(role.permissions.map((p) => p.id));
    setSavedNotice(false);
  };

  const togglePerm = (id: string) => {
    setSelectedPermIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Roles &amp; Permissions</h1>
        <p className="text-xs text-ink-secondary mt-1">
          Select a role to configure dynamic module permissions enforced on the backend.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3">
          {roles.map((role) => (
            <button
              key={role.id}
              type="button"
              onClick={() => handleSelectRole(role)}
              className={[
                "w-full text-left bg-surface-white border rounded-xl p-4 shadow-card transition-colors",
                selectedRole?.id === role.id ? "border-brand-primary bg-brand-tint/30" : "border-line hover:bg-surface-bg",
              ].join(" ")}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-ink-primary flex items-center gap-2">
                  <Shield className="h-4 w-4 text-brand-primary" />
                  {role.name}
                </span>
                <StatusBadge status={role.is_active ? "active" : "inactive"} />
              </div>
              <p className="text-xs text-ink-secondary mt-1">{role.description}</p>
              <div className="mt-2 text-xs text-ink-secondary tabular-nums">
                {role.users_count} users • {role.permissions_count} permissions
              </div>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2 bg-surface-white border border-line rounded-xl p-5 shadow-card">
          {!selectedRole ? (
            <p className="text-sm text-ink-secondary py-12 text-center">
              Select a role on the left to inspect or modify its permissions.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div>
                  <h2 className="text-base font-bold text-ink-primary">{selectedRole.name} Permissions</h2>
                  <p className="text-xs text-ink-secondary">{selectedPermIds.length} selected</p>
                </div>
                <PermissionGate permission="permissions.manage">
                  <Button
                    size="sm"
                    isLoading={savePermsMutation.isPending}
                    leftIcon={savedNotice ? <Check className="h-4 w-4" /> : undefined}
                    onClick={() => savePermsMutation.mutate()}
                  >
                    {savedNotice ? "Saved" : "Save Permissions"}
                  </Button>
                </PermissionGate>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[480px] overflow-y-auto pr-1">
                {allPermissions.map((perm) => (
                  <label
                    key={perm.id}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg border border-line hover:bg-surface-bg cursor-pointer text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPermIds.includes(perm.id)}
                      onChange={() => togglePerm(perm.id)}
                      className="mt-0.5 accent-[#D71920]"
                    />
                    <div>
                      <p className="font-medium text-ink-primary">{perm.name}</p>
                      <p className="text-[11px] text-ink-secondary font-mono">{perm.codename}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
