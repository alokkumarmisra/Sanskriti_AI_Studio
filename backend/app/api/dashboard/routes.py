"""Agent Monitoring Dashboard API routes."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter


# Define available agents based on existing scripts
AVAILABLE_AGENTS = [
    {"id": "planner_agent", "name": "Planner Agent", "description": "Creates execution plans for development tasks"},
    {"id": "coder_agent", "name": "Coding Agent", "description": "Implements features and code changes"},
    {"id": "tester_agent", "name": "Testing Agent", "description": "Runs unit and integration tests"},
    {"id": "documentation_agent", "name": "Documentation Agent", "description": "Generates and updates project documentation"},
    {"id": "reviewer_agent", "name": "Reviewer Agent", "description": "Reviews implementation quality and compliance"},
    {"id": "debugger_agent", "name": "Debugging Agent", "description": "Analyzes failures and suggests fixes"},
    {"id": "vision_agent", "name": "Vision Agent", "description": "Performs visual analysis of UI screenshots"},
    {"id": "browser_runtime", "name": "Browser Runtime", "description": "Automates browser for testing and screenshots"},
    {"id": "screenshot_service", "name": "Screenshot Service", "description": "Captures UI screenshots with metadata"},
    {"id": "model_router", "name": "Model Router", "description": "Routes vision requests to appropriate models"},
]


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


def _load_state_from_path(path: str) -> Dict[str, Any]:
    """Load JSON state from a path."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_actions_history() -> List[Dict[str, Any]]:
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
    
    actions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return actions[:100]


def _get_orchestrator_state() -> Dict[str, Any]:
    task_path = "ai_agents/state/orchestrator/current_task.json"
    return _load_state_from_path(task_path)


def _get_planner_state() -> Dict[str, Any]:
    plan_path = "ai_agents/state/planner/current_plan.json"
    return _load_state_from_path(plan_path)


def _load_coder_state() -> Dict[str, Any]:
    coder_path = "ai_agents/state/coder_agent/coding_result.json"
    if not os.path.exists(coder_path):
        return {}
    try:
        with open(coder_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_tester_state() -> Dict[str, Any]:
    test_path = "ai_agents/state/tester_agent/task_report.json"
    if not os.path.exists(test_path):
        return {}
    try:
        with open(test_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_reviewer_state() -> Dict[str, Any]:
    review_path = "ai_agents/state/review_report.json"
    if not os.path.exists(review_path):
        return {}
    try:
        with open(review_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _get_orchestrator_logs() -> str:
    log_path = "ai_agents/logs/orchestrator/execution.log"
    if not os.path.exists(log_path):
        return ""
    with open(log_path, "r", encoding="utf-8") as f:
        return f.read()


def _safe_get_status(state: Dict[str, Any]) -> Optional[str]:
    """Safely get status from state dict."""
    status = state.get("status")
    if isinstance(status, str):
        return status
    return None


def _safe_get_str(state: Dict[str, Any], key: str) -> Optional[str]:
    """Safely get string value from state dict."""
    value = state.get(key)
    if isinstance(value, str):
        return value
    return None


@router.get("/agents", response_model=Dict[str, Any])
async def list_agents(
    include_details: bool = False,
):
    """List all available agents with their current status."""
    
    # For now, return empty list - actual state loading to be implemented
    agent_list = []
    
    return {
        "agents": agent_list,
        "count": len(agent_list),
        "total_available": len(AVAILABLE_AGENTS),
    }


@router.get("/activity/stream", response_model=Dict[str, Any])
async def get_activity_stream():
    """Get current activity from all agents."""
    
    orchestrator_state = _get_orchestrator_state()
    planner_state = _get_planner_state()
    coder_state = _load_coder_state()
    tester_state = _load_tester_state()
    reviewer_state = _load_reviewer_state()
    
    activities: List[Dict[str, Any]] = []
    
    # Orchestrator activity
    status = _safe_get_status(orchestrator_state)
    if status:
        activities.append({
            "agent": "orchestrator",
            "event_type": status.lower().replace("_", " "),
            "message": _safe_get_str(orchestrator_state, "task_name") or "Processing task",
            "status": status,
            "timestamp": orchestrator_state.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        })
    
    # Planner activity
    status = _safe_get_status(planner_state)
    if status:
        activities.append({
            "agent": "planner",
            "event_type": status.lower().replace("_", " "),
            "message": _safe_get_str(planner_state, "request") or "Planning task",
            "status": status,
            "timestamp": planner_state.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        })
    
    # Coder activity
    status = _safe_get_status(coder_state) or "running"
    activities.append({
        "agent": "coder_agent",
        "event_type": status,
        "message": _safe_get_str(coder_state, "summary") or "Implementing task",
        "status": status,
        "timestamp": coder_state.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    })
    
    # Tester activity
    status = _safe_get_status(tester_state) or "running"
    activities.append({
        "agent": "tester_agent",
        "event_type": status,
        "message": _safe_get_str(tester_state, "summary") or "Running tests",
        "status": status,
        "timestamp": tester_state.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    })
    
    # Reviewer activity
    review_status = _safe_get_str(reviewer_state, "review_status")
    if review_status:
        activities.append({
            "agent": "reviewer_agent",
            "event_type": review_status.lower().replace("_", " ").title(),
            "message": _safe_get_str(reviewer_state, "summary") or "Reviewing implementation",
            "status": review_status,
            "timestamp": reviewer_state.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        })
    
    return {
        "activities": activities,
        "count": len(activities),
        "has_active_execution": any(
            a["status"] in ("running", "in_progress", "analyzing", "planning")
            for a in activities
        ),
    }


@router.get("/history", response_model=Dict[str, Any])
async def get_execution_history(limit: int = 100):
    """Get recent execution events from actions history."""
    
    actions = _load_actions_history()[:limit]
    
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
    
    return {
        "timeline": timeline,
        "total_events": len(timeline),
    }


@router.get("/logs/orchestrator", response_model=Dict[str, Any])
async def get_orchestrator_logs(
    limit: int = 500,
    filter_level: Optional[str] = None,
):
    """Get orchestrator agent logs."""
    
    raw_logs = _get_orchestrator_logs()
    
    if not raw_logs:
        return {
            "agent": "orchestrator",
            "logs": [],
            "count": 0,
        }
    
    filtered_lines = []
    for line in raw_logs.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if filter_level and filter_level.upper() != "ALL":
            if f"[{filter_level.upper()}]" not in line:
                continue
        
        filtered_lines.append(line)
    
    return {
        "agent": "orchestrator",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/orchestrator/execution.log",
    }
