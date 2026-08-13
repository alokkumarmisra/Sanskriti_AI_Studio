/** Type definitions for Agent Dashboard components */

export interface AgentListItem {
  id: string;
  name: string;
  description?: string;
  status: "running" | "completed" | "error" | "paused" | "stopped";
  current_task?: string;
  progress: number;
  started_at?: string;
  elapsed_seconds?: number;
  last_error?: string;
}

export interface AgentListItemWithMetadata extends AgentListItem {
  created_at: string;
  updated_at: string;
}
