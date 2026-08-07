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

from ai_agents.scripts import lmstudio_client


def chat_with_coding_model(messages: List[Dict[str, str]], **config) -> Dict[str, Any]:
    """Call LM Studio with Qwen 3.5 model using provided configuration."""
    base_url = config.get('base_url', os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1'))
    model = config.get('model', '')
    
    client = lmstudio_client.LMStudioClient()
    client._base_url = base_url
    if model:
        client._model = model
    
    return client.chat(messages=messages)


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
    return normalized


def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON object from disk, returning None when unavailable/invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            data.setdefault("_source", path)
            return data
        return {"value": data, "_source": path}
    except Exception:
        return None


def load_text_file(path: str, limit: int = 20000) -> str:
    """Load text file with a character limit."""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read(limit)
    except Exception:
        return ""


def log_event(message: str) -> None:
    """Append a timestamped event to the debugger execution log."""
    os.makedirs(DEBUGGER_LOGS_DIR, exist_ok=True)
    timestamp = utc_now()
    log_entry = f"[{timestamp}] [DEBUGGER] {message}\n"
    with open(os.path.join(DEBUGGER_LOGS_DIR, "execution.log"), "a", encoding="utf-8") as f:
        f.write(log_entry)


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append an action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "debugger",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(os.path.join(STATE_DIR, "actions.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_debugger_state() -> Dict[str, Any]:
    """Load current debugger task state."""
    state_path = os.path.join(DEBUGGER_STATE_DIR, "current_debug.json")
    return load_json_file(state_path) or {
        "debugging_request_id": None,
        "original_user_request": None,
        "plan_id": None,
        "task_id": None,
        "failure_source": None,
        "failure_type": None,
        "error_message": "",
        "stack_trace": "",
        "command_executed": "",
        "exit_code": None,
        "test_name": None,
        "affected_files": [],
        "retry_count": 0,
        "max_retries": MAX_DEBUG_RETRIES,
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
        "diagnosis_complete": False,
        "fix_plan_generated": False,
        "coding_agent_assigned": False,
        "escalation_required": False,
        "errors": [],
        "warnings": [],
    }


def save_debugger_state(state: Dict[str, Any]) -> None:
    """Persist debugger task state."""
    os.makedirs(DEBUGGER_STATE_DIR, exist_ok=True)
    with open(os.path.join(DEBUGGER_STATE_DIR, "current_debug.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# --- Failure Classification ------------------------------------------------

FAILURE_TYPES = [
    "syntax_error",
    "type_error",
    "import_error",
    "dependency_error",
    "configuration_error",
    "environment_error",
    "database_error",
    "api_error",
    "frontend_error",
    "backend_error",
    "runtime_error",
    "test_failure",
    "integration_test_failure",
    "build_failure",
    "lint_failure",
    "migration_error",
    "authentication_error",
    "authorization_error",
    "network_error",
    "file_system_error",
    "unknown_error",
]


def classify_failure_type(error_message: str, stack_trace: Optional[str] = None) -> str:
    """Classify the failure type from error messages and stack traces."""
    text_lower = (error_message + " " + (stack_trace or "")).lower()
    
    # Test failures
    if any(kw in text_lower for kw in ["assertionerror", "expected", "failed"]):
        if "integration" in text_lower:
            return "integration_test_failure"
        return "test_failure"
    
    # Build failures
    if any(kw in text_lower for kw in ["compilation error", "build failed", "cannot resolve", 
                                         "module not found", "no such file"]):
        return "build_failure"
    
    # Lint failures
    if any(kw in text_lower for kw in ["eslint", "warning", "fixable", "prettier"]):
        return "lint_failure"
    
    # Database errors
    if any(kw in text_lower for kw in ["sqlite", "postgres", "mysql", "connection refused", 
                                         "could not connect", "database does not exist"]):
        return "database_error"
    
    # Migration errors
    if any(kw in text_lower for kw in ["alembic", "migration", "reverting", "autogenerate"]):
        return "migration_error"
    
    # Import/Dependency errors
    if any(kw in text_lower for kw in ["module not found", "no module named", 
                                         "import error", "dependency"]):
        return "import_error"
    
    # API/HTTP errors
    if any(kw in text_lower for kw in ["http", "status code", "500", "404", "401", "403",
                                         "cors", "unauthorized", "forbidden"]):
        return "api_error"
    
    # Network errors
    if any(kw in text_lower for kw in ["connection refused", "timeout", "network error",
                                         "could not resolve", "dns"]):
        return "network_error"
    
    # File system errors
    if any(kw in text_lower for kw in ["cannot write", "permission denied", "no space left",
                                         "file not found", "directory does not exist"]):
        return "file_system_error"
    
    # Configuration/Environment errors
    if any(kw in text_lower for kw in ["environment variable", "config", ".env", 
                                         "configuration", "invalid config", "missing env"]):
        return "configuration_error"
    
    # Environment setup errors
    if any(kw in text_lower for kw in ["pip", "node", "npm install", "package not installed"]):
        return "environment_error"
    
    # Authentication/Authorization
    if any(kw in text_lower for kw in ["unauthorized", "forbidden", "invalid token",
                                         "authentication failed"]):
        if "token" in text_lower or "auth" in text_lower:
            return "authentication_error"
        return "authorization_error"
    
    # Runtime errors (catch-all for exceptions)
    if any(kw in text_lower for kw in ["exception", "error:", "traceback"]):
        return "runtime_error"
    
    # Frontend/Backend specific
    if "frontend" in text_lower or "react" in text_lower:
        return "frontend_error"
    if "backend" in text_lower or "fastapi" in text_lower:
        return "backend_error"
    
    # Type errors
    if any(kw in text_lower for kw in ["type error", "typescript", "undefined is not a",
                                         "cannot read property"]):
        return "type_error"
    
    # Syntax errors
    if any(kw in text_lower for kw in ["syntax error", "invalid syntax", "parse error"]):
        return "syntax_error"
    
    # Default to unknown
    return "unknown_error"


def detect_severity(failure_type: str, error_message: str) -> str:
    """Detect severity level based on failure characteristics."""
    text_lower = error_message.lower()
    
    # Critical - application cannot function or data at risk
    if any(p in text_lower for p in ["database does not exist", "corruption", "data loss", 
                                      "dropping database", "delete table"]):
        return "critical"
    
    # High - core functionality broken but data safe
    if any(p in text_lower for p in ["500 error", "internal server error", "build failed", 
                                      "cannot connect to database", "authentication failed"]):
        return "high"
    
    # Medium - specific feature broken, application works
    if failure_type in ["test_failure", "type_error", "api_error"]:
        return "medium"
    
    # Low - cosmetic or minor issues
    if any(p in text_lower for p in ["warning", "style", "formatting", "lint"]):
        return "low"
    
    return "medium"  # Default severity


def extract_root_cause(error_message: str, stack_trace: Optional[str] = None) -> Dict[str, Any]:
    """Extract root cause analysis from error messages and stack traces."""
    text_lower = (error_message + " " + (stack_trace or "")).lower()
    
    if any(kw in text_lower for kw in ["database does not exist", "cannot connect to"]):
        root_cause = {
            "description": "Database connection configuration is incorrect or database is missing.",
            "confidence": "high" if "does not exist" in text_lower else "medium",
        }
    elif any(kw in text_lower for kw in ["module not found", "no module named"]):
        root_cause = {
            "description": "Python package is not installed or import path is incorrect.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["http 500", "internal server error"]):
        root_cause = {
            "description": "Backend API endpoint has an unhandled exception or logic error.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["assertionerror", "expected"]):
        root_cause = {
            "description": "Test assertion failed - actual output does not match expected output.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["compilation error", "cannot resolve"]) and "lint" not in text_lower:
        root_cause = {
            "description": "TypeScript/Python compilation or build process has errors.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["cors enabled"]):
        root_cause = {
            "description": "CORS middleware configuration does not allow frontend origin.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["unauthorized", "401", "invalid token"]):
        root_cause = {
            "description": "Request authentication is missing or using invalid credentials.",
            "confidence": "high",
        }
    elif any(kw in text_lower for kw in ["permission denied"]):
        root_cause = {
            "description": "File system permissions prevent required operation.",
            "confidence": "high",
        }
    else:
        # Generic fallback analysis
        if stack_trace and len(stack_trace) > 50:
            root_cause = {
                "description": f"Error detected in application. Review full traceback for details.",
                "confidence": "low",
            }
        else:
            root_cause = {
                "description": "Insufficient information to determine exact root cause.",
                "confidence": "low",
            }
    
    return root_cause


def analyze_affected_files(error_message: str, stack_trace: Optional[str] = None) -> Dict[str, List[str]]:
    """Identify files likely affected by the failure."""
    affected = {
        "likely_affected": [],
        "not_affected": [],
    }
    
    text_lower = (error_message + " " + (stack_trace or "")).lower()
    
    # Extract file paths from stack traces if available
    if stack_trace:
        import_paths = re.findall(r'File "(.+?)"', stack_trace)
        for imp_path in import_paths[:5]:
            safe_path = safe_rel_path(imp_path)
            if safe_path:
                affected["likely_affected"].append(safe_path)
    
    return affected


def build_fix_plan(
    failure_type: str,
    root_cause: Dict[str, Any],
    affected_files: List[str],
    task_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Build a structured fix plan for the identified issue."""
    fix_tasks = []
    
    # Generate task ID if not provided
    if task_id is None or task_id == "DEBUG":
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        fix_task_id = f"FIX-{timestamp}"
    else:
        fix_task_id = f"{task_id}-FIX-1"
    
    # Create fix task based on failure type
    title_map = {
        "syntax_error": "Fix syntax error in code",
        "type_error": "Fix type mismatch or undefined variable",
        "import_error": "Install missing dependency or fix import path",
        "dependency_error": "Update or reinstall dependencies",
        "configuration_error": "Correct configuration or environment variables",
        "environment_error": "Set up required environment or install packages",
        "database_error": "Fix database connection or query issue",
        "migration_error": "Review and fix migration script",
        "api_error": "Fix API endpoint implementation",
        "frontend_error": "Fix frontend component or routing",
        "backend_error": "Fix backend service logic",
        "runtime_error": "Handle runtime exception properly",
        "test_failure": "Fix failing test or underlying code causing failure",
        "integration_test_failure": "Fix integration between components",
        "build_failure": "Fix build configuration or dependency issues",
        "lint_failure": "Fix linting/formatting issues",
    }
    
    task_title = title_map.get(failure_type, f"Fix {failure_type}")
    task_description = root_cause.get("description", f"Address the {failure_type} issue")
    
    fix_task = {
        "task_id": fix_task_id,
        "title": task_title,
        "description": task_description,
        "target_files": affected_files[:5] if affected_files else ["backend/app/main.py"],
        "assigned_agent": "coding_agent",
        "dependencies": [],
        "priority": "high" if root_cause.get("confidence") == "high" else "medium",
        "complexity": "medium",
        "acceptance_criteria": [
            f"{failure_type.replace('_', ' ')} is resolved",
            "Related tests pass",
            "No new errors introduced",
        ],
        "validation": [
            f"Run validation for {failure_type}",
            "Verify through related API endpoints or UI",
        ],
    }
    
    fix_tasks.append(fix_task)
    
    # Add re-test task if applicable
    if failure_type in ["test_failure", "api_error", "database_error"]:
        retest_task = {
            "task_id": f"{fix_task_id}-RETEST",
            "title": "Re-run failed tests/API checks",
            "description": "Run the previously failing validation to confirm fix.",
            "target_files": [],
            "assigned_agent": "testing_agent",
            "dependencies": [fix_task_id],
            "priority": "high",
            "complexity": "low",
            "acceptance_criteria": [f"{failure_type.replace('_', ' ')} test/check passes"],
            "validation": [],
        }
        fix_tasks.append(retest_task)
    
    return fix_tasks


def build_debugging_prompt(
    error_message: str,
    stack_trace: Optional[str] = None,
    failure_type: Optional[str] = None,
    severity: Optional[str] = None,
    affected_files: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Build a text-only prompt for Qwen 3.5 debugging analysis."""
    messages = []
    
    system_content = f"""You are the Debugging Agent for Sanskriti AI Studio.
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.

You are responsible for:
1. Analyzing failure reports
2. Identifying root causes
3. Classifying failure types and severity
4. Recommending fix strategies
5. Assigning appropriate agents for remediation
6. Tracking debugging attempts to prevent infinite loops
7. Escalating issues that cannot be resolved automatically

You will receive structured input containing error messages, stack traces, and context.
Always base your analysis on the evidence provided. Do not invent errors or causes.
"""
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    failure_report = f"""## Failure Report

### Failure Type: {failure_type or 'unknown'}
### Severity: {severity or 'medium'}

### Error Message:
{error_message[:5000]}

### Stack Trace:
{"{stack_trace}" if stack_trace else "No stack trace provided"}

### Context:
- Affected files: {', '.join(affected_files) if affected_files else 'unknown'}
"""
    
    messages.append({
        "role": "user",
        "content": failure_report,
    })
    
    return messages


def process_debugging_request(
    debugging_input: Dict[str, Any],
    retry_count: int = 0,
) -> Dict[str, Any]:
    """Process a debugging request and return analysis result."""
    root_cause: Dict[str, Any] = {}  # Initialize to avoid unbound variable error
    result = {
        "agent": "debugger_agent",
        "status": "processing",
        "timestamp": utc_now(),
        "input_received": False,
        "diagnosis_complete": False,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(debugging_input)
        
        if not debugging_input:
            result["status"] = "no_input"
            result["message"] = "No debugging input provided."
            return result
        
        # Extract input fields with defaults
        error_message = debugging_input.get("error_message", "")
        stack_trace = debugging_input.get("stack_trace", "")
        failure_type = debugging_input.get("failure_type")
        affected_files = debugging_input.get("affected_files", [])
        command_executed = debugging_input.get("command_executed", "")
        exit_code = debugging_input.get("exit_code")
        task_id = debugging_input.get("task_id")
        
        # Step 2: Classify failure type if not already classified
        if not failure_type or failure_type == "unknown":
            failure_type = classify_failure_type(error_message, stack_trace)
            
        result["failure_classification"] = failure_type
        
        # Step 3: Detect severity
        severity = detect_severity(failure_type, error_message)
        result["severity"] = severity
        
        # Step 4: Extract root cause (can use model or direct analysis)
        root_cause = extract_root_cause(error_message, stack_trace)
        result["root_cause_extraction"] = root_cause
        
        # Step 5: Analyze affected files
        affected_analysis = analyze_affected_files(error_message, stack_trace)
        result["affected_files"] = {
            "likely": affected_analysis.get("likely_affected", []),
            "not": [],
        }
        
        # Step 6: Determine if model-based analysis is needed
        confidence_needed = root_cause.get("confidence") == "low" or not stack_trace
        
        # Step 7: Build and send model prompt if needed (TEXT-ONLY)
        if confidence_needed:
            messages = build_debugging_prompt(
                error_message=error_message,
                stack_trace=stack_trace,
                failure_type=failure_type,
                severity=severity,
                affected_files=affected_analysis.get("likely_affected", []),
            )
            
            # Build config for LM Studio call
            config = {
                'base_url': os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1'),
                'model': os.getenv('QWEN_3_5_MODEL', ''),
            }
            
            try:
                if config['model']:
                    model_response = chat_with_coding_model(messages=messages, **config)
                    if model_response and model_response.get('choices'):
                        analysis_content = model_response['choices'][0].get('message', {}).get('content', '')
                        
                        try:
                            model_analysis = json.loads(analysis_content)
                            result["model_analysis"] = model_analysis
                            
                            if model_analysis.get("fix_plan"):
                                result["fix_plan"] = model_analysis["fix_plan"]
                                
                        except json.JSONDecodeError:
                            result["model_analysis_raw"] = analysis_content[:2000]
                            
            except Exception as e:
                # Model unavailable - continue with direct analysis
                pass
        
        # Step 8: Build fix plan
        fix_plan = build_fix_plan(
            failure_type=failure_type,
            root_cause=root_cause,
            affected_files=affected_analysis.get("likely_affected", []),
            task_id=task_id,
        )
        result["fix_plan"] = fix_plan
        
        # Step 9: Determine retry recommendation
        retry_recommended = severity in ["medium", "low"] and retry_count < MAX_DEBUG_RETRIES
        
        if failure_type == "unknown_error" or severity == "critical":
            retry_recommended = False
        
        result["retry_recommendation"] = {
            "recommended": retry_recommended,
            "reason": "Transient issue may be retryable" if retry_recommended else 
                      "Critical/non-retryable issue detected",
        }
        
        # Step 10: Determine escalation need
        escalation_required = (
            retry_count >= MAX_DEBUG_RETRIES or
            severity == "critical"
        )
        
        result["escalation_required"] = escalation_required
        if escalation_required:
            if retry_count >= MAX_DEBUG_RETRIES:
                result["escalation_reason"] = f"Retry limit reached ({retry_count}/{MAX_DEBUG_RETRIES})"
            elif severity == "critical":
                result["escalation_reason"] = "Critical issue detected"
        
        result["diagnosis_complete"] = True
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {str(e)}"
    
    return result


def build_final_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build the structured debugging final report."""
    diagnosis = state.get("diagnosis_complete", False)
    
    root_cause_data = state.get("root_cause_extraction", {})
    
    if not diagnosis:
        summary = "Debugging analysis incomplete."
    else:
        root_cause_desc = root_cause_data.get("description", "Unknown root cause")
        failure_type = state.get("failure_classification", "unknown")
        severity = state.get("severity", "medium")
        
        summary = f"{failure_type} ({severity}) - {root_cause_desc}"
    
    report = {
        "agent": "debugger_agent",
        "status": "completed" if diagnosis else "incomplete",
        "summary": summary,
        "timestamp": utc_now(),
        "diagnosis": {
            "failure_type": state.get("failure_classification"),
            "severity": state.get("severity"),
            "root_cause": root_cause_data,
            "affected_files": {
                "likely": state.get("affected_files", {}).get("likely", []),
                "not": [],
            },
        },
        "fix_plan": state.get("fix_plan", []),
        "retry_recommendation": state.get("retry_recommendation", {
            "recommended": False,
            "reason": None,
        }),
        "escalation_required": state.get("escalation_required", False),
        "escalation_reason": state.get("escalation_reason"),
        "confidence_level": root_cause_data.get("confidence") if isinstance(root_cause_data, dict) else "medium",
    }
    
    return report


def main():
    """CLI entry point for the Debugging Agent."""
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Debugging Agent."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="JSON file with debugging input (error message, stack trace, etc.)",
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=0,
        help="Current retry count for this debugging attempt",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("DEBUGGING AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    debugging_input: Optional[Dict[str, Any]] = None
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                debugging_input = json.load(f)
            print(f"\n[DEBUGGER] Input loaded from: {args.input}")
        except Exception as e:
            print(f"\n[ERROR] Failed to load input file: {e}")
    else:
        try:
            input_data = json.load(sys.stdin)
            debugging_input = input_data
            print("\n[DEBUGGER] Input received via stdin")
        except Exception as e:
            print(f"\n[ERROR] Failed to parse stdin input: {e}")
    
    debugging_request_id = generate_debugging_request_id()
    retry_count = args.retry_count
    
    if debugging_input is None:
        print("[ERROR] No valid debugging input provided.")
        return  # Exit early to avoid type errors
    
    result = process_debugging_request(debugging_input, retry_count)
    report = build_final_report({**load_debugger_state(), **result})
    save_debugger_state(report)
    
    print("\n" + "=" * 70)
    print("DEBUGGING AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Request ID: {debugging_request_id}")
    print(f"Status: {report['status']}")
    print(f"\nDiagnosis:")
    print(f"  Failure Type: {report['diagnosis']['failure_type']}")
    print(f"  Severity: {report['diagnosis']['severity']}")
    print(f"  Root Cause: {report['diagnosis']['root_cause'].get('description', 'N/A')}")
    
    if report.get("fix_plan"):
        print(f"\nFix Plan:")
        for task in report["fix_plan"]:
            print(f"  - {task['task_id']}: {task['title']}")
    
    print(f"\nRetry Recommendation: {'Yes' if report['retry_recommendation']['recommended'] else 'No'}")
    
    if report.get("escalation_required"):
        print(f"\n[!] ESCALATION REQUIRED: {report['escalation_reason']}")
    
    print("\nTEXT-ONLY LLM CHECK:")
    print("- Images sent to Qwen 3.5: NO")
    print("- Image input added: NO")
    print("- Visual analysis attempted: NO")
    print("=" * 70)
    
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
