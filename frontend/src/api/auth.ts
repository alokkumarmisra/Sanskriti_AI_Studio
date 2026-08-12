/** Authentication API client using Axios and TanStack Query. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1/auth";

interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string | null;
  last_name?: string | null;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  token: string;
  refresh_token: string;
  payload: {
    sub: string;
    email: string;
    roles: string[];
    exp: number;
    iat: number;
  };
}

interface ProfileData {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  role: string;
  is_active: boolean;
}


/** Register a new user. */
export function useRegisterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: RegisterRequest) => {
      const res = await axios.post(`${BASE_URL}/register`, request);
      if (!res.data.success) throw new Error(res.data.message || "Registration failed");
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}


/** Login user. */
export function useLoginMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: LoginRequest) => {
      const res = await axios.post(`${BASE_URL}/login`, request);
      if (!res.data.success) throw new Error(res.data.message || "Login failed");
      
      // Store token and refresh_token in localStorage for demo
      localStorage.setItem("auth_token", res.data.data.token);
      localStorage.setItem("auth_refresh_token", res.data.data.refresh_token);
      
      return res.data.data as AuthResponse;
    },
  });
}


/** Logout user. */
export function useLogoutMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const refreshToken = localStorage.getItem("auth_refresh_token");
      if (!refreshToken) throw new Error("No refresh token found");
      
      const res = await axios.post(`${BASE_URL}/logout`, null, {
        params: { refresh_token: refreshToken },
      });
      return res.data;
    },
    onSuccess: () => {
      // Clear auth tokens on logout
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_refresh_token");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}


/** Get user profile. */
export function useProfileQuery(userId: string) {
  return useQuery({
    queryKey: ["profile", userId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/profile`, { params: { user_id: userId } });
      if (!res.data.success) throw new Error(res.data.message || "Failed to get profile");
      return res.data as unknown as ProfileData;
    },
  });
}


/** Update user profile. */
export function useUpdateProfileMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, first_name, last_name }: { 
      userId: string;
      first_name?: string | null;
      last_name?: string | null;
    }) => {
      const res = await axios.put(`${BASE_URL}/profile`, {}, {
        params: { 
          user_id: userId,
          first_name: first_name,
          last_name: last_name
        },
      });
      if (!res.data.success) throw new Error(res.data.message || "Profile update failed");
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}


/** Change user password. */
export function useChangePasswordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, oldPassword, newPassword }: { 
      userId: string;
      oldPassword: string;
      newPassword: string;
    }) => {
      const res = await axios.post(`${BASE_URL}/password/change`, {}, {
        params: { 
          user_id: userId,
          old_password: oldPassword,
          new_password: newPassword
        },
      });
      if (!res.data.success) throw new Error(res.data.message || "Password change failed");
      return res.data;
    },
  });
}
