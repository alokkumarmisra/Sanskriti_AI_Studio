#!/usr/bin/env python3
"""
Task Manager Script - AI Task Console Backend Management.

Manages task lifecycle: create, start, pause, resume, cancel, and monitor.
Uses existing agent system (Planner → Orchestrator → Agents).
"""

import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
TASKS_DIR = os.path.join(STATE_DIR, "tasks")


def get_task_path(task_id: str) -> str:
    """Get path to task state file."""
    return os.path.join(TASKS_DIR, f"task_{task_id}.json")


def load_task_json(path: str) -> Optional[Dict[str, Any]]:
    """Load task from JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_task_json(path: str, data: Dict[str, Any]) -> None:
    """Save task to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_task(
    project_id: str = "project_workspace_demo",
    milestone: str = "6.7",
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "medium",
    instructions: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task and return task data."""
    now = datetime.now(timezone.utc).isoformat()
    
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    task_data = {
        "id": task_id,
        "project_id": project_id,
        "milestone": milestone,
        "title": title or "Untitled Task",
        "description": description or "",
        "priority": priority,
        "instructions": instructions or "",
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
        "actions": [],
        "files_created": [],
        "files_modified": [],
    }
    
    task_path = get_task_path(task_id)
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": "Task created successfully"
    }


def list_tasks(project_id: Optional[str] = None, milestone: Optional[str] = None) -> Dict[str, Any]:
    """List all tasks with optional filtering."""
    tasks = []
    
    if not os.path.exists(TASKS_DIR):
        return {"tasks": [], "count": 0}
    
    for filename in os.listdir(TASKS_DIR):
        if not filename.startswith("task_"):
            continue
        task_data = load_task_json(os.path.join(TASKS_DIR, filename))
        if not task_data:
            continue
        
        # Apply filters
        if project_id and task_data.get("project_id") != project_id:
            continue
        if milestone and task_data.get("milestone") != milestone:
            continue
        
        tasks.append(task_data)
    
    # Sort by created time descending
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "tasks": tasks,
        "count": len(tasks),
        "project_id": project_id,
        "milestone": milestone
    }


def start_task(task_id: str) -> Dict[str, Any]:
    """Start a task and trigger execution plan creation."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    task_data = load_task_json(task_path)
    
    if task_data is None:
        return {
            "success": False,
            "message": f"Task not found or invalid: {task_id}"
        }
    
    if task_data.get("status") in ("completed", "failed", "cancelled"):
        return {
            "success": False,
            "message": f"Cannot start task with status: {task_data['status']}"
        }
    
    # Update task state
    task_data["status"] = "planning"
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": "Task started - Planner Agent will create execution plan"
    }


def pause_task(task_id: str) -> Dict[str, Any]:
    """Pause a running task."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    task_data = load_task_json(task_path)
    
    if task_data is None:
        return {
            "success": False,
            "message": f"Task not found or invalid: {task_id}"
        }
    
    if task_data.get("status") in ("completed", "failed", "cancelled"):
        return {
            "success": False,
            "message": f"Cannot pause completed/failed/cancelled task"
        }
    
    task_data["status"] = "paused"
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": "Task paused"
    }


def resume_task(task_id: str) -> Dict[str, Any]:
    """Resume a paused task."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    task_data = load_task_json(task_path)
    
    if task_data is None:
        return {
            "success": False,
            "message": f"Task not found or invalid: {task_id}"
        }
    
    if task_data.get("status") != "paused":
        return {
            "success": False,
            "message": f"Cannot resume non-paused task (current status: {task_data['status']})"
        }
    
    task_data["status"] = "planning"
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": "Task resumed - Planner Agent will re-create execution plan"
    }


def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a task."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    task_data = load_task_json(task_path)
    
    if task_data is None:
        return {
            "success": False,
            "message": f"Task not found or invalid: {task_id}"
        }
    
    # Can only cancel pending, planning, or paused tasks
    if task_data.get("status") in ("completed", "failed"):
        return {
            "success": False,
            "message": f"Cannot cancel completed/failed task"
        }
    
    task_data["status"] = "cancelled"
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": "Task cancelled"
    }


