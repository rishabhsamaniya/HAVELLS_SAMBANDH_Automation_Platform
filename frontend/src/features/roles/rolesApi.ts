import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface PermissionDTO {
  id: string;
  name: string;
  codename: string;
  module: string;
  action: string;
  description: string;
}

export interface RoleDTO {
  id: string;
  name: string;
  code: string;
  description: string;
  is_system_role: boolean;
  is_active: boolean;
  users_count: number;
  permissions_count: number;
  permissions: PermissionDTO[];
}

export const rolesApi = {
  async listRoles(): Promise<RoleDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<RoleDTO[]>>("/roles/");
    return data.data;
  },

  async createRole(payload: { name: string; code: string; description?: string }): Promise<RoleDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<RoleDTO>>("/roles/", payload);
    return data.data;
  },

  async listPermissions(): Promise<PermissionDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<PermissionDTO[]>>("/permissions/");
    return data.data;
  },

  async assignRolePermissions(roleId: string, permissionIds: string[]): Promise<RoleDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<RoleDTO>>(
      `/roles/${roleId}/permissions/`,
      { permission_ids: permissionIds }
    );
    return data.data;
  },
};
