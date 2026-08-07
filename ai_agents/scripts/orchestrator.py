#!/usr/bin/env python3
"""
Orchestrator Agent Runtime for Sanskriti AI Studio.

This runtime coordinates the multi-agent development workflow by:
1. Receiving a task from the user
2. Reading project documentation to understand context
3. Creating an execution plan
4. Executing appropriate agents (Coding, Testing, Documentation) in sequence
5. Collecting results and handling failures with retry logic
6. Producing a final execution report

CRITICAL: Qwen 3.5 is TEXT-ONLY. This runtime never sends images or visual data.

Version: 1.0
Last Updated: 2026-07-30
"""

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
ORCHESTRATOR_STATE_DIR = os.path.join(STATE_DIR, "orchestrator")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
ORCHESTRATOR_LOGS_DIR = os.path.join(LOGS_DIR, "orchestrator")

TASK_STATE_PATH = os.path.join(ORCHESTRATOR_STATE_DIR, "current_task.json")
ACTIONS_PATH = os.path.join(STATE_DIR, "actions.jsonl")
EXECUTION_LOGS_PATH = os.path.join(ORCHESTRATOR_LOGS_DIR, "execution.log")

MAX_RETRIES = 3


TASK_STATES = {
    "PENDING": "Task received, awaiting planning",
    "PLANNING": "Execution plan being created",
    "IN_PROGRESS": "Agent currently executing",
    "CODING": "Coding Agent active",
    "TESTING": "Testing Agent active",
    "FAILED": "Validation failed",
    "FIXING": "Sending back to coding agent for fix",
    "RETESTING": "Retrying after fixes applied",
    "DOCUMENTING": "Documentation Agent running",
    "COMPLETED": "Task successfully completed",
    "BLOCKED": "Retry limit reached, needs manual intervention",
    "CANCELLED": "Task cancelled by user",
}


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


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
    """Append a timestamped event to the orchestrator execution log."""
    os.makedirs(ORCHESTRATOR_LOGS_DIR, exist_ok=True)
    timestamp = utc_now()
    log_entry = f"[{timestamp}] [ORCHESTRATOR] {message}\n"
    with open(EXECUTION_LOGS_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append an action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "orchestrator",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(ACTIONS_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_task_state() -> Dict[str, Any]:
    """Load current orchestrator task state."""
    return load_json_file(TASK_STATE_PATH) or {
        "task_id": None,
        "task_name": None,
        "description": "",
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
        "current_agent": None,
        "execution_steps": [],
        "completed_steps": [],
        "failed_steps": [],
        "retry_count": 0,
        "max_retries": MAX_RETRIES,
        "errors": [],
        "warnings": [],
        "final_result": None,
    }


def save_task_state(state: Dict[str, Any]) -> None:
    """Persist orchestrator task state."""
    os.makedirs(ORCHESTRATOR_STATE_DIR, exist_ok=True)
    with open(TASK_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def generate_task_id() -> str:
    """Generate a unique task ID for the orchestrator."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"STEP-ORCHESTRATOR-{timestamp}"


# ============================================================================
# Documentation Reader
# ============================================================================

def load_all_documentation() -> Dict[str, str]:
    """Load all relevant project documentation for context."""
    docs = {
        "00_PROJECT_STORY": read_doc("docs/00_PROJECT_STORY.md"),
        "01_CODING_RULES": read_doc("docs/01_CODING_RULES.md"),
        "02_SYSTEM_ARCHITECTURE": read_doc("docs/02_SYSTEM_ARCHITECTURE.md"),
        "03_DATABASE_DESIGN": read_doc("docs/03_DATABASE_DESIGN.md"),
        "04_API_SPECIFICATION": read_doc("docs/04_API_SPECIFICATION.md"),
        "05_ROADMAP": read_doc("docs/05_ROADMAP.md"),
        "06_CURRENT_TASK": read_doc("docs/06_CURRENT_TASK.md"),
        "07_DEVELOPMENT_GUIDELINES": read_doc("docs/07_DEVELOPMENT_GUIDELINES.md"),
        "08_AI_CONTEXT": read_doc("docs/08_AI_CONTEXT.md"),
        "09_COMPLETED_TASKS": read_doc("docs/09_COMPLETED_TASKS.md"),
        "10_NEXT_TASK": read_doc("docs/10_NEXT_TASK.md"),
        "11_CHANGELOG": read_doc("docs/11_CHANGELOG.md"),
    }
    return {k: v for k, v in docs.items() if v is not None}


def read_doc(path: str) -> Optional[str]:
    """Read a documentation file."""
    full_path = safe_rel_path(path)
    if not full_path:
        return None
    return load_text_file(os.path.join(WORKSPACE_ROOT, full_path))


def get_current_milestone() -> str:
    """Extract current milestone from Current Task doc."""
    current_task_doc = read_doc("docs/06_CURRENT_TASK.md")
    if current_task_doc:
        match = re.search(r"(?i)(Milestone\s+\d+\.\d+|Step\s+\d+)[:\s]+COMPLETED", current_task_doc)
        if match:
            return f"{match.group()}"
    return "Unknown"


def get_next_task_description() -> str:
    """Extract next task description from Next Task doc."""
    next_task_doc = read_doc("docs/10_NEXT_TASK.md")
    if next_task_doc:
        match = re.search(r"#\s*Sanskriti\s+AI\s+Studio\s*—\s*Next\s+Task", next_task_doc)
        if match:
            content = next_task_doc[match.start():]
            lines = content.split("\n")
            for line in lines[:5]:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped[:500].strip()
    return "No next task description available."


# ============================================================================
# Execution Plan Generator
# ============================================================================

def create_execution_plan(task_description: str) -> Dict[str, Any]:
    """Create an execution plan based on the task description."""
    plan = {
        "task_id": None,
        "description": task_description,
        "steps": [],
    }
    
    text_lower = task_description.lower()
    
    # Check for coding/implementation tasks
    if any(keyword in text_lower for keyword in ["implement", "create", "write", "add", "code", "feature"]):
        plan["steps"].append({
            "order": 1,
            "type": "CODING",
            "description": "Execute Coding Agent for implementation",
        })
    
    # Check for testing/verification tasks
    if any(keyword in text_lower for keyword in ["test", "validate", "verify", "check", "lint", "build"]):
        plan["steps"].append({
            "order": 2,
            "type": "TESTING",
            "description": "Execute Testing Agent for validation",
        })
    
    # Check for documentation tasks
    if any(keyword in text_lower for keyword in ["document", "docs", "read documentation", "report"]):
        plan["steps"].append({
            "order": 3,
            "type": "DOCUMENTATION",
            "description": "Execute Documentation Agent to update docs",
        })
    
    # If task is analysis-only (no code changes needed)
    if not plan["steps"]:
        plan["steps"] = [{
            "order": 1,
            "type": "ANALYSIS",
            "description": "Analyze current state and report results",
        }]
    
    return plan


# ============================================================================
# Agent Executor Functions
# ============================================================================

def execute_coding_agent() -> Optional[Dict[str, Any]]:
    """Execute the Coding Agent and return its result."""
    try:
        from ai_agents.scripts.coder_agent import process_task
        result = process_task()
        return result
    except Exception as e:
        print(f"[ORCHESTRATOR] Coding Agent error: {e}")
        return None


def execute_testing_agent() -> Optional[Dict[str, Any]]:
    """Execute the Testing Agent and return its result."""
    try:
        from ai_agents.scripts.tester_agent import process_task
        result = process_task()
    except Exception as e:
        print(f"[ORCHESTRATOR] Testing Agent error: {e}")
        return None


def execute_documentation_agent(task_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute the Documentation Agent and return its result."""
    try:
        from ai_agents.agents.documentation_agent import process_task
        result = process_task(task_input)
        return result
    except Exception as e:
        print(f"[ORCHESTRATOR] Documentation Agent error: {e}")
        return None


def execute_reviewer_agent(input_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Execute the Review Agent and return its result."""
    try:
        from ai_agents.scripts.reviewer_agent import process_task
        result = process_task(input_path=input_path)
        return result
    except Exception as e:
        print(f"[ORCHESTRATOR] Review Agent error: {e}")
        return None


def execute_analysis_agent() -> Optional[Dict[str, Any]]:
    """Execute analysis using Coding Agent in read-only mode."""
    try:
        from ai_agents.scripts.coder_agent import process_task
        result = process_task()
        
        # Check for implementation instructions
        content = ""
        if result and result.get("response"):
            choices = result["response"].get("choices", [{}])
            if choices:
                msg = choices[0].get("message", {})
                if msg:
                    content = msg.get("content", "")
        
        has_impl_keywords = any(kw in (content or "").lower() for kw in ["implement", "create", "write", "add", "modify"])
        status = "success" if not has_impl_keywords else "needs_review"
        
        return {
            "status": status,
            "summary": "Analysis complete - no implementation required" if status == "success" else "Analysis requires review",
            "next_action": "REPORT",
        }
    except Exception as e:
        print(f"[ORCHESTRATOR] Analysis Agent error: {e}")
        return None


# ============================================================================
# Orchestration Logic
# ============================================================================

def orchestrate_task(task: str, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Main orchestration function that runs the full agent workflow."""
    task_id = generate_task_id()
    state = load_task_state()
    
    # Update state with new task
    state["task_id"] = task_id
    state["task_name"] = task[:100]
    state["description"] = task
    state["status"] = "PENDING"
    state["start_time"] = utc_now()
    state["execution_steps"] = []
    state["completed_steps"] = []
    state["failed_steps"] = []
    state["retry_count"] = 0
    state["errors"] = []
    state["warnings"] = []
    state["final_result"] = None
    
    save_task_state(state)
    
    log_event(f"Task received: {task_id[:50]}...")
    record_action("task_received", {"task_id": task_id, "description": task[:200]})
    
    print("=" * 70)
    print("ORCHESTRATOR AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    print(f"\nTask ID: {task_id}")
    print(f"Task: {task[:100]}...")
    
    # Step 2: Read documentation
    log_event("Reading project documentation")
    record_action("reading_documentation", {})
    
    documentation = load_all_documentation()
    current_milestone = get_current_milestone()
    next_task_desc = get_next_task_description()
    
    print(f"\n[ORCHESTRATOR] Current Milestone: {current_milestone}")
    print(f"[ORCHESTRATOR] Next Task (from docs): {next_task_desc[:200]}...")
    
    # Step 3: Create execution plan
    log_event("Creating execution plan")
    record_action("creating_plan", {})
    
    execution_plan = create_execution_plan(task)
    state["execution_steps"] = execution_plan["steps"]
    state["status"] = "PLANNING"
    save_task_state(state)
    
    print(f"\n[ORCHESTRATOR] Execution Plan Created:")
    for step in execution_plan["steps"]:
        print(f"  - Step {step['order']}: {step['type']} - {step['description']}")
    
    # Step 4: Execute plan steps
    retry_count = 0
    blocked = False
    
    for step_idx, step in enumerate(execution_plan["steps"]):
        step_type = step["type"]
        
        log_event(f"Starting {step_type} Agent")
        record_action("starting_agent", {"step": step_idx + 1, "type": step_type})
        
        print(f"\n[ORCHESTRATOR] Starting {step_type} Agent...")
        state["current_agent"] = f"{step_type.lower()}_agent"
        state["status"] = TASK_STATES.get(step_type, "IN_PROGRESS")
        save_task_state(state)
        
        try:
            # Execute the appropriate agent based on step type
            if step_type == "CODING":
                result = execute_coding_agent()
            elif step_type == "TESTING":
                result = execute_testing_agent()
            elif step_type == "DOCUMENTATION":
                result = execute_documentation_agent({
                    "task_id": task_id,
                    "task_description": task,
                    "current_milestone": current_milestone,
                })
            elif step_type == "ANALYSIS":
                result = execute_analysis_agent()
            else:
                print(f"[ORCHESTRATOR] Unknown step type: {step_type}")
                continue
            
            # Log agent completion
            log_event(f"{step_type} Agent completed")
            record_action("agent_completed", {"step": step_idx + 1, "result_summary": result.get("status", "unknown") if result else "none"})
            
            # Store result
            state["execution_steps"][step_idx]["result"] = result
            state["completed_steps"].append({
                "step_number": step_idx + 1,
                "type": step_type,
                "result": result,
            })
            
            if result and result.get("status") == "success":
                print(f"[ORCHESTRATOR] {step_type} Agent completed successfully.")
            else:
                print(f"[ORCHESTRATOR] {step_type} Agent reported an issue.")
            
            state["retry_count"] = retry_count
            save_task_state(state)
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            log_event(f"{step_type} Agent failed: {error_msg}")
            record_action("agent_failed", {"step": step_idx + 1, "error": error_msg})
            
            state["errors"].append({
                "step": step_idx + 1,
                "type": step_type,
                "error": error_msg,
                "retry_count": retry_count,
            })
            
            if retry_count < max_retries and not blocked:
                print(f"[ORCHESTRATOR] Retry {retry_count + 1}/{max_retries} for {step_type} Agent...")
                state["status"] = "RETESTING"
                retry_count += 1
                continue
            else:
                print(f"[ORCHESTRATOR] Retry limit reached. Marking task BLOCKED.")
                state["status"] = "BLOCKED"
                blocked = True
            
            state["retry_count"] = retry_count
            save_task_state(state)
    
    # Step 5: Build final result
    if blocked:
        state["status"] = "BLOCKED"
        log_event("Task marked BLOCKED due to repeated failures")
        print(f"\n[ORCHESTRATOR] Task BLOCKED - Retry limit reached.")
    elif state["completed_steps"]:
        state["status"] = "COMPLETED"
        log_event("Task COMPLETED successfully")
        print(f"\n[ORCHESTRATOR] Task COMPLETED successfully.")
    else:
        state["status"] = "FAILED"
        log_event("Task FAILED without any completed steps")
        print(f"\n[ORCHESTRATOR] Task FAILED - No steps completed.")
    
    # Set end time
    state["end_time"] = utc_now()
    state["final_result"] = {
        "task_id": task_id,
        "status": state["status"],
        "completed_steps": len(state["completed_steps"]),
        "failed_steps": len([s for s in state.get("failed_steps", [])]),
        "errors": state["errors"],
        "warnings": state["warnings"],
    }
    save_task_state(state)
    
    # Build final report
    return build_final_report(task_id, task, state)


def build_final_report(task_id: str, task_description: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Build the structured final execution report."""
    completed = state.get("completed_steps", [])
    errors = state.get("errors", [])
    status = state.get("status", "UNKNOWN")
    
    summary_parts = []
    if completed:
        for step in completed:
            step_type = step.get("type", "unknown")
            result = step.get("result", {})
            if result and result.get("status"):
                status_str = result.get("status", "unknown").upper()
                summary_parts.append(f"{step_type}: {status_str}")
    
    if not summary_parts:
        summary_parts.append("No agent steps completed.")
    
    summary = "; ".join(summary_parts)
    
    report = {
        "task_id": task_id,
        "task_description": task_description,
        "status": status,
        "summary": summary,
        "started_at": state.get("start_time"),
        "ended_at": state.get("end_time"),
        "execution_steps": [
            {
                "order": step.get("order"),
                "type": step.get("type"),
                "description": step.get("description"),
                "completed": step.get("result", {}).get("status") in ["success", "PASS"],
                "errors": [],
            }
            for step in state.get("execution_steps", [])
        ],
        "completed_steps": [
            {
                "step_number": s.get("step_number"),
                "type": s.get("type"),
                "result_status": s.get("result", {}).get("status") if s.get("result") else None,
            }
            for s in completed
        ],
        "failed_steps": [
            {
                "retry_count": e.get("retry_count", 0),
                "error": e.get("error"),
            }
            for e in errors
        ],
        "errors": [e.get("error") for e in errors],
        "warnings": state.get("warnings", []),
        "text_only_llm_check": {
            "images_sent_to_qwen_3_5": "NO",
            "image_input_added": "NO",
            "visual_analysis_attempted": "NO",
        },
    }
    
    if status == "BLOCKED":
        report["recommendations"] = [
            "Task has reached maximum retry limit.",
            "Manual intervention required to resolve issues.",
            "Check error logs for details: ai_agents/logs/orchestrator/execution.log",
        ]
    elif status == "COMPLETED":
        report["recommendations"] = [
            "Task completed successfully.",
            "Review documentation changes in docs/",
            "Run frontend build to verify output.",
        ]
    else:
        report["recommendations"] = [
            "Review error logs for details.",
            "Consider breaking down the task into smaller steps.",
        ]
    
    return report


def main() -> None:
    """CLI entry point for the Orchestrator Agent."""
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Orchestrator Agent."
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="The task to execute (e.g., 'Analyze current project documentation and report milestone').",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("ORCHESTRATOR AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    report = orchestrate_task(args.task)
    
    print("\n" + "=" * 70)
    print("ORCHESTRATOR EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Task ID: {report['task_id']}")
    print(f"Status: {report['status'].upper()}")
    print(f"\nSummary: {report['summary']}")
    
    if report.get("recommendations"):
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    
    print("\nTEXT-ONLY LLM CHECK:")
    print("- Images sent to Qwen 3.5: NO")
    print("- Image input added: NO")
    print("- Visual analysis attempted: NO")
    print("=" * 70)


if __name__ == "__main__":
    main()
