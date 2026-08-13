"""API endpoints for Agent Monitoring Dashboard - Current Activity Stream."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Any as AnyType
from fastapi import APIRouter


router = APIRouter(prefix="/activity", tags=["Activity"])


def _load_orchestrator_state() -> Dict[str, AnyType]:
    """Load orchestrator state."""
    task_path = "ai_agents/state/orchestrator/current_task.json"
    if not os.path.exists(task_path):
        return {}
    
    with open(task_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_planner_state() -> Dict[str, AnyType]:
    """Load planner state."""
    plan_path = "ai_agents/state/planner/current_plan.json"
    if not os.path.exists(plan_path):
        return {}
    
    with open(plan_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_tester_state() -> Dict[str, AnyType]:
    """Load tester agent state."""
    test_path = "ai_agents/state/tester_agent/task_report.json"
    if not os.path.exists(test_path):
        return {}
    
    with open(test_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_reviewer_state() -> Dict[str, AnyType]:
    """Load reviewer agent state."""
    review_path = "ai_agents/state/review_report.json"
    if not os.path.exists(review_path):
        return {}
    
    with open(review_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_coder_state() -> Dict[str, AnyType]:
    """Load coder agent state."""
    coder_path = "ai_agents/state/coder_agent/coding_result.json"
    if not os.path.exists(coder_path):
        return {}
    
    with open(coder_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_vision_state() -> Dict[str, AnyType]:
    """Load vision agent state."""
    vision_path = "ai_agents/state/vision_agent/vision_report.json"
    if not os.path.exists(vision_path):
        return {}
    
    with open(vision_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_debugger_state() -> Dict[str, AnyType]:
    """Load debugger agent state."""
    debugger_path = "ai_agents/state/debugger_agent/debugging_result.json"
    if not os.path.exists(debugger_path):
        return {}
    
    with open(debugger_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _load_test_report_state() -> Dict[str, AnyType]:
    """Load test report state."""
    test_path = "ai_agents/state/test_report.json"
    if not os.path.exists(test_path):
        return {}
    
    with open(test_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


def _safe_get_status(state: Dict[str, AnyType]) -> Optional[str]:
    """Safely get status from state dict."""
    status = state.get("status")
    if isinstance(status, str):
        return status
    return None


def _safe_get_str(state: Dict[str, AnyType], key: str) -> Optional[str]:
    """Safely get string value from state dict."""
    value = state.get(key)
    if isinstance(value, str):
        return value
    return None


@router.get("/stream", response_model=Dict[str, AnyType])
async def get_activity_stream():
    """Get current activity from all agents."""
    
    orchestrator_state = _load_orchestrator_state()
    planner_state = _load_planner_state()
    coder_state = _load_coder_state()
    tester_state = _load_tester_state()
    reviewer_state = _load_reviewer_state()
    vision_state = _load_vision_state()
    debugger_state = _load_debugger_state()
    test_report = _load_test_report_state()
    
    # Build current activity snapshot
    activities: List[Dict[str, AnyType]] = []
    
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
    
    # Test report activity
    if test_report:
        status = _safe_get_str(test_report, "status") or "unknown"
        activities.append({
            "agent": "test_report",
            "event_type": status.lower().replace("_", " "),
            "message": _safe_get_str(test_report, "summary") or f"Test status: {status}",
            "status": status,
            "timestamp": test_report.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        })
    
    return {
        "activities": activities,
        "count": len(activities),
        "has_active_execution": any(
            a["status"] in ("running", "in_progress", "analyzing", "planning")
            for a in activities
        ),
    }


@router.get("/agents", response_model=Dict[str, AnyType])
async def get_active_agents():
    """Get list of currently active agents."""
    
    orchestrator_state = _load_orchestrator_state()
    planner_state = _load_planner_state()
    coder_state = _load_coder_state()
    tester_state = _load_tester_state()
    reviewer_state = _load_reviewer_state()
    
    active_agents: List[Dict[str, AnyType]] = []
    
    status = _safe_get_status(orchestrator_state)
    if status:
        active_agents.append({
            "agent": "orchestrator",
            "status": status,
            "task": _safe_get_str(orchestrator_state, "task_name") or "Processing task",
        })
    
    status = _safe_get_status(planner_state)
    if status:
        active_agents.append({
            "agent": "planner",
            "status": status,
            "task": _safe_get_str(planner_state, "request") or "Planning task",
        })
    
    status = _safe_get_status(coder_state) or "running"
    active_agents.append({
        "agent": "coder_agent",
        "status": status,
        "task": _safe_get_str(coder_state, "summary") or "Implementing task",
    })
    
    status = _safe_get_status(tester_state) or "running"
    active_agents.append({
        "agent": "tester_agent",
        "status": status,
        "task": _safe_get_str(tester_state, "summary") or "Running tests",
    })
    
    review_status = _safe_get_str(reviewer_state, "review_status")
    if review_status:
        active_agents.append({
            "agent": "reviewer_agent",
            "status": review_status,
            "task": _safe_get_str(reviewer_state, "summary") or "Reviewing implementation",
        })
    
    return {
        "active_agents": active_agents,
        "count": len(active_agents),
    }
