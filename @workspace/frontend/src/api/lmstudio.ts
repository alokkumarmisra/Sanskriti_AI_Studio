// LM Studio Manager API Client for Sanskriti AI Studio

const LM_STUDIO_API = "/api/v1/dashboard/lmstudio";

export interface LmStudioStatus {
  success: boolean;
  server_status: string;
  server_url?: string;
  text_model?: string;
  vision_model?: string;
  response_time_ms?: number;
  last_health_check?: string;
  error_message?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  type?: string;
  classification: string;
  size_gb?: number | null;
  organization?: string;
  format?: string;
  quantization?: string;
}

export const lmstudioApi = {
  /**
   * Get LM Studio server status
   */
  getStatus: async (): Promise<LmStudioStatus> => {
    const url = `${LM_STUDIO_API}/status`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get available models
   */
  getModels: async () => {
    const url = `${LM_STUDIO_API}/models`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get loaded models
   */
  getLoadedModels: async () => {
    const url = `${LM_STUDIO_API}/loaded`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Test text model
   */
  testTextModel: async (payload: { prompt?: string; url?: string; model?: string }) => {
    const url = `${LM_STUDIO_API}/test/text`;
    const body = JSON.stringify(payload);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body,
    });

    return response.json();
  },

  /**
   * Test vision model
   */
  testVisionModel: async (payload: { prompt?: string; image?: string; url?: string; model?: string }) => {
    const url = `${LM_STUDIO_API}/test/vision`;
    const body = JSON.stringify(payload);

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body,
    });

    return response.json();
  },

  /**
   * Get LM Studio logs
   */
  getLogs: async (limit?: number, filterLevel?: string) => {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());
    if (filterLevel) params.append("filter_level", filterLevel);

    const url = `${LM_STUDIO_API}/logs${params.toString() ? `?${params}` : ""}`;
    const response = await fetch(url);
    return response.json();
  },
};

export default lmstudioApi;
