/** Scenes API client using TanStack Query and Axios - Content & Scene Planning Workspace */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1/projects";

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface Character {
  id: string;
  project_id?: string;
  character_name: string;
  display_name?: string;
  age_range?: string;
  appearance?: string;
  clothing?: string;
  accessories?: string;
  hair_style?: string;
  eye_color?: string;
  skin_tone?: string;
  personality?: string;
  role?: string;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: string;
  project_id?: string;
  location_name: string;
  display_name?: string;
  environment_type?: string;
  description?: string;
  time_of_day?: string;
  season?: string;
  lighting_condition?: string;
  architecture_style?: string;
  interior_exterior?: string;
  color_palette?: string;
  atmospheric_effects?: string;
  created_at: string;
  updated_at: string;
}

export interface LyricAnalysisResult {
  analysis_id: string;
  lyrics_id: string;
  project_id?: string;
  verses: Array<{ section: string; text: string }>;
  chorus: string | null;
  bridge: string | null;
  characters: Array<{ name: string; description: string }>;
  locations: Array<{ name: string; description: string }>;
  events: Array<{ event: string; description: string }>;
  emotions: string[];
  themes: string[];
  visual_moments: Array<{ moment: string; description: string }>;
  recommended_scene_count?: number;
  song_duration_estimate?: number;
  narrative_complexity: "simple" | "medium" | "complex";
}

export interface LyricAnalysisRequest {
  lyrics_id: string;
  project_id?: string;
  target_scene_count?: number;
  auto_detect_scenes?: boolean;
}

// ============================================
// LYRIC ANALYSIS QUERIES AND MUTATIONS
// ============================================

/** Fetch lyric analysis result for a specific lyrics entry. */
export function useLyricAnalysisQuery(lyricsId: string) {
  return useQuery({
    queryKey: ["lyric_analysis", lyricsId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/lyrics/${lyricsId}/analysis`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch lyric analysis");
      return res.data.data as LyricAnalysisResult;
    },
  });
}

/** Fetch AI-generated scenes for a specific lyrics entry. */
export function useLyricScenesQuery(lyricsId: string, project_id?: string) {
  const url = project_id 
    ? `${BASE_URL}/${project_id}/content/scenes?lyrics_id=${lyricsId}`
    : `${BASE_URL}/content/scenes?lyrics_id=${lyricsId}`;

  return useQuery({
    queryKey: ["lyric_scenes", lyricsId, project_id],
    queryFn: async () => {
      const res = await axios.get(url);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch scenes");
      return res.data.data as SceneItem[];
    },
  });
}

/** Submit lyrics for AI analysis. */
export function useSubmitLyricAnalysisMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LyricAnalysisRequest) => {
      const res = await axios.post(`${BASE_URL}/lyrics/${payload.lyrics_id}/analysis`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to submit analysis");
      return res.data.data as LyricAnalysisResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lyric_analysis"] });
    },
  });
}

/** Generate scenes from lyrics analysis. */
export function useGenerateScenesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      lyricsId,
      project_id,
      target_scene_count,
      auto_detect_scenes,
    }: {
      lyricsId: string;
      project_id?: string;
      target_scene_count?: number;
      auto_detect_scenes?: boolean;
    }) => {
      const res = await axios.post(`${BASE_URL}/content/scenes/generate`, {
        lyrics_id: lyricsId,
        project_id,
        target_scene_count,
        auto_detect_scenes,
      });
      if (!res.data.success) throw new Error(res.data.message || "Failed to generate scenes");
      return res.data.data as SceneItem[];
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lyric_scenes"] });
    },
  });
}

// ============================================
// SCENE CRUD OPERATIONS
// ============================================

export interface SceneItem {
  id: string;
  project_id?: string;
  lyrics_id: string;
  scene_number: number;
  lyric_section?: string;
  lyric_text?: string;
  title: string;
  description?: string;
  characters?: Array<{ name: string; description?: string }>;
  location_name?: string;
  location_description?: string;
  time_period?: string;
  emotion?: string;
  action?: string;
  visual_theme?: string;
  visual_prompt?: string;
  negative_prompt?: string;
  camera_angle?: string;
  lighting?: string;
  composition?: string;
  duration_seconds: number;
  continuity_notes?: string;
  status: "draft" | "ready" | "generating" | "generated" | "failed" | "approved";
  created_at: string;
  updated_at: string;
}

/** Fetch all scenes for a project. */
export function useProjectScenesQuery(projectId: string) {
  return useQuery({
    queryKey: ["project_scenes", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${projectId}/content/scenes`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch scenes");
      return res.data.data as SceneItem[];
    },
  });
}

