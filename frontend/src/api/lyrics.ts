/** Lyrics API client using TanStack Query and Axios. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1/projects";

interface LyricsItem {
  id: string;
  project_id?: string;
  title: string | null;
  content: string;
  language: string | null;
  status: string;
}

/** Update payload for lyrics */
export interface LyricsUpdatePayload {
  title?: string | null;
  content?: string | null;
  language?: string | null;
  status?: string | null;
}


/** Fetch lyrics for a specific project. */
export function useProjectLyricsQuery(projectId: string) {
  return useQuery({
    queryKey: ["project_lyrics", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${projectId}/lyrics`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch project lyrics");
      return res.data.data as LyricsItem[];
    },
  });
}


/** Create a new lyrics entry. */
export function useCreateLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, content, title, language }: { 
      projectId: string; 
      content: string;
      title?: string | null;
      language?: string;
    }) => {
      const res = await axios.post(`${BASE_URL}/${projectId}/lyrics`, { 
        content, 
        title, 
        language 
      });
      if (!res.data.success) throw new Error(res.data.message || "Failed to create lyrics");
      return res.data.data[0] as LyricsItem;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_lyrics"] });
    },
  });
}


/** Delete a lyrics entry. */
export function useDeleteLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (lyricsId: string) => {
      const res = await axios.delete(`${BASE_URL}/lyrics/${lyricsId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete lyrics");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_lyrics"] });
    },
  });
}


/** Update an existing lyrics entry. */
export function useUpdateLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { 
      id: string;
      payload?: LyricsUpdatePayload;
    }) => {
      const res = await axios.put(`${BASE_URL}/lyrics/${id}`, payload || {});
      if (!res.data.success) throw new Error(res.data.message || "Failed to update lyrics");
      return res.data.data[0] as LyricsItem;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_lyrics"] });
    },
  });
}


/** Search lyrics globally. */
export function useLyricsSearchQuery(query: string, projectId?: string) {
  const url = projectId 
    ? `${BASE_URL}/lyrics/search?query=${encodeURIComponent(query)}&project_id=${projectId}`
    : `${BASE_URL}/lyrics/search?query=${encodeURIComponent(query)}`;
  
  return useQuery({
    queryKey: ["lyrics_search", query, projectId],
    queryFn: async () => {
      const res = await axios.get(url);
      if (!res.data.success) throw new Error(res.data.message || "Lyrics search failed");
      return res.data.data as LyricsItem[];
    },
  });
}


/** Get a single lyrics entry by ID. */
export function useLyricsQuery(lyricsId: string) {
  return useQuery({
    queryKey: ["lyrics", lyricsId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/lyrics/${lyricsId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch lyrics");
      return res.data.data[0] as LyricsItem;
    },
  });
}
