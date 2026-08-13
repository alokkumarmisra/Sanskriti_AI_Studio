/** Types for Agent Monitoring Dashboard */

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  status: string; // idle, queued, running, completed, failed, paused, etc.
  current_task?: string;
  current_operation?: string;
  start_time?: string;
  completion_time?: string;
  retry_count: number;
  last_error?: string;
  progress: number;
}

export interface AgentListItem extends Omit<AgentInfo, 'status'> {
  status: string;
  elapsed_seconds: number;
  started_at?: string; // ISO timestamp when agent started (for Date() parsing)
}

export interface ExecutionEvent {
  timestamp: string;
  agent: string;
  event_type: string;
  message?: string;
  status?: string;
}

export interface ActivityStreamResponse {
  activities: ExecutionEvent[];
  count: number;
  has_active_execution: boolean;
}

export interface ExecutionHistoryItem {
  timestamp: string;
  agent: string;
  event: string;
  details?: string;
}

export interface ExecutionHistoryResponse {
  timeline: ExecutionHistoryItem[];
  total_events: number;
}

export interface LogEntry {
  timestamp: string;
  level: string; // INFO, WARNING, ERROR, etc.
  message: string;
}

export interface LogResponse {
  agent: string;
  logs: LogEntry[];
  count: number;
  path?: string;
  note?: string;
}

export interface DashboardState {
  agents: AgentListItem[];
  activity: ActivityStreamResponse;
  history: ExecutionHistoryResponse;
  current_task_name?: string;
}
