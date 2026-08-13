"""API endpoints for Agent Monitoring Dashboard - Log Viewer."""

import os
from typing import Optional, Dict, Any, List
from enum import StrEnum
from fastapi import APIRouter, Query


router = APIRouter(prefix="/logs", tags=["Logs"])


def read_log_file(path: str) -> str:
    """Read a log file from disk."""
    
    if not os.path.exists(path):
        return ""
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_orchestrator_logs() -> str:
    """Get orchestrator execution logs (helper)."""
    log_path = "ai_agents/logs/orchestrator/execution.log"
    return read_log_file(log_path)


def _get_planner_logs() -> str:
    """Get planner execution logs (helper)."""
    log_path = "ai_agents/logs/planner/execution.log"
    return read_log_file(log_path)


def _get_coder_logs() -> str:
    """Get coder agent logs (helper)."""
    log_path = "ai_agents/logs/coder_agent/execution.log"
    return read_log_file(log_path)


def _get_tester_logs() -> str:
    """Get tester agent logs (helper)."""
    log_path = "ai_agents/logs/tester_agent/execution.log"
    return read_log_file(log_path)


def _get_reviewer_logs() -> str:
    """Get reviewer agent logs (helper)."""
    log_path = "ai_agents/logs/reviewer_agent/execution.log"
    return read_log_file(log_path)


def _get_vision_logs() -> str:
    """Get vision agent logs (helper)."""
    log_path = "ai_agents/logs/vision_agent/execution.log"
    return read_log_file(log_path)


def _get_debugger_logs() -> str:
    """Get debugger agent logs (helper)."""
    log_path = "ai_agents/logs/debugger_agent/execution.log"
    return read_log_file(log_path)


class LogFilter(StrEnum):
    """Log level filter."""
    ALL = "all"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _filter_logs(raw_logs: str, filter_level: Optional[LogFilter]) -> List[str]:
    """Filter log lines by level if specified."""
    filtered_lines = []
    for line in raw_logs.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if filter_level and filter_level != LogFilter.ALL:
            if f"[{filter_level.upper()}]" not in line:
                continue
        filtered_lines.append(line)
    return filtered_lines


@router.get("/orchestrator", response_model=dict)
async def get_orchestrator_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get orchestrator agent logs."""
    
    raw_logs = _get_orchestrator_logs()
    
    if not raw_logs:
        return {
            "agent": "orchestrator",
            "logs": [],
            "count": 0,
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "orchestrator",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/orchestrator/execution.log",
    }


@router.get("/planner", response_model=dict)
async def get_planner_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get planner agent logs."""
    
    raw_logs = _get_planner_logs()
    
    if not raw_logs:
        return {
            "agent": "planner",
            "logs": [],
            "count": 0,
            "note": "Planner logs are typically minimal - see orchestrator for coordinated events",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "planner",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/planner/execution.log",
    }


@router.get("/coder_agent", response_model=dict)
async def get_coder_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get coder agent logs."""
    
    raw_logs = _get_coder_logs()
    
    if not raw_logs:
        return {
            "agent": "coder_agent",
            "logs": [],
            "count": 0,
            "note": "Coder agent output is typically in state files (coding_result.json)",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "coder_agent",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/coder_agent/execution.log",
    }


@router.get("/tester_agent", response_model=dict)
async def get_tester_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get tester agent logs."""
    
    raw_logs = _get_tester_logs()
    
    if not raw_logs:
        return {
            "agent": "tester_agent",
            "logs": [],
            "count": 0,
            "note": "Tester agent output is typically in state files (test_report.json)",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "tester_agent",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/tester_agent/execution.log",
    }


@router.get("/reviewer_agent", response_model=dict)
async def get_reviewer_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get reviewer agent logs."""
    
    raw_logs = _get_reviewer_logs()
    
    if not raw_logs:
        return {
            "agent": "reviewer_agent",
            "logs": [],
            "count": 0,
            "note": "Reviewer agent output is typically in state files (review_report.json)",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "reviewer_agent",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/reviewer_agent/execution.log",
    }


@router.get("/vision_agent", response_model=dict)
async def get_vision_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get vision agent logs."""
    
    raw_logs = _get_vision_logs()
    
    if not raw_logs:
        return {
            "agent": "vision_agent",
            "logs": [],
            "count": 0,
            "note": "Vision agent output is typically in state files (vision_report.json)",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "vision_agent",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/vision_agent/execution.log",
    }


@router.get("/debugger_agent", response_model=dict)
async def get_debugger_logs(
    limit: int = 500,
    filter_level: Optional[LogFilter] = Query(default=None),
):
    """Get debugger agent logs."""
    
    raw_logs = _get_debugger_logs()
    
    if not raw_logs:
        return {
            "agent": "debugger_agent",
            "logs": [],
            "count": 0,
            "note": "Debugger agent output is typically in state files (debugging_report.json)",
        }
    
    filtered_lines = _filter_logs(raw_logs, filter_level)
    
    return {
        "agent": "debugger_agent",
        "logs": filtered_lines[:limit],
        "count": len(filtered_lines),
        "path": "ai_agents/logs/debugger_agent/execution.log",
    }


@router.get("/all", response_model=Dict[str, Any])
async def get_all_logs():
    """Get logs for all agents at once."""
    
    return {
        "orchestrator": {
            "count": len(_get_orchestrator_logs().split("\n")),
            "path": "ai_agents/logs/orchestrator/execution.log",
        },
        "planner": {
            "count": len(_get_planner_logs().split("\n")),
            "path": "ai_agents/logs/planner/execution.log",
        },
        "coder_agent": {
            "count": len(_get_coder_logs().split("\n")),
            "path": "ai_agents/logs/coder_agent/execution.log",
        },
        "tester_agent": {
            "count": len(_get_tester_logs().split("\n")),
            "path": "ai_agents/logs/tester_agent/execution.log",
        },
        "reviewer_agent": {
            "count": len(_get_reviewer_logs().split("\n")),
            "path": "ai_agents/logs/reviewer_agent/execution.log",
        },
        "vision_agent": {
            "count": len(_get_vision_logs().split("\n")),
            "path": "ai_agents/logs/vision_agent/execution.log",
        },
        "debugger_agent": {
            "count": len(_get_debugger_logs().split("\n")),
            "path": "ai_agents/logs/debugger_agent/execution.log",
        },
    }
