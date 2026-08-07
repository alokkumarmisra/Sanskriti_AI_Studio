#!/usr/bin/env python3
"""
Debugging Agent Runtime for Sanskriti AI Studio.

This runtime analyzes failures produced by the Testing Agent or other execution agents
and determines:
1. What failed
2. Why it failed
3. The probable root cause
4. Which files or components are affected
5. What should be changed
6. Which agent should perform the fix
7. How the fix should be validated

CRITICAL: Qwen 3.5 is TEXT-ONLY. This runtime never sends images or visual data.

Version: 1.0
Last Updated: 2026-07-30
"""

import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import LM Studio client for chat completions
from lmstudio_client import chat_with_coding_model


# --- Configuration ---------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
DEBUGGER_STATE_DIR = os.path.join(STATE_DIR, "debugger")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
DEBUGGER_LOGS_DIR = os.path.join(LOGS_DIR, "debugger")

# Maximum debugging retries before escalation
MAX_DEBUG_RETRIES = 3


# --- State Management Functions --------------------------------------------

def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_debugging_request_id() -> str:
    """Generate a unique debugging request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return f"DEBUG-{timestamp}-{unique_id}"


def safe_rel_path(path: str) -> Optional[str]:
    """Normalize workspace-relative path and reject unsafe paths."""
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return None
    absolute = os.path.abspath(os.path.join(WORKSPACE_ROOT, normalized))
    workspace = os.path.abspath(WORKSPACE_ROOT)
    if not absolute.startswith(workspace):
        return None
    relative_to_workspace = os.path.relpath(absolute, workspace).replace("\\", "/")
    if relative_to_workspace.startswith(".."):
        return None
    return relative_to_workspace


# --- Failure Classification Functions --------------------------------------

def classify_failure_type(error_message: str, stack_trace: Optional[str] = None) -> str:
    """Classify the type of failure based on error message and stack trace.
    
    Returns one of: test_failure, api_error, database_error, import_error, 
                     lint_failure, syntax_error, security_error, network_error,
                     memory_error, permission_error, config_error, dependency_error,
                     environment_error, runtime_error, unknown_error
    """
    error_lower = error_message.lower() if error_message else ""
    
    # Test failures - AssertionError, pytest-specific errors
    if any(pattern in error_lower for pattern in [
        "assertionerror", "pytest.fail", "expected.*but got", "assert ",
        "assert False"
    ]):
        return "test_failure"
    
    # API errors - HTTP status codes, endpoint calls
    if any(pattern in error_lower for pattern in [
        "http 500", "http 502", "http 503", "internal server error",
        "bad gateway", "service unavailable", "get /api", "post /api",
        "/api/"
    ]):
        return "api_error"
    
    # Database errors - connection, query, corruption issues
    if any(pattern in error_lower for pattern in [
        "could not connect", "connection refused", "database", "sql",
        "postgres", "mysql", "sqlite", "corrupt", "foreign key", "primary key"
    ]):
        return "database_error"
    
    # Import errors - missing modules
    if any(pattern in error_lower for pattern in [
        "importerror", "moduleNotFoundError", "no module named",
        "could not import"
    ]):
        return "import_error"
    
    # Linting errors
    if any(pattern in error_lower for pattern in [
        "eslint", "linting", "unused variable", "deprecated",
        "warning:", "'useless-constructor'"
    ]):
        return "lint_failure"
    
    # Syntax errors
    if any(pattern in error_lower for pattern in [
        "syntaxerror", "invalid syntax", "unexpected token", "missing )"
    ]):
        return "syntax_error"
    
    # Security issues
    if any(pattern in error_lower for pattern in [
        "injection", "vulnerability", "unauthorized", "forbidden",
        "csrf", "xss", "security"
    ]):
        return "security_error"
    
    # Network errors  
    if any(pattern in error_lower for pattern in [
        "connection timeout", "network is unreachable", "dns failed",
        "socket", "network error", "timed out"
    ]):
        return "network_error"
    
    # Memory errors
    if any(pattern in error_lower for pattern in [
        "memoryerror", "allocation failed", "out of memory", "segfault"
    ]):
        return "memory_error"
    
    # Permission errors
    if any(pattern in error_lower for pattern in [
        "permission denied", "access denied", "no permission", "403 forbidden"
    ]):
        return "permission_error"
    
    # Configuration errors
    if any(pattern in error_lower for pattern in [
        "config", "configuration", "invalid config", "yaml", "toml", "ini",
        "environment variable not set"
    ]):
        return "config_error"
    
    # Dependency errors - missing packages
    if any(pattern in error_lower for pattern in [
        "package not found", "dependency", "pip", "requirements", 
        "version conflict", "incompatible"
    ]):
        return "dependency_error"
    
    # Environment errors
    if any(pattern in error_lower for pattern in [
        "environment variable", "not set", "env", "docker", "container",
        "path not found", "working directory"
    ]):
        return "environment_error"
    
    # Runtime errors
    if any(pattern in error_lower for pattern in [
        "runtimeerror", "traceback", "stack trace", "exception"
    ]):
        return "runtime_error"
    
    return "unknown_error"


def detect_severity(failure_type: str, error_message: str) -> str:
    """Detect the severity of a failure based on type and message.
    
    Returns: critical, high, medium, low
    """
    if failure_type == "database_error":
        if any(pattern in error_message.lower() for pattern in [
            "corruption", "data loss", "critical", "immediate"
        ]):
            return "critical"
        return "high"
    
    elif failure_type == "api_error":
        status_match = re.search(r'HTTP (\d+)', error_message)
        if status_match and int(status_match.group(1)) >= 500:
            return "high"
        return "medium"
    
    elif failure_type == "test_failure":
        # Test failures are medium - they indicate bugs but don't break the system
        return "medium"
    
    elif failure_type in ["import_error", "dependency_error", "config_error"]:
        return "high"
    
    elif failure_type in ["lint_failure", "syntax_error"]:
        return "low"
    
    elif failure_type == "network_error":
        # Network errors can be transient
        if "timeout" in error_message.lower() or "unreachable" in error_message.lower():
            return "medium"
        return "high"
    
    elif failure_type in ["security_error", "permission_error"]:
        return "critical"
    
    elif failure_type in ["memory_error", "database_error"]:
        return "critical"
    
    else:
        return "medium"


def extract_root_cause(error_message: str, stack_trace: Optional[str] = None) -> Dict[str, Any]:
    """Extract root cause information from error message.
    
    Returns a dict with: description, confidence, suggested_fix, related_files
    """
    result = {
        "description": "",
        "confidence": "medium",
        "suggested_fix": "",
        "related_files": []
    }
    
    if not error_message:
        return result
    
    # Try to extract meaningful information from the error message
    # Database connection issues
    if "database" in error_message.lower() or "postgres" in error_message.lower():
        result["description"] = "Database connectivity issue detected"
        result["confidence"] = "high"
        result["suggested_fix"] = "Check database connection string, verify service is running"
    
    # Import errors
    elif "importerror" in error_message.lower() or "module not found" in error_message.lower():
        match = re.search(r"No module named ['\"]?(\w+)", error_message, re.IGNORECASE)
        if match:
            missing_module = match.group(1)
            result["description"] = f"Missing Python module: {missing_module}"
            result["confidence"] = "high"
            result["suggested_fix"] = f"Install package using pip install {missing_module}"
    
    # HTTP/API errors
    elif "http" in error_message.lower():
        status_match = re.search(r'HTTP (\d+)', error_message)
        if status_match:
            status_code = int(status_match.group(1))
            result["description"] = f"HTTP {status_code} error from API endpoint"
            if status_code == 500:
                result["suggested_fix"] = "Check backend service logs for application errors"
            elif status_code == 404:
                result["suggested_fix"] = "Verify resource path exists, check routing configuration"
            elif status_code == 403:
                result["suggested_fix"] = "Review authentication/authorization requirements"
        else:
            result["description"] = "HTTP request failed"
    
    # Network errors
    elif "network" in error_message.lower() or "timeout" in error_message.lower():
        result["description"] = "Network connectivity issue detected"
        result["suggested_fix"] = "Check network connection, DNS resolution, firewall settings"
    
    # Permission issues
    elif "permission" in error_message.lower():
        result["description"] = "Permission/access denied error"
        result["suggested_fix"] = "Review file/directory permissions and user authorization"
    
    # Configuration errors  
    elif "config" in error_message.lower() or "configuration" in error_message.lower():
        result["description"] = "Configuration error detected"
        result["suggested_fix"] = "Verify configuration files, check environment variables"
    
    # Syntax errors
    elif "syntaxerror" in error_message.lower():
        result["description"] = "Syntax error in code"
        result["suggested_fix"] = "Review code for syntax issues, proper brackets and delimiters"
    
    # General fallback
    else:
        result["description"] = error_message.strip()[:200]
    
    # Extract file paths from stack trace if provided
    if stack_trace:
        file_patterns = [
            r'File ["\']?([^"\']+)["\']?',
            r'\s*in\s+([^\s]+)\.py',
            r'at\s+(?:line\s+(\d+))?\s*(?:of\s+.+)?(?:file\s*[\'"]([^"\']+)[\'"]?)?'
        ]
        for pattern in file_patterns:
            matches = re.findall(pattern, stack_trace)
            for match in matches:
                if isinstance(match, tuple):
                    file_path = match[0] or match[1]
                else:
                    file_path = match
                if file_path and not any(x in str(file_path) for x in ["__pycache__", ".pyc"]):
                    result["related_files"].append(safe_rel_path(file_path))
    
    return result


def analyze_affected_files(error_message: str, stack_trace: Optional[str] = None) -> Dict[str, List[str]]:
    """Analyze stack trace to identify affected files.
    
    Returns dict with likely_affected and possibly_affected file lists.
    """
    result = {
        "likely_affected": [],
        "possibly_affected": []
    }
    
    if not stack_trace:
        return result
    
    # Extract file paths from common stack trace formats
    file_matches = re.findall(
        r'(?:File|at)\s*[\'"]?([^\'"\s]+)[\'"]?(?:\.py)?(?:\s*#line\s*(\d+))?(\s|$)',
        stack_trace
    )
    
    seen_files = set()
    for match in file_matches:
        if isinstance(match, tuple):
            file_path = match[0] or ""
            line_num = match[1] if len(match) > 1 else None
        else:
            file_path = match
            line_num = None
        
        if file_path:
            normalized = safe_rel_path(file_path)
            if normalized and normalized not in seen_files:
                seen_files.add(normalized)
                result["likely_affected"].append(normalized)
    
    # Also check for import statements that might indicate affected files
    import_matches = re.findall(r'from\s+([^\s]+)\s+import', stack_trace)
    for module in import_matches:
        if module and not module.startswith(("os", "sys", "json", "re", "datetime", "typing", "unittest")):
            result["possibly_affected"].append(f"import/{module}")
    
    return result


def build_fix_plan(
    failure_type: str,
    root_cause: Dict[str, Any],
    affected_files: List[str],
    task_id: str
) -> List[Dict[str, Any]]:
    """Build a fix plan based on failure type and root cause.
    
    Returns list of fix tasks with agent assignments and validation steps.
    """
    fix_tasks = []
    
    if failure_type == "test_failure":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "re-run tests",
            "assigned_agent": "testing_agent",
            "validation_step": "verify all related tests pass"
        })
        
    elif failure_type in ["api_error", "runtime_error"]:
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "review backend code",
            "assigned_agent": "coder_agent",
            "validation_step": "verify API endpoint responds correctly"
        })
        
    elif failure_type == "database_error":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "check database connectivity and schema",
            "assigned_agent": "coder_agent",
            "validation_step": "run database health check queries"
        })
        
    elif failure_type == "import_error":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "install missing dependencies",
            "assigned_agent": "setup_agent",
            "validation_step": "verify all imports work correctly"
        })
        
    elif failure_type == "syntax_error":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "fix syntax errors in affected files",
            "assigned_agent": "coder_agent",
            "validation_step": "run linting and type checking"
        })
        
    elif failure_type == "config_error":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "update configuration files",
            "assigned_agent": "config_agent",
            "validation_step": "verify configuration is valid and applied"
        })
        
    elif failure_type == "network_error":
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "check network connectivity and DNS",
            "assigned_agent": "infrastructure_agent",
            "validation_step": "verify external endpoints are reachable"
        })
    
    else:
        fix_tasks.append({
            "task_id": f"{task_id}-FIX-001",
            "action": "investigate error and create fix plan",
            "assigned_agent": "coder_agent",
            "validation_step": "run tests after fix is applied"
        })
    
    # Add specific fixes for affected files if any are provided
    for file_path in affected_files[:3]:  # Limit to top 3 files
        if file_path not in [t.get("assigned_agent") for t in fix_tasks if isinstance(t.get("assigned_agent"), str)]:
            continue
        
    return fix_tasks


def process_debugging_request(
    input_data: Dict[str, Any],
    retry_count: int = 0
) -> Dict[str, Any]:
    """Process a debugging request and return analysis results.
    
    Args:
        input_data: Contains failure_type, error_message, stack_trace, etc.
        retry_count: Current retry attempt number
    
    Returns dict with diagnosis_complete, severity, root_cause, affected_files, fix_plan, escalation_required, retry_limit_reached
    """
    result = {
        "diagnosis_complete": True,
        "severity": "medium",
        "root_cause": {},
        "affected_files": [],
        "fix_plan": [],
        "retry_count": retry_count,
        "escalation_required": False,
        "retry_limit_reached": False,
        "escalation_reason": "",
    }
    
    # Extract input data
    failure_type = input_data.get("failure_type", "unknown_error")
    error_message = input_data.get("error_message", "")
    stack_trace = input_data.get("stack_trace", "")
    
    # Classify failure type if not provided
    if not failure_type or failure_type == "unknown_error":
        result["failure_classification"] = classify_failure_type(error_message, stack_trace)
        failure_type = result["failure_classification"]
    
    # Detect severity
    result["severity"] = detect_severity(failure_type, error_message)
    
    # Extract root cause
    root_cause_data = extract_root_cause(error_message, stack_trace)
    result["root_cause"] = root_cause_data
    
    # Analyze affected files
    file_analysis = analyze_affected_files(error_message, stack_trace)
    result["affected_files"] = file_analysis.get("likely_affected", []) + file_analysis.get("possibly_affected", [])
    
    # Build fix plan
    fix_plan = build_fix_plan(
        failure_type=failure_type,
        root_cause=root_cause_data,
        affected_files=result["affected_files"],
        task_id=input_data.get("task_id", "UNKNOWN")
    )
    result["fix_plan"] = fix_plan
    
    # Check retry limits and escalation
    if retry_count >= MAX_DEBUG_RETRIES:
        result["escalation_required"] = True
        result["retry_limit_reached"] = True
        result["escalation_reason"] = "Retry limit reached for this debugging request"
    
    return result


if __name__ == "__main__":
    print("Debugging Agent module loaded successfully.")
    print(f"Importing from lmstudio_client works correctly!")
