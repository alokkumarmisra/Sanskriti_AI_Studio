// ComfyUI Manager Types for Sanskriti AI Studio

export interface ComfyUIStatus {
  success: boolean;
  server_status: "connected" | "disconnected" | "unavailable";
  server_url: string;
  comfyui_version: string | null;
  response_time_ms: number | null;
  last_health_check: string | null;
  error_message: string | null;
}

export interface SystemInfo {
  success: boolean;
  version: string | null;
  gpu_info: GPUInfo | {};
  memory_info: MemoryInfo | {};
  error_message: string | null;
}

export interface GPUInfo {
  name: string;
  compute_capability?: string;
  vram_total_mb?: number;
  vram_used_mb?: number;
  vram_available_mb?: number;
  utilization?: number;
}

export interface MemoryInfo {
  total_mb?: number;
  used_mb?: number;
  available_mb?: number;
}

export interface QueueItem {
  id: string;
  title: string;
  status: "RUNNING" | "PENDING" | "FAILED" | "COMPLETED" | "UNKNOWN";
  queue_position: number;
  progress?: any;
  start_time?: string;
  end_time?: string;
  duration?: number;
}

export interface QueueStatus {
  success: boolean;
  running: QueueItem[];
  pending: QueueItem[];
  completed: QueueItem[];
  failed: QueueItem[];
  total_running: number;
  total_pending: number;
  total_completed: number;
  total_failed: number;
  error_message: string | null;
}

export interface WorkflowHistoryItem {
  id: string;
  filename: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration?: number | null;
  outputs?: number | null;
  errors?: any;
}

export interface WorkflowHistory {
  success: boolean;
  workflows: WorkflowHistoryItem[];
  count: number;
  error_message: string | null;
}

export interface JobDetails {
  success: boolean;
  job_id: string | null;
  workflow: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration?: number | null;
  outputs: any[];
  errors: any | null;
  error_message: string | null;
}

export interface OutputFile {
  filename: string;
  type: "IMAGE" | "VIDEO" | "OTHER";
  size_bytes: number;
  content_type?: string;
}

export interface JobOutputs {
  success: boolean;
  job_id: string;
  outputs: OutputFile[];
  count: number;
  error_message: string | null;
}

export interface WorkflowSubmitResult {
  success: boolean;
  status: "submitted" | "failed" | "timeout" | "disconnected" | "error";
  job_id: string | null;
  message: string;
  error_message: string | null;
}

export interface OutputPreview {
  success: boolean;
  filename: string;
  view_url: string | null;
  content_length: number;
  preview_available: boolean;
}

export interface DownloadResult {
  success: boolean;
  file_info?: FileInfo | null;
  message: string;
}

export interface FileInfo {
  filename: string;
  content_type: string;
  size_bytes: number;
  is_image: boolean;
  is_video: boolean;
}

export interface HealthCheckResult {
  success: boolean;
  server_reachable: boolean;
  api_available: boolean;
  queue_accessible: boolean;
  workflow_accessible: boolean;
  generation_available: boolean;
  error_message?: string | null;
}

export interface VRAMInfo {
  success: boolean;
  gpu_name: string;
  vram_total_gb: number;
  vram_used_gb: number;
  vram_available_gb: number;
  utilization_percent: number;
  error_message?: string | null;
}

export interface ErrorHandlingResult {
  success: boolean;
  error_type: string;
  job_id: string | null;
  message: string;
  workflow_error: any;
  input_error: any;
}