/** Create a new scene. */
export function useCreateSceneMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, payload }: { projectId: string; payload: Partial<SceneItem> }) => {
      const res = await axios.post(`${BASE_URL}/${projectId}/content/scenes`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to create scene");
      return res.data.data as SceneItem;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_scenes"] });
    },
  });
}

/** Update an existing scene. */
export function useUpdateSceneMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload?: Partial<SceneItem> }) => {
      const res = await axios.put(`${BASE_URL}/content/scenes/${id}`, payload || {});
      if (!res.data.success) throw new Error(res.data.message || "Failed to update scene");
      return res.data.data as SceneItem;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_scenes"] });
    },
  });
}

/** Delete a scene. */
export function useDeleteSceneMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`${BASE_URL}/content/scenes/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete scene");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_scenes"] });
    },
  });
}

/** Reorder scenes. */
export function useReorderScenesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, orderList }: { projectId: string; orderList: Array<{ scene_id: string; position: number }> }) => {
      const res = await axios.post(`${BASE_URL}/${projectId}/content/scenes/reorder`, orderList);
      if (!res.data.success) throw new Error(res.data.message || "Failed to reorder scenes");
      return true;
    },
  });
}

// ============================================
// CHARACTER OPERATIONS
// ============================================

/** Fetch all characters for a project. */
export function useProjectCharactersQuery(projectId: string) {
  return useQuery({
    queryKey: ["project_characters", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${projectId}/content/characters`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch characters");
      return res.data.data as Character[];
    },
  });
}

/** Create a new character. */
export function useCreateCharacterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, payload }: { projectId: string; payload: Partial<Character> }) => {
      const res = await axios.post(`${BASE_URL}/${projectId}/content/characters`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to create character");
      return res.data.data as Character;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_characters"] });
    },
  });
}

/** Delete a character. */
export function useDeleteCharacterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`${BASE_URL}/content/characters/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete character");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_characters"] });
    },
  });
}

// ============================================
// LOCATION OPERATIONS
// ============================================

/** Fetch all locations for a project. */
export function useProjectLocationsQuery(projectId: string) {
  return useQuery({
    queryKey: ["project_locations", projectId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/${projectId}/content/locations`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch locations");
      return res.data.data as Location[];
    },
  });
}

/** Create a new location. */
export function useCreateLocationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, payload }: { projectId: string; payload: Partial<Location> }) => {
      const res = await axios.post(`${BASE_URL}/${projectId}/content/locations`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to create location");
      return res.data.data as Location;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_locations"] });
    },
  });
}

/** Delete a location. */
export function useDeleteLocationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await axios.delete(`${BASE_URL}/content/locations/${id}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete location");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project_locations"] });
    },
  });
}

// ============================================
// PROMPT HISTORY (AI REGENERATION)
// ============================================

/** Create prompt history entry for regeneration. */
export function useCreatePromptHistoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sceneId, payload }: { sceneId: string; payload: { prompt_type: string; prompt_text: string; version?: number } }) => {
      const res = await axios.post(`${BASE_URL}/content/scenes/${sceneId}/prompts`, payload);
      if (!res.data.success) throw new Error(res.data.message || "Failed to create prompt history");
      return res.data.data as { id: string; message: string };
    },
  });
}

/** Get prompt history for a scene. */
export function useScenePromptHistoryQuery(sceneId: string) {
  return useQuery({
    queryKey: ["scene_prompt_history", sceneId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/content/scenes/${sceneId}/prompts/history`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to fetch prompt history");
      return res.data.data as Array<{ id: string; version: number; prompt_type: string; prompt_text: string }>;
    },
  });
}
