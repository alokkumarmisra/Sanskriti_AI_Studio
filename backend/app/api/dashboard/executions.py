"""API endpoints for Agent Monitoring Dashboard - Execution History."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/executions", tags=["Executions"])


def load_actions_history() -> List[Dict[str, Any]]:
    """Load execution history from actions.jsonl."""
    
    actions_path = "ai_agents/state/actions.jsonl"
    if not os.path.exists(actions_path):
        return []
    
    actions = []
    with open(actions_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    actions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    # Sort by timestamp descending
    actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return actions[:100]  # Limit to last 100 entries


def load_current_task_state() -> Dict[str, Any]:
    """Load current task state from orchestrator."""
    
    task_path = "ai_agents/state/orchestrator/current_task.json"
    if not os.path.exists(task_path):
        return {}
    
    with open(task_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def load_planner_state() -> Dict[str, Any]:
    """Load planner state from current_plan.json."""
    
    plan_path = "ai_agents/state/planner/current_plan.json"
    if not os.path.exists(plan_path):
        return {}
    
    with open(plan_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def load_reviewer_state() -> Dict[str, Any]:
    """Load reviewer state from review_report.json."""
    
    review_path = "ai_agents/state/review_report.json"
    if not os.path.exists(review_path):
        return {}
    
    with open(review_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


class ExecutionEvent(BaseModel):
    """Execution event."""
    timestamp: str
    agent: str
    action_type: str
    details: Optional[str]


class ExecutionHistoryItem(BaseModel):
    """Execution history item."""
    execution_id: str
    task_name: str
    status: str
    timestamp: str
    agent: str
    event_type: str


@router.get("/history", response_model=Dict[str, Any])
async def get_execution_history(limit: int = 100):
    """Get recent execution events from actions history."""
    
    actions = load_actions_history()[:limit]
    
    # Build timeline of events
    timeline = []
    for action in actions:
        agent = action.get("agent", "unknown")
        action_type = action.get("action_type", "unknown")
        details = action.get("details")
        
        timeline.append({
            "timestamp": action.get("timestamp"),
            "agent": agent,
            "event": action_type.replace("_", " ").title(),
            "details": details[:200] if details else None,
        })
    
    # Group consecutive same-agent events into runs
    runs = []
    current_run = None
    
    for event in timeline:
        agent = event["agent"]
        event_type = event["event"]
        
        if current_run is None or current_run["agent"] != agent:
            # End previous run and start new one
            if current_run and len(current_run["events"]) > 0:
                runs.append({
                    "agent": current_run["agent"],
                    "start_time": current_run["events"][0]["timestamp"],
                    "end_time": current_run["events"][-1]["timestamp"],
                    "events": current_run["events"][:5],  # Limit to first 5 events
                })
            current_run = {"agent": agent, "events": [event]}
        else:
            current_run["events"].append(event)
    
    # Don't forget the last run
    if current_run and len(current_run["events"]) > 0:
        runs.append({
            "agent": current_run["agent"],
            "start_time": current_run["events"][0]["timestamp"],
            "end_time": current_run["events"][-1]["timestamp"],
            "events": current_run["events"][:5],
        })
    
    return {
        "timeline": timeline,
        "runs": runs,
        "total_events": len(timeline),
    }


@router.get("/current", response_model=Dict[str, Any])
async def get_current_execution():
    """Get current active execution information."""
    
    task_state = load_current_task_state()
    plan_state = load_planner_state()
    review_state = load_reviewer_state()
    
    # Determine if there's an active execution
    has_active_execution = (
        task_state.get("status") in ("PLANNING", "CODING", "TESTING", "IN_PROGRESS", "RESETTING") or
        plan_state.get("status") in ("PENDING", "PLANNING", "IN_PROGRESS") or
        review_state.get("review_status") in ("REVIEWING", "REQUIRES_CHANGES")
    )
    
    current_task_name = task_state.get("task_name") or plan_state.get("request") or "No active task"
    
    return {
        "has_active_execution": has_active_execution,
        "current_task_name": current_task_name,
        "task_status": task_state.get("status"),
        "plan_id": plan_state.get("plan_id"),
        "review_status": review_state.get("review_status"),
        "last_event": task_state.get("end_time") or plan_state.get("updated_at"),
    }


@router.get("/tasks", response_model=Dict[str, Any])
async def list_tasks():
    """List all tasks from the tasks state directory."""
    
    tasks_dir = "ai_agents/state/tasks"
    if not os.path.exists(tasks_dir):
        return {"tasks": [], "count": 0}
    
    tasks = []
    for filename in os.listdir(tasks_dir):
        if not filename.startswith("task_") or not filename.endswith(".json"):
            continue
        
        task_path = os.path.join(tasks_dir, filename)
        with open(task_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                tasks.append({
                    "id": filename.replace(".json", ""),
                    "title": data.get("title"),
                    "milestone": data.get("milestone"),
                    "status": data.get("status"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                })
            except json.JSONDecodeError:
                continue
    
    # Sort by created_at descending
    tasks.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    
    return {
        "tasks": tasks,
        "count": len(tasks),
    }
