import React from "react";
import { useAuth } from "@/features/auth/AuthContext";

interface PermissionGateProps {
  permission: string | string[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * UX-level permission gate driven by backend-supplied user permissions.
 * Note: All authorization is independently enforced on the Django backend.
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  permission,
  fallback = null,
  children,
}) => {
  const { hasPermission } = useAuth();
  const allowed = Array.isArray(permission)
    ? permission.some((p) => hasPermission(p))
    : hasPermission(permission);

  return <>{allowed ? children : fallback}</>;
};