def retry_task(task_id: str) -> Dict[str, Any]:
    """Retry a failed task."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    task_data = load_task_json(task_path)
    
    if task_data is None:
        return {
            "success": False,
            "message": f"Task not found or invalid: {task_id}"
        }
    
    if task_data.get("status") != "failed":
        return {
            "success": False,
            "message": f"Cannot retry non-failed task (current status: {task_data['status']})"
        }
    
    task_data["status"] = "pending"
    task_data["retry_count"] = task_data.get("retry_count", 0) + 1
    task_data["error"] = None
    task_data["failed_stage"] = None
    task_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_task_json(task_path, task_data)
    
    return {
        "success": True,
        "task_id": task_id,
        "task": task_data,
        "message": f"Task queued for retry (attempt {task_data['retry_count']})"
    }


def get_task(task_id: str) -> Dict[str, Any]:
    """Get task details by ID."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    return {
        "success": True,
        "task": load_task_json(task_path)
    }


def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task (soft delete by adding to graveyard)."""
    task_path = get_task_path(task_id)
    
    if not os.path.exists(task_path):
        return {
            "success": False,
            "message": f"Task not found: {task_id}"
        }
    
    # Move to graveyard (soft delete)
    graveyard_dir = os.path.join(STATE_DIR, "tasks_graveyard")
    os.makedirs(graveyard_dir, exist_ok=True)
    graveyard_path = os.path.join(graveyard_dir, f"task_{task_id}.json")
    
    try:
        os.rename(task_path, graveyard_path)
        return {
            "success": True,
            "message": f"Task moved to graveyard: {task_id}"
        }
    except OSError as e:
        return {
            "success": False,
            "message": f"Failed to move task to graveyard: {e}"
        }


def main():
    """CLI entry point for task management."""
    parser = argparse.ArgumentParser(description="AI Task Console Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create task
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("--project", default="project_workspace_demo", help="Project ID")
    create_parser.add_argument("--milestone", default="6.7", help="Milestone")
    create_parser.add_argument("--title", help="Task title")
    create_parser.add_argument("--description", help="Task description")
    create_parser.add_argument("--priority", default="medium", help="Priority (low/medium/high)")
    create_parser.add_argument("--instructions", help="Task instructions")
    
    # List tasks
    list_parser = subparsers.add_parser("list", help="List all tasks")
    list_parser.add_argument("--project", help="Filter by project ID")
    list_parser.add_argument("--milestone", help="Filter by milestone")
    
    # Get task
    get_parser = subparsers.add_parser("get", help="Get task details")
    get_parser.add_argument("task_id", help="Task ID")
    
    # Start task
    start_parser = subparsers.add_parser("start", help="Start a task")
    start_parser.add_argument("task_id", help="Task ID")
    
    # Pause task
    pause_parser = subparsers.add_parser("pause", help="Pause a task")
    pause_parser.add_argument("task_id", help="Task ID")
    
    # Resume task
    resume_parser = subparsers.add_parser("resume", help="Resume a paused task")
    resume_parser.add_argument("task_id", help="Task ID")
    
    # Cancel task
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a task")
    cancel_parser.add_argument("task_id", help="Task ID")
    
    # Retry task
    retry_parser = subparsers.add_parser("retry", help="Retry a failed task")
    retry_parser.add_argument("task_id", help="Task ID")
    
    # Delete task
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="Task ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "create":
        result = create_task(
            project_id=args.project,
            milestone=args.milestone,
            title=args.title,
            description=args.description,
            priority=args.priority,
            instructions=args.instructions,
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "list":
        result = list_tasks(project_id=args.project, milestone=args.milestone)
        print(json.dumps(result, indent=2))
    
    elif args.command == "get":
        result = get_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "start":
        result = start_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "pause":
        result = pause_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "resume":
        result = resume_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "cancel":
        result = cancel_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "retry":
        result = retry_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == "delete":
        result = delete_task(args.task_id)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
