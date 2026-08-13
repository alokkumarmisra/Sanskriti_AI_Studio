"""API routes for Task Console Management."""

import uuid
import os
import json
from typing import Annotated, List, Optional
from datetime import datetime, timezone
from enum import StrEnum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreate(BaseModel):
    """Request schema for creating a task."""
    project_id: str = Field(..., description="Project ID this task belongs to")
    milestone: Optional[str] = Field(None, description="Milestone for this task (e.g., 6.7)")
    title: Optional[str] = Field(None, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high)$", description="Priority level")
    instructions: Optional[str] = Field(None, max_length=2000, description="Optional task instructions")


class TaskStatus(StrEnum):
    """Task status enumeration."""
    PENDING = "pending"
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    DEBUGGING = "debugging"
    VISION_VALIDATION = "vision_validation"
    REVIEWING = "reviewing"
    WAITING_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskRead(BaseModel):
    """Response schema for task details."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    project_id: str
    milestone: Optional[str]
    title: str
    description: Optional[str]
    priority: str
    instructions: Optional[str]
    status: TaskStatus
    current_agent: Optional[str]
    current_operation: Optional[str]
    progress: int
    start_time: Optional[str]
    completed_time: Optional[str]
    elapsed_seconds: int
    retry_count: int
    execution_plan: Optional[dict]
    result: Optional[dict]
    error: Optional[str]
    failed_stage: Optional[str]
    review_status: Optional[str]
    needs_approval: bool
    approval_action: Optional[str]
    created_at: str
    updated_at: str
    files_created: List[str] = Field(default=[])
    files_modified: List[str] = Field(default=[])


class TaskListItem(BaseModel):
    """Compact task info for listing."""
    id: str
    project_id: str
    milestone: Optional[str]
    title: str
    status: TaskStatus
    progress: int
    created_at: str
    updated_at: str


# =============================================================================
# TASK CRUD ENDPOINTS
# =============================================================================

@router.post("", response_model=dict)
async def create_task(payload: TaskCreate):
    """Create a new AI development task."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create initial task state
    task_data = {
        "id": task_id,
        "project_id": payload.project_id,
        "milestone": payload.milestone,
        "title": payload.title or "Untitled Task",
        "description": payload.description,
        "priority": payload.priority,
        "instructions": payload.instructions,
        "status": "pending",
        "current_agent": None,
        "current_operation": None,
        "progress": 0,
        "start_time": None,
        "completed_time": None,
        "elapsed_seconds": 0,
        "retry_count": 0,
        "execution_plan": None,
        "result": None,
        "error": None,
        "failed_stage": None,
        "review_status": None,
        "needs_approval": False,
        "approval_action": None,
        "created_at": now,
        "updated_at": now,
        "files_created": [],
        "files_modified": [],
    }
    
    # Save to state store
    tasks_dir = "ai_agents/state/tasks"
    os.makedirs(tasks_dir, exist_ok=True)
    
    task_path = os.path.join(tasks_dir, f"{task_id}.json")
    with open(task_path, "w") as f:
        json.dump(task_data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": TaskRead(**task_data),
        "message": "Task created successfully"
    }


@router.get("", response_model=dict)
async def list_tasks(
    project_id: Optional[str] = None,
    milestone: Optional[str] = None,
):
    """List all tasks with optional filtering."""
    tasks_dir = "ai_agents/state/tasks"
    
    if not os.path.exists(tasks_dir):
        return {"tasks": [], "count": 0}
    
    tasks_list = []
    for filename in os.listdir(tasks_dir):
        if not filename.startswith("task_"):
            continue
        
        task_path = os.path.join(tasks_dir, filename)
        with open(task_path, "r") as f:
            data = json.load(f)
        
        # Apply filters
        if project_id and data.get("project_id") != project_id:
            continue
        if milestone and data.get("milestone") != milestone:
            continue
        
        tasks_list.append(TaskListItem(**data))
    
    # Sort by created_at descending
    tasks_list.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "tasks": [TaskListItem.model_validate(t) for t in tasks_list],
        "count": len(tasks_list),
        "project_id": project_id,
        "milestone": milestone
    }


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: str):
    """Get task details by ID."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    return {
        "success": True,
        "task": TaskRead(**data)
    }


@router.post("/start/{task_id}", response_model=dict)
async def start_task(task_id: str):
    """Start a pending task."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    # Validate task is in a startable state
    if data.get("status") in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot start task with status: {data['status']}")
    
    # Update task state
    now = datetime.now(timezone.utc).isoformat()
    data["status"] = "planning"
    data["updated_at"] = now
    
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Task started - Planner Agent will create execution plan"
    }


@router.post("/pause/{task_id}", response_model=dict)
async def pause_task(task_id: str):
    """Pause a running task."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    # Validate task is pauseable
    if data.get("status") in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot pause completed/failed/cancelled task")
    
    # Update task state
    now = datetime.now(timezone.utc).isoformat()
    data["status"] = "paused"
    data["updated_at"] = now
    
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Task paused"
    }


@router.post("/resume/{task_id}", response_model=dict)
async def resume_task(task_id: str):
    """Resume a paused task."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    # Validate task is pausable
    if data.get("status") != "paused":
        raise HTTPException(status_code=400, detail=f"Cannot resume non-paused task (current status: {data['status']})")
    
    # Update task state
    now = datetime.now(timezone.utc).isoformat()
    data["status"] = "planning"
    data["updated_at"] = now
    
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Task resumed - Planner Agent will re-create execution plan"
    }


@router.post("/cancel/{task_id}", response_model=dict)
async def cancel_task(task_id: str):
    """Cancel a running task."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    # Validate task is cancellable
    if data.get("status") in ("completed", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel completed/failed task")
    
    # Update task state
    now = datetime.now(timezone.utc).isoformat()
    data["status"] = "cancelled"
    data["updated_at"] = now
    
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Task cancelled"
    }


@router.post("/retry/{task_id}", response_model=dict)
async def retry_task(task_id: str):
    """Retry a failed task."""
    task_path = os.path.join("ai_agents/state/tasks", f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    with open(task_path, "r") as f:
        data = json.load(f)
    
    # Validate task is retryable
    if data.get("status") != "failed":
        raise HTTPException(status_code=400, detail=f"Cannot retry non-failed task (current status: {data['status']})")
    
    # Update task state for retry
    now = datetime.now(timezone.utc).isoformat()
    data["status"] = "pending"
    data["retry_count"] = data.get("retry_count", 0) + 1
    data["error"] = None
    data["failed_stage"] = None
    data["updated_at"] = now
    
    with open(task_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Task queued for retry (attempt {data['retry_count']})"
    }


@router.delete("/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    """Soft delete a task by moving to graveyard."""
    tasks_dir = "ai_agents/state/tasks"
    graveyard_dir = "ai_agents/state/tasks_graveyard"
    
    task_path = os.path.join(tasks_dir, f"{task_id}.json")
    
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    # Create graveyard directory
    os.makedirs(graveyard_dir, exist_ok=True)
    graveyard_path = os.path.join(graveyard_dir, f"{task_id}.json")
    
    try:
        os.rename(task_path, graveyard_path)
        return {
            "success": True,
            "message": f"Task moved to graveyard: {task_id}"
        }
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to move task to graveyard: {e}")
