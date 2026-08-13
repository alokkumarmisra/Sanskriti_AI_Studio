// Model Management Types for Sanskriti AI Studio

export interface ModelInfo {
  id: string;
  name: string;
  type?: string;
  classification: string; // TEXT, VISION, MULTIMODAL, IMAGE_GENERATION, etc.
  size_gb?: number | null;
  organization?: string;
  format?: string;
  quantization?: string;
  source: "lmstudio" | "comfyui";
  application: "LM Studio" | "ComfyUI";
  status?: string; // available, loaded, unavailable
  capabilities?: string[];
}

export interface ModelDetails extends ModelInfo {
  details?: {
    location: string;
    last_used: string;
    compatible_with: string[];
  };
}

export interface ModelInventoryResponse {
  success: boolean;
  models: ModelInfo[];
  count: number;
  lmstudio_count: number;
  comfyui_count: number;
  total_count: number;
  resource_info?: ResourceInfo;
}

export interface ResourceInfo {
  gpu_name: string;
  total_vram_gb: number;
  vram_used_gb: number;
  vram_available_gb: number;
  utilization_percent: number;
}

export interface ModelHealthResponse {
  success: boolean;
  checks: {
    lmstudio_server: boolean;
    comfyui_server: boolean;
    models_healthy: boolean;
  };
  overall_status: string; // healthy, unhealthy
}

export interface RoutingView {
  success: boolean;
  routing: Array<{
    request_type: string;
    step1: string;
    step2: string;
    application: string;
  }>;
}

export interface SearchResult {
  success: boolean;
  query: string;
  models: ModelInfo[];
  count: number;
  total_available: number;
}

export interface FilterResult {
  success: boolean;
  filters: {
    model_type?: string;
    application?: string;
    status?: string;
  };
  models: ModelInfo[];
  count: number;
  total_available: number;
}

export interface TestModelResponse {
  success: boolean;
  status: string; // success, error, disconnected, not_configured, image_not_found
  model?: string;
  response?: string;
  response_time_ms?: number;
  error_message?: string;
}
