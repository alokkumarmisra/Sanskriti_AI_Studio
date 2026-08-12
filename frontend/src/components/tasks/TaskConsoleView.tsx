import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  useListTasksQuery,
  useCreateTaskMutation,
  useStartTaskMutation,
} from "../../api/tasks";

// Task status type matching the backend
type TaskStatus = "pending" | "planning" | "coding" | "testing" | "debugging" | 
                  "vision_validation" | "reviewing" | "waiting_for_approval" | 
                  "completed" | "failed" | "paused" | "cancelled";

// Task item type for rendering
interface TaskItem {
  id: string;
  title: string;
  milestone?: string | number;
  description?: string;
  status: TaskStatus;
  progress?: number;
  error?: string;
  created_at: string;
  updated_at: string;
}

// Status colors mapping
const STATUS_COLORS: Record<TaskStatus, string> = {
  pending: "bg-gray-100 text-gray-800",
  planning: "bg-blue-100 text-blue-800",
  coding: "bg-yellow-100 text-yellow-800",
  testing: "bg-green-100 text-green-800",
  debugging: "bg-purple-100 text-purple-800",
  vision_validation: "bg-indigo-100 text-indigo-800",
  reviewing: "bg-teal-100 text-teal-800",
  waiting_for_approval: "bg-orange-100 text-orange-800",
  completed: "bg-green-500 text-white",
  failed: "bg-red-500 text-white",
  paused: "bg-gray-400 text-white",
  cancelled: "bg-gray-500 text-white",
};

