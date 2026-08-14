/** Lyrics API client using TanStack Query and Axios. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// Canonical backend paths:
// GET    /api/v1/projects/lyrics/{project_id}   - List lyrics for a project
// POST   /api/v1/projects/{project_id}/lyrics   - Create new lyrics
// GET    /api/v1/lyrics/{lyrics_id}             - Get single lyrics by ID
// PUT    /api/v1/lyrics/{lyrics_id}             - Update lyrics
// DELETE /api/v1/lyrics/{lyrics_id}             - Delete lyrics

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

/** Fetch lyrics for a specific project. Uses canonical path: /api/v1/projects/lyrics/{projectId} */
export function useProjectLyricsQuery(projectId: string) {
  return useQuery({
    queryKey: ["project_lyrics", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/lyrics/${projectId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch project lyrics");
      return res.data.data as LyricsItem[];
    },
  });
}

/** Create a new lyrics entry. Uses path: /api/v1/projects/{projectId}/lyrics */
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

/** Delete a lyrics entry by ID. Uses path: /api/v1/lyrics/{lyricsId} */
export function useDeleteLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (lyricsId: string) => {
      const res = await axios.delete(`/api/v1/lyrics/${lyricsId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete lyrics");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_lyrics"] });
    },
  });
}

/** Update an existing lyrics entry. Uses path: /api/v1/lyrics/{lyricsId} */
export function useUpdateLyricsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { 
      id: string;
      payload?: LyricsUpdatePayload;
    }) => {
      const res = await axios.put(`/api/v1/lyrics/${id}`, payload || {});
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
    : `/api/v1/lyrics/search?query=${encodeURIComponent(query)}`;
  
  return useQuery({
    queryKey: ["lyrics_search", query, projectId],
    queryFn: async () => {
      const res = await axios.get(url);
      if (!res.data.success) throw new Error(res.data.message || "Lyrics search failed");
      return res.data.data as LyricsItem[];
    },
  });
}

/** Get a single lyrics entry by ID. Uses path: /api/v1/lyrics/{lyricsId} */
export function useLyricsQuery(lyricsId: string) {
  return useQuery({
    queryKey: ["lyrics", lyricsId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/lyrics/${lyricsId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch lyrics");
      return res.data.data[0] as LyricsItem;
    },
  });
}
