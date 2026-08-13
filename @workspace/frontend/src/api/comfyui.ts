// ComfyUI Manager API Client for Sanskriti AI Studio

import type { ComfyUIStatus, SystemInfo, QueueStatus, WorkflowHistory, JobDetails, OutputFile, WorkflowSubmitResult, OutputPreview, HealthCheckResult, VRAMInfo } from "../types";

const COMFYUI_BASE_URL = "/api/v1/dashboard/comfyui";

export const comfyuiApi = {
  /**
   * Get ComfyUI server status and health information
   */
  getStatus: async (): Promise<ComfyUIStatus> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/status`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get system information from ComfyUI
   */
  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/system`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get queue status information
   */
  getQueueStatus: async (): Promise<QueueStatus> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/queue`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get position of a specific job in the queue
   */
  getQueuePosition: async (jobId: string): Promise<{ success: boolean; jobId: string; position: number | null; status: string | null; error_message: string | null }> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/queue/position/${encodeURIComponent(jobId)}`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get history of executed workflows
   */
  getWorkflowHistory: async (limit: number = 20): Promise<WorkflowHistory> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/history?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get details of a specific job
   */
  getJobDetails: async (jobId: string): Promise<JobDetails> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/history/${encodeURIComponent(jobId)}`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get list of output files for a completed job
   */
  getJobOutputs: async (jobId: string): Promise<{ success: boolean; jobId: string; outputs: OutputFile[]; count: number; error_message: string | null }> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/history/${encodeURIComponent(jobId)}/outputs`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Submit a workflow to ComfyUI for execution
   */
  submitWorkflow: async (workflow: string | object, inputs?: any): Promise<WorkflowSubmitResult> => {
    let workflowStr: string;
    
    if (typeof workflow === "string") {
      try {
        // Try to parse as JSON
        const parsed = JSON.parse(workflow);
        if (typeof parsed === "object" && parsed !== null) {
          workflowStr = JSON.stringify(parsed);
        } else {
          workflowStr = workflow;
        }
      } catch {
        // If parsing fails, check if it's a file path
        if (!workflow.startsWith("/") && !workflow.startsWith("http")) {
          throw new Error("Workflow must be a valid JSON string or workflow object");
        }
        workflowStr = workflow;
      }
    } else {
      workflowStr = JSON.stringify(workflow);
    }

    const payload = {
      workflow: workflowStr,
      inputs: inputs || {},
    };

    const response = await fetch(`${COMFYUI_BASE_URL}/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Submit a workflow from file
   */
  submitWorkflowFromFile: async (filepath: string): Promise<WorkflowSubmitResult> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/submit/file`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filepath }),
    });
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Cancel a running job
   */
  cancelJob: async (jobId: string): Promise<any> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/cancel/${encodeURIComponent(jobId)}`, {
      method: "POST",
    });
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get preview of an output file
   */
  getOutputPreview: async (filename: string): Promise<OutputPreview> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/output/${encodeURIComponent(filename)}`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Download an output file
   */
  downloadOutput: async (filename: string): Promise<{ success: boolean; message: string }> => {
    // Note: Actual file download is handled via browser navigation to the view endpoint
    const viewUrl = `${COMFYUI_BASE_URL}/view?filename=${encodeURIComponent(filename)}`;
    
    return {
      success: true,
      message: `To download ${filename}, open this URL in a new tab:\n\n${viewUrl}`,
    };
  },

  /**
   * Perform comprehensive health check
   */
  healthCheck: async (): Promise<HealthCheckResult> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get detailed VRAM information from ComfyUI
   */
  getVRAMInfo: async (): Promise<VRAMInfo> => {
    const response = await fetch(`${COMFYUI_BASE_URL}/vram`);
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Handle common ComfyUI errors
   */
  handleError: async (errorType: string, jobId?: string, workflow?: any, inputs?: any): Promise<any> => {
    const payload = {
      error_type: errorType,
      job_id: jobId,
      workflow,
      inputs,
    };

    const response = await fetch(`${COMFYUI_BASE_URL}/error`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      throw new Error(`ComfyUI API error: ${response.status}`);
    }

    return response.json();
  },
};
