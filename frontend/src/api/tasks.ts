/** Task Console API client using Axios and TanStack Query. */

import axios from "axios";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE_URL = "/api/v1";

// =============================================================================
// TASK REQUEST/RESPONSE TYPES
// =============================================================================

interface TaskCreateRequest {
  project_id: string;
  milestone?: string;
  title?: string;
  description?: string;
  priority?: "low" | "medium" | "high";
  instructions?: string;
}

interface TaskResponseData {
  id: string;
  project_id: string;
  milestone?: string;
  title: string;
  description?: string;
  priority: string;
  instructions?: string;
  status: TaskStatus;
  current_agent?: string | null;
  current_operation?: string | null;
  progress: number;
  start_time?: string | null;
  completed_time?: string | null;
  elapsed_seconds: number;
  retry_count: number;
  execution_plan?: Record<string, unknown> | null;
  result?: Record<string, unknown> | null;
  error?: string | null;
  failed_stage?: string | null;
  review_status?: string | null;
  needs_approval: boolean;
  approval_action?: string | null;
  created_at: string;
  updated_at: string;
  files_created?: string[];
  files_modified?: string[];
}

interface TaskListResponse {
  tasks: TaskListItem[];
  count: number;
  project_id?: string;
  milestone?: string;
}

interface TaskListItem {
  id: string;
  project_id: string;
  milestone?: string;
  title: string;
  status: TaskStatus;
  progress: number;
  created_at: string;
  updated_at: string;
}

// Status enumeration
type TaskStatus = "pending" | "planning" | "coding" | "testing" | "debugging" | "vision_validation" | "reviewing" | "waiting_for_approval" | "completed" | "failed" | "paused" | "cancelled";

interface CreateTaskResponse {
  success: boolean;
  task_id: string;
  task: TaskResponseData;
  message: string;
}

// =============================================================================
// TASK MUTATIONS
// =============================================================================

/** Create a new task. */
export function useCreateTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: TaskCreateRequest) => {
      const res = await axios.post(`${BASE_URL}/tasks`, request);
      if (!res.data.success) throw new Error(res.data.message || "Task creation failed");
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

/** Start a task (begin execution). */
export function useStartTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.post(`${BASE_URL}/tasks/start/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to start task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

/** Pause a running task. */
export function usePauseTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.post(`${BASE_URL}/tasks/pause/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to pause task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

/** Resume a paused task. */
export function useResumeTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.post(`${BASE_URL}/tasks/resume/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to resume task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

/** Cancel a running task. */
export function useCancelTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.post(`${BASE_URL}/tasks/cancel/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to cancel task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

/** Retry a failed task. */
export function useRetryTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.post(`${BASE_URL}/tasks/retry/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to retry task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
    },
  });
}

/** Delete a task (soft delete). */
export function useDeleteTaskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await axios.delete(`${BASE_URL}/tasks/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to delete task");
      return res.data;
    },
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

// =============================================================================
// TASK QUERIES
// =============================================================================

/** List all tasks with optional filtering. */
export function useListTasksQuery(
  projectId?: string,
  milestone?: string
) {
  return useQuery({
    queryKey: ["tasks", projectId, milestone],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (projectId) params.project_id = projectId;
      if (milestone) params.milestone = milestone;
      
      const res = await axios.get(`${BASE_URL}/tasks`, { params });
      return res.data;
    },
  });
}

/** Get a single task by ID. */
export function useGetTaskQuery(taskId: string) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: async () => {
      const res = await axios.get(`${BASE_URL}/tasks/${taskId}`);
      if (!res.data.success) throw new Error(res.data.message || "Failed to get task");
      return res.data.task;
    },
  });
}
