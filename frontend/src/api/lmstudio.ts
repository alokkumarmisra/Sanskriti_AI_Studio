/**
 * LM Studio API Client
 * 
 * Provides typed HTTP requests to LM Studio Manager endpoints.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1/dashboard";

export interface LmStudioStatus {
  success: boolean;
  server_status: "connected" | "disconnected" | "unavailable";
  server_url?: string;
  text_model?: string;
  vision_model?: string;
  response_time_ms?: number;
  last_health_check?: string;
  error_message?: string;
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

export interface ModelTestResponse {
  success: boolean;
  status: "success" | "error" | "disconnected";
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

export const lmstudioApi = {
  /**
   * Get LM Studio server status and health information
   */
  getStatus(): Promise<LmStudioStatus> {
    return fetch(`${BASE_URL}/lmstudio/status`)
      .then((res) => res.json())
      .catch((err) => {
        console.error("Failed to get LM Studio status:", err);
        throw err;
      });
  },

  /**
   * Get list of all available models from LM Studio
   */
  getModels(): Promise<LmStudioModels> {
    return fetch(`${BASE_URL}/lmstudio/models`)
      .then((res) => res.json())
      .catch((err) => {
        console.error("Failed to get LM Studio models:", err);
        throw err;
      });
  },

  /**
   * Get information about currently loaded models
   */
  getLoadedModels(): Promise<LmStudioLoadedModels> {
    return fetch(`${BASE_URL}/lmstudio/loaded`)
      .then((res) => res.json())
      .catch((err) => {
        console.error("Failed to get LM Studio loaded models:", err);
        throw err;
      });
  },

  /**
   * Test text model with a simple prompt
   */
  async testTextModel(payload: { url?: string; model?: string; prompt: string }): Promise<ModelTestResponse> {
    const res = await fetch(`${BASE_URL}/lmstudio/test/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    return res.json().catch((err) => {
      console.error("Failed to test text model:", err);
      throw err;
    });
  },

  /**
   * Test vision model with image and prompt
   */
  async testVisionModel(payload: { url?: string; model?: string; image?: string; prompt?: string }): Promise<ModelTestResponse> {
    const res = await fetch(`${BASE_URL}/lmstudio/test/vision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    return res.json().catch((err) => {
      console.error("Failed to test vision model:", err);
      throw err;
    });
  },

  /**
   * Get LM Studio-related log entries
   */
  getLogs(limit?: number, filterLevel?: string): Promise<LmStudioLogs> {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());
    if (filterLevel) params.append("filter_level", filterLevel);

    return fetch(`${BASE_URL}/lmstudio/logs${params.toString()}`)
      .then((res) => res.json())
      .catch((err) => {
        console.error("Failed to get LM Studio logs:", err);
        throw err;
      });
  },
};