// New Task Form Component
function NewTaskForm(props: { isCreating: boolean; onCreateTask: () => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<"low" | "medium" | "high">("medium");
  const [instructions, setInstructions] = useState("");

  async function handleCreateTask() {
    if (!title) return alert("Title is required");
    await props.onCreateTask();
    setTitle("");
    setDescription("");
    setInstructions("");
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm">+</span>
        Create New Task
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Task Title *</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Implement user authentication"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this task should accomplish..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as "low" | "medium" | "high")}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Instructions (Optional)</label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Additional context or instructions for the agent..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={handleCreateTask}
          disabled={props.isCreating || !title}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {props.isCreating ? (
            <span className="animate-pulse">Creating...</span>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create Task
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// Task Card Component
function TaskCard(props: { 
  task: TaskItem; 
  onStartTask: (taskId: string) => Promise<unknown>;
}) {
  const getStatusLabel = (status: TaskStatus): string => {
    switch (status) {
      case "pending": return "Pending";
      case "planning": return "Planning";
      case "coding": return "Coding";
      case "testing": return "Testing";
      case "debugging": return "Debugging";
      case "vision_validation": return "Vision Validation";
      case "reviewing": return "Reviewing";
      case "waiting_for_approval": return "Waiting for Approval";
      case "completed": return "Completed";
      case "failed": return "Failed";
      default: return status;
    }
  };

  const renderProgressBar = (progress?: number, status?: TaskStatus) => {
    if (!progress) return null;
    const width = Math.min(100, progress);
    const barColors = {
      pending: "bg-gray-400",
      planning: "bg-blue-500",
      coding: "bg-yellow-500",
      testing: "bg-green-500",
      debugging: "bg-purple-500",
      vision_validation: "bg-indigo-500",
      reviewing: "bg-teal-500",
      waiting_for_approval: "bg-orange-500",
      completed: "bg-green-600",
      failed: "bg-red-600",
      paused: "bg-gray-400",
      cancelled: "bg-gray-400",
    };

    return (
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div 
          className={`${barColors[status || "pending" as keyof typeof barColors] || "bg-gray-400"} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${width}%` }}
        />
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-800 truncate pr-4">{props.task.title}</h4>
          {typeof props.task.milestone === 'number' && (
            <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full mt-1">
              Milestone {props.task.milestone}
            </span>
          )}
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[props.task.status]}`}>
          {getStatusLabel(props.task.status)}
        </div>
      </div>

      {props.task.description && (
        <p className="text-sm text-gray-600 line-clamp-2 mb-3">{props.task.description}</p>
      )}

      {renderProgressBar(props.task.progress, props.task.status)}

      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
        <span>{new Date(props.task.created_at).toLocaleDateString()}</span>
        <span>•</span>
        <span>{props.task.updated_at ? new Date(props.task.updated_at).toLocaleTimeString() : "—"}</span>
      </div>

      <div className="flex items-center gap-2 mt-3 pt-3 border-t">
        {props.task.status === "pending" && (
          <button
            onClick={() => props.onStartTask(props.task.id)}
            className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
          >
            Start
          </button>
        )}

        {props.task.status === "planning" && (
          <span className="text-xs text-gray-500">Awaiting Planner Agent...</span>
        )}

        {props.task.status === "coding" && (
          <span className="text-xs text-gray-500">Coding Agent is working...</span>
        )}

        {props.task.status === "testing" && (
          <span className="text-xs text-gray-500">Testing Agent is running tests...</span>
        )}

        {props.task.status === "debugging" && (
          <span className="text-xs text-gray-500">Debugging Agent analyzing failures...</span>
        )}

        {props.task.status === "vision_validation" && (
          <span className="text-xs text-gray-500">Vision Pipeline validating output...</span>
        )}

        {props.task.status === "reviewing" && (
          <span className="text-xs text-gray-500">Reviewer Agent evaluating...</span>
        )}

        {props.task.status === "waiting_for_approval" && (
          <div className="flex items-center gap-2">
            <span className="text-yellow-600 font-medium">Needs Approval</span>
            <button 
              onClick={() => props.onStartTask(props.task.id)}
              className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
            >
              Approve
            </button>
          </div>
        )}

        {props.task.status === "completed" && (
          <span className="text-xs text-green-600 font-medium">✓ Completed</span>
        )}

        {props.task.status === "failed" && (
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-medium">✗ Failed</span>
            <button
              onClick={() => props.onStartTask(props.task.id)}
              className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        )}

        {props.task.status === "paused" && (
          <span className="text-gray-500">Paused</span>
        )}

        {props.task.status === "cancelled" && (
          <span className="text-gray-500">Cancelled</span>
        )}

        {props.task.error && (
          <div className="text-xs text-red-600 truncate max-w-[200px]">{props.task.error}</div>
        )}
      </div>
    </div>
  );
}

// Task Console View
export function TaskConsoleView() {
  const [selectedProject, setSelectedProject] = useState<string>("project_workspace_demo");
  const [milestoneFilter, setMilestoneFilter] = useState<string | undefined>();
  
  // Query hooks - properly destructure mutation results
  const { data: tasksData, isLoading: isTasksLoading, isError: isTasksError } = useListTasksQuery(selectedProject, milestoneFilter);
  
  // Get mutations - call .mutate() to invoke them
  const createTaskMutation = useCreateTaskMutation();
  const startTaskMutation = useStartTaskMutation();

  // Initialize projects on mount - skip for now, using demo options
  useEffect(() => {
    async function initProjects() {
      try {
        const res = await fetch(`/api/v1/projects`);
        if (res.ok) {
          console.log("Projects API call successful");
        }
      } catch (e) {
        console.error("Failed to load projects:", e);
      }
    }
    initProjects();
  }, []);

  // Derived state
  const tasks = tasksData?.tasks || [];
  
  // Use demo options if no projects loaded yet
  const projectOptions: Array<{ value: string; label: string }> = [
    { value: "project_workspace_demo", label: "Demo Project" },
    { value: "default", label: "Default" },
  ];

// Form state
  const [formTitle, setFormTitle] = useState("");
  const [formDescription] = useState("");
  const [formPriority, setFormPriority] = useState<"low" | "medium" | "high">("medium");
  const [formInstructions, setFormInstructions] = useState("");

  // Actions
  async function handleCreateTask() {
    if (!formTitle) return alert("Title is required");
    
    const response = await createTaskMutation.mutateAsync({
      project_id: selectedProject,
      milestone: milestoneFilter,
      title: formTitle,
      description: formDescription,
      priority: formPriority,
      instructions: formInstructions,
    });
    
    if (response.success) {
      alert(`Task created! Click START to begin execution.\nID: ${response.task_id}`);
      
      try {
        const startRes = await startTaskMutation.mutateAsync(response.task_id);
        if (!startRes.success) {
          alert(`Start failed: ${startRes.message}`);
        }
      } catch (e) {
        console.error("Failed to start task:", e);
      }
    } else {
      alert(response.message || "Failed to create task");
    }
  }

  return (
    <div className="space-y-6">
      {/* New Task Form */}
      <NewTaskForm 
        isCreating={false} 
        onCreateTask={handleCreateTask}
      />

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 flex items-center gap-4 flex-wrap">
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          {projectOptions.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Filter by milestone..."
          value={milestoneFilter || ""}
          onChange={(e) => setMilestoneFilter(e.target.value || undefined)}
          className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-md text-sm"
        />

        <span className="text-sm text-gray-600">
          {tasks.length} task{tasks.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Task List */}
      {isTasksLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : isTasksError ? (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          <p>Failed to load tasks. Please try refreshing the page.</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">No tasks found.</p>
          <button
            onClick={() => setFormTitle("Demo Task")}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Demo Task
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task: TaskItem) => (
            <TaskCard 
              key={task.id} 
              task={{
                id: task.id,
                title: task.title,
                milestone: task.milestone,
                description: task.description,
                status: task.status,
                progress: task.progress,
                error: task.error,
                created_at: task.created_at,
                updated_at: task.updated_at,
              }}
              onStartTask={startTaskMutation.mutateAsync}
            />
          ))}
        </div>
      )}
    </div>
  );
}
