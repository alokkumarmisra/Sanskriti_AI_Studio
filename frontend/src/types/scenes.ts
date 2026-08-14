/** Scene Planning Workspace Types */

export interface Scene {
  id: string;
  project_id?: string;
  lyrics_id: string;
  scene_number: number;

  // Lyric association
  lyric_section?: string;
  lyric_text?: string;

  // Scene content
  title: string;
  description?: string;

  // Character information (JSON array of character objects)
  characters?: Array<{
    id: string;
    name: string;
    description?: string;
  }>;

  // Location information  
  location_name?: string;
  location_description?: string;

  // Scene attributes
  time_period?: string;
  emotion?: string;
  action?: string;

  // Visual information
  visual_theme?: string;
  visual_prompt?: string;
  negative_prompt?: string;

  // Camera and lighting
  camera_angle?: string;
  lighting?: string;
  composition?: string;

  // Duration in seconds
  duration_seconds: number;

  // Continuity notes
  continuity_notes?: string;

  // Status
  status: "draft" | "ready" | "generating" | "generated" | "failed" | "approved";

  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  project_id?: string;
  character_name: string;
  display_name?: string;

  // Physical description
  age_range?: string;
  appearance?: string;
  
  // Clothing and accessories
  clothing?: string;
  accessories?: string;

  // Visual traits
  hair_style?: string;
  eye_color?: string;
  skin_tone?: string;

  // Personality and traits
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

  // Environment and setting
  environment_type?: string;
  description?: string;
  
  // Time and atmosphere
  time_of_day?: string;
  season?: string;
  
  // Lighting
  lighting_condition?: string;

  // Architecture and structure
  architecture_style?: string;
  interior_exterior?: string;
  
  // Visual characteristics
  color_palette?: string;
  atmospheric_effects?: string;

  created_at: string;
  updated_at: string;
}

export interface SceneCreatePayload {
  title: string;
  description?: string;
  lyric_section?: string;
  lyric_text?: string;
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
}

export interface SceneUpdatePayload {
  title?: string;
  description?: string;
  lyric_section?: string;
  lyric_text?: string;
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
  duration_seconds?: number;
  continuity_notes?: string;
  status?: Scene["status"];
}

export interface SceneReorderItem {
  scene_id: string;
  position: number;
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

export interface SceneAnalysisData {
  analysis: LyricAnalysisResult;
  target_scene_count?: number;
  auto_detect_scenes?: boolean;
}

export interface GeneratedScenes {
  scenes: Array<{
    scene_number: number;
    title: string;
    description: string;
    characters: Character[];
    location_name?: string;
    visual_prompt?: string;
    negative_prompt?: string;
    duration_seconds?: number;
  }>;
  used_characters: Character[];
  used_locations: Location[];
}

export interface SceneReadinessCheck {
  scene_id: string;
  is_ready: boolean;
  issues: Array<{
    field: string;
    message: string;
    severity: "error" | "warning";
  }>;
}

export type SceneStatus = 
  | "draft" 
  | "ready" 
  | "generating" 
  | "generated" 
  | "failed" 
  | "approved";
