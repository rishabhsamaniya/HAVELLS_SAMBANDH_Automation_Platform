import { apiClient } from "@/api/client";
import { ApiSuccessResponse } from "@/types/api";

export interface UserDTO {
  id: string;
  full_name: string;
  mobile_number: string;
  email: string | null;
  reporting_manager: string | null;
  reporting_manager_name: string | null;
  is_active: boolean;
  last_login: string | null;
  roles: Array<{ id: string; name: string; code: string }>;
}

export const usersApi = {
  async list(params?: Record<string, string>): Promise<UserDTO[]> {
    const { data } = await apiClient.get<ApiSuccessResponse<UserDTO[]>>("/users/", { params });
    return data.data;
  },

  async create(payload: {
    full_name: string;
    mobile_number: string;
    email?: string;
    password: string;
    role_ids: string[];
  }): Promise<UserDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<UserDTO>>("/users/", payload);
    return data.data;
  },

  async deactivate(id: string): Promise<UserDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<UserDTO>>(`/users/${id}/deactivate/`);
    return data.data;
  },

  async activate(id: string): Promise<UserDTO> {
    const { data } = await apiClient.post<ApiSuccessResponse<UserDTO>>(`/users/${id}/activate/`);
    return data.data;
  },
};
