"""API endpoints for Agent Monitoring Dashboard - Agent Status."""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import StrEnum
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict


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


class AgentStatus(StrEnum):
    """Agent status enumeration."""
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class AgentListItem(BaseModel):
    """Compact agent info for listing."""
    id: str
    name: str
    description: str
    status: AgentStatus
    current_task: Optional[str]
    started_at: Optional[str]
    elapsed_seconds: int


class AgentDetailItem(BaseModel):
    """Detailed agent information."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    description: str
    status: AgentStatus
    current_task: Optional[str]
    current_operation: Optional[str]
    start_time: Optional[str]
    completion_time: Optional[str]
    retry_count: int
    last_error: Optional[str]
    progress: int


router = APIRouter(prefix="/agents", tags=["Agents"])


def load_agent_state(agent_id: str) -> Dict[str, Any]:
    """Load agent state from ai_agents/state directory."""
    
    # Check various possible state files
    possible_specs = [
        {"file": f"planner/current_plan.json", "match_ids": ["planner_agent"]},
        {"file": "orchestrator/current_task.json", "match_ids": ["coder_agent", "tester_agent"]},
        {"file": "current_task.json", "match_ids": []},  # fallback
    ]
    
    for spec in possible_specs:
        file_spec = spec["file"]
        match_ids = spec["match_ids"]
        
        if not os.path.exists(file_spec):
            continue
        
        full_path = file_spec
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check if this agent matches the state
        agent_matches = agent_id in match_ids or any(mid in agent_id for mid in match_ids)
        if not agent_matches and file_spec != f"current_task.json":
            continue
        
        start_time = data.get("start_time") or data.get("created_at") or None
        end_time = data.get("end_time") or data.get("updated_at") or None
        
        retry_count = data.get("retry_count", 0) or 0
        current_task = data.get("request") or data.get("task_name") or data.get("title")
        current_operation = data.get("objective") or data.get("description") or None
        progress = data.get("progress", 0) or 0
        
        return {
            "id": agent_id,
            "name": AVAILABLE_AGENTS[0]["name"],  # Default name
            "description": AVAILABLE_AGENTS[0]["description"],  # Default description
            "status": data.get("status") or AgentStatus.IDLE.value,
            "current_task": current_task,
            "current_operation": current_operation[:200] if current_operation else None,
            "start_time": start_time,
            "completion_time": end_time,
            "retry_count": retry_count,
            "last_error": data.get("error") or (data.get("errors", [{}])[-1]["error"] if isinstance(data.get("errors"), list) else None),
            "progress": progress,
        }
    
    # Return default for agents without state file
    return {
        "id": agent_id,
        "name": AVAILABLE_AGENTS[0]["name"],
        "description": AVAILABLE_AGENTS[0]["description"],
        "status": AgentStatus.IDLE.value,
        "current_task": None,
        "current_operation": None,
        "start_time": None,
        "completion_time": None,
        "retry_count": 0,
        "last_error": None,
        "progress": 0,
    }


@router.get("", response_model=Dict[str, Any])
async def list_agents(
    include_details: bool = False,
):
    """List all available agents with their current status."""
    
    agent_list = []
    now = datetime.now(timezone.utc)
    
    for agent_info in AVAILABLE_AGENTS:
        agent_id = agent_info["id"]
        state = load_agent_state(agent_id)
        
        elapsed_seconds = 0
        if state["start_time"]:
            try:
                start_dt = datetime.fromisoformat(state["start_time"])
                elapsed_seconds = int((now - start_dt).total_seconds())
            except:
                pass
        
        item_data = {
            "id": state["id"],
            "name": state["name"],
            "description": state["description"],
            "status": state["status"],
            "current_task": state.get("current_task"),
            "started_at": state.get("start_time"),
            "elapsed_seconds": elapsed_seconds,
        }
        
        if include_details:
            item_data.update({
                "completion_time": state.get("completion_time"),
                "retry_count": state.get("retry_count", 0),
                "last_error": state.get("last_error"),
                "progress": state.get("progress", 0),
            })
        
        agent_list.append(item_data)
    
    return {
        "agents": agent_list,
        "count": len(agent_list),
        "total_available": len(AVAILABLE_AGENTS),
    }


@router.get("/{agent_id}", response_model=AgentDetailItem)
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent."""
    
    state = load_agent_state(agent_id)
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    elapsed_seconds = 0
    
    if state["start_time"]:
        try:
            start_dt = datetime.fromisoformat(state["start_time"])
            elapsed_seconds = int((now - start_dt).total_seconds())
        except:
            pass
    
    return AgentDetailItem(
        id=state["id"],
        name=state["name"],
        description=state["description"],
        status=AgentStatus(state["status"]),
        current_task=state.get("current_task"),
        current_operation=state.get("current_operation"),
        start_time=state.get("start_time"),
        completion_time=state.get("completion_time"),
        retry_count=int(state.get("retry_count") or 0),
        last_error=state.get("last_error"),
        progress=int(state.get("progress") or 0),
    )
