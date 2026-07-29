/** Lyrics API client using TanStack Query and Axios. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1/projects";

/** Fetch lyrics for a specific project. */
export function useLyricsQuery(projectId: string) {
  return useQuery({
    queryKey: ["lyrics", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${projectId}/lyrics`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch lyrics");
      return res.data.data;
    },
  });
}

/** Create a new lyrics entry. */
export function useCreateLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { projectId: string; content: string; title?: string | null; language?: string; status?: string }) => {
      const res = await axios.post(
        `${BASE_URL}/${payload.projectId}/lyrics`,
        { content: payload.content, title: payload.title, language: payload.language, status: payload.status }
      );
      if (!res.data.success) throw new Error(res.data.message || "Failed to create lyrics");
      return res.data.data[0];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lyrics"] });
    },
  });
}

/** Update an existing lyrics entry. */
export function useUpdateLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload?: Partial<Record<string, string | null>> }) => {
      const res = await axios.put(`${BASE_URL}/lyrics/${id}`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to update lyrics");
      return res.data.data[0];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lyrics"] });
    },
  });
}

/** Delete a lyrics entry. */
export function useDeleteLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`${BASE_URL}/lyrics/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete lyrics");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lyrics"] });
    },
  });
}