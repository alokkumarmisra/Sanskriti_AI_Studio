/**
 * LM Studio Manager Types
 * 
 * Defines TypeScript interfaces for LM Studio API responses and requests.
 */

export type ServerStatus = "connected" | "disconnected" | "unavailable";

export interface LmStudioStatus {
  success: boolean;
  server_status: ServerStatus;
  server_url?: string;
  response_time_ms?: number;
  last_health_check?: string;
  error_message?: string;
  text_model?: string;
  vision_model?: string;
}

export interface ModelInfo {
  id: string;
  name?: string;
  type?: string;
  size_gb?: number;
  format?: string;
  quantization?: string;
  organization?: string;
  classification?: "TEXT" | "VISION" | "MULTIMODAL" | "UNKNOWN";
}

export interface LmStudioModels {
  success: boolean;
  models: ModelInfo[];
  count: number;
  error_message?: string;
}

export interface LmStudioLoadedModels {
  success: boolean;
  loaded_models: ModelInfo[];
  count: number;
  error_message?: string;
}

export type TestModelStatus = "success" | "error" | "disconnected";

export interface ModelTestResponse {
  success: boolean;
  status: TestModelStatus;
  model?: string;
  response?: string;
  response_time_ms?: number;
  error_message?: string;
}

export interface LmStudioLogs {
  agent: string;
  logs: string[];
  count: number;
  path?: string;
}

export interface TextTestPayload {
  url?: string;
  model?: string;
  prompt: string;
}

export interface VisionTestPayload {
  url?: string;
  model?: string;
  image?: string;
  prompt?: string;
}
