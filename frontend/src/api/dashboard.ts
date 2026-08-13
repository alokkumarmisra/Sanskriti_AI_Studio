/** Dashboard API Client for Agent Monitoring */

import type {
  AgentListItem,
  ActivityStreamResponse,
  ExecutionHistoryResponse,
  LogResponse,
} from "../types/agent-dashboard";

const API_BASE = "/api/v1/dashboard";

interface ListAgentsParams {
  include_details?: boolean;
}

export const dashboardAPI = {
  /**
   * List all available agents with their current status.
   * @param includeDetails - Whether to include detailed agent information.
   */
  listAgents: async (params?: ListAgentsParams): Promise<{
    agents: AgentListItem[];
    count: number;
    total_available: number;
  }> => {
    const response = await fetch(`${API_BASE}/agents?include_details=${params?.include_details ?? false}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to list agents");
    }
    
    return response.json();
  },

  /**
   * Get current activity stream from all agents.
   */
  getActivityStream: async (): Promise<ActivityStreamResponse> => {
    const response = await fetch(`${API_BASE}/activity/stream`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to get activity stream");
    }
    
    return response.json();
  },

  /**
   * Get execution history timeline.
   * @param limit - Maximum number of events to retrieve.
   */
  getExecutionHistory: async (limit?: number): Promise<ExecutionHistoryResponse> => {
    const url = `${API_BASE}/history${limit ? `?limit=${limit}` : ""}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to get execution history");
    }
    
    return response.json();
  },

  /**
   * Get orchestrator agent logs.
   * @param limit - Maximum number of log lines.
   * @param filterLevel - Log level filter (all, info, warning, error).
   */
  getOrchestratorLogs: async (limit = 500, filterLevel?: string): Promise<LogResponse> => {
    const url = `${API_BASE}/logs/orchestrator${limit ? `&limit=${limit}` : ""}${filterLevel ? `&filter_level=${filterLevel}` : ""}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to get orchestrator logs");
    }
    
    return response.json();
  },
};
