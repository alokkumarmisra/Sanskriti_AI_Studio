/** Projects API client using TanStack Query and Axios. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1/projects";

/** Fetch all projects. */
export function useProjectsQuery() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await axios.get(BASE_URL);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch projects");
      return res.data.data;
    },
  });
}

/** Fetch a single project by ID. */
export function useProjectQuery(id: string) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch project");
      return res.data.data[0];
    },
  });
}

/** Create a new project. */
export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Record<string, string | null>>) => {
      const res = await axios.post(BASE_URL, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to create project");
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

/** Update an existing project. */
export function useUpdateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload?: Partial<Record<string, string | null>> }) => {
      const res = await axios.put(`${BASE_URL}/${id}`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to update project");
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

/** Delete a project. */
export function useDeleteProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`${BASE_URL}/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete project");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}