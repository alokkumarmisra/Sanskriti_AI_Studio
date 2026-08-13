// Model Management API Client for Sanskriti AI Studio

const MODEL_MANAGEMENT_API = "/api/v1/models";

export interface TestModelPayload {
  prompt?: string;
  image?: string;
}

export const modelManagementApi = {
  /**
   * Get unified inventory of all AI models
   */
  getInventory: async (limit?: number, filterStatus?: string): Promise<{
    success: boolean;
    models: any[];
    count: number;
    lmstudio_count: number;
    comfyui_count: number;
    total_count: number;
    resource_info?: any;
  }> => {
    const params = new URLSearchParams();
    if (limit) params.append("limit", limit.toString());
    if (filterStatus) params.append("filter_status", filterStatus);

    const url = `${MODEL_MANAGEMENT_API}/inventory${params.toString() ? `?${params}` : ""}`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get text models
   */
  getTextModels: async (): Promise<{
    success: boolean;
    models: any[];
    count: number;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/text`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get vision models
   */
  getVisionModels: async (): Promise<{
    success: boolean;
    models: any[];
    count: number;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/vision`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get loaded models
   */
  getLoadedModels: async (): Promise<{
    success: boolean;
    models: any[];
    count: number;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/loaded`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get generation models
   */
  getGenerationModels: async (): Promise<{
    success: boolean;
    models: any[];
    count: number;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/generation`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get model details
   */
  getModelDetails: async (modelId: string): Promise<{
    success: boolean;
    model?: any;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/details/${encodeURIComponent(modelId)}`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Search models
   */
  searchModels: async (query: string, limit?: number): Promise<{
    success: boolean;
    query: string;
    models: any[];
    count: number;
    total_available: number;
  }> => {
    const params = new URLSearchParams();
    params.append("query", query);
    if (limit) params.append("limit", limit.toString());

    const url = `${MODEL_MANAGEMENT_API}/search${params.toString() ? `?${params}` : ""}`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Filter models
   */
  filterModels: async (
    modelType?: string,
    application?: string,
    status?: string,
  ): Promise<{
    success: boolean;
    filters: any;
    models: any[];
    count: number;
  }> => {
    const params = new URLSearchParams();
    if (modelType) params.append("model_type", modelType);
    if (application) params.append("application", application);
    if (status) params.append("status", status);

    const url = `${MODEL_MANAGEMENT_API}/filter${params.toString() ? `?${params}` : ""}`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get model health
   */
  getHealth: async (): Promise<{
    success: boolean;
    checks: any;
    overall_status: string;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/health`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get routing view
   */
  getRoutingView: async (): Promise<{
    success: boolean;
    routing: any[];
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/routing`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Get resource info
   */
  getResourceInfo: async (): Promise<any> => {
    const url = `${MODEL_MANAGEMENT_API}/resource`;
    const response = await fetch(url);
    return response.json();
  },

  /**
   * Test text model
   */
  testTextModel: async (payload: TestModelPayload): Promise<{
    success: boolean;
    status: string;
    model?: string;
    response?: string;
    response_time_ms?: number;
    error_message?: string;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/test/text`;
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
  testVisionModel: async (payload: TestModelPayload): Promise<{
    success: boolean;
    status: string;
    model?: string;
    response?: string;
    response_time_ms?: number;
    error_message?: string;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/test/vision`;
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
   * Refresh models
   */
  refresh: async (): Promise<{
    success: boolean;
    lmstudio_connected?: boolean;
    comfyui_connected?: boolean;
    refreshed_at?: string;
  }> => {
    const url = `${MODEL_MANAGEMENT_API}/refresh`;
    const response = await fetch(url, { method: "POST" });
    return response.json();
  },
};
