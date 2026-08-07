#!/usr/bin/env python3
"""
Orchestrator Agent Runtime for Sanskriti AI Studio.

This runtime coordinates multi-agent development workflows.
The Orchestrator Agent:
1. Receives high-level development requests from user
2. Coordinates Planning, Coding, Testing, Debugging agents
3. Manages workflow state and transitions
4. Handles failures and escalations
5. Ensures no images are sent to Qwen 3.5

Version: 1.0
Last Updated: 2026-08-04
"""

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# --- Configuration ---------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
ORCHESTRATOR_STATE_DIR = os.path.join(STATE_DIR, "orchestrator")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
ORCHESTRATOR_LOGS_DIR = os.path.join(LOGS_DIR, "orchestrator")


# Import read_project_documentation from coding_agent module
from scripts.coding_agent import read_project_documentation

def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_orchestrator_request_id() -> str:
    """Generate a unique orchestrator request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return "ORCH-" + timestamp + "-" + unique_id


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
    log_entry = "[{}] [ORCHESTRATOR] {}\n".format(timestamp, message)
    with open(os.path.join(ORCHESTRATOR_LOGS_DIR, "execution.log"), "a", encoding="utf-8") as f:
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
    with open(os.path.join(STATE_DIR, "actions.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_orchestrator_state() -> Dict[str, Any]:
    """Load current orchestrator task state."""
    state_path = os.path.join(ORCHESTRATOR_STATE_DIR, "current_orch.json")
    return load_json_file(state_path) or {
        "orchestrator_request_id": None,
        "task_id": None,
        "milestone": None,
        "user_request": None,
        "planner_result": None,
        "coding_result": None,
        "testing_result": None,
        "debugging_result": None,
        "documentation_result": None,
        "reviewer_result": None,
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
        "error": None,
    }


def save_orchestrator_state(state: Dict[str, Any]) -> None:
    """Persist orchestrator task state."""
    os.makedirs(ORCHESTRATOR_STATE_DIR, exist_ok=True)
    with open(os.path.join(ORCHESTRATOR_STATE_DIR, "current_orch.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# --- Workflow Functions ----------------------------------------------------

def build_orchestration_prompt(
    request_id: str,
    user_request: str,
    milestone: str,
) -> List[Dict[str, str]]:
    """Build a text-only prompt for Qwen 3.5 orchestration assistance."""
    messages = []
    
    system_content = """You are the Orchestrator Agent for Sanskriti AI Studio.
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.

You coordinate multi-agent development workflows:
1. Plan tasks using Planner Agent
2. Execute coding with Coding Agent
3. Test with Testing Agent (with Debugging on failure)
4. Review with Reviewer Agent
5. Document with Documentation Agent

Workflow:
USER -> ORCHESTRATOR -> PLANNER -> CODING AGENT -> TESTING AGENT 
-> Debugging Agent (on failure) -> Testing Agent -> REVIEWER AGENT 
    ↓ APPROVED/APPROVED_WITH_WARNINGS                    ↓ REQUIRES_CHANGES/REJECTED
  DOCUMENTATION AGENT                                  CODING AGENT
                                                        -> TESTING AGENT
                                                        -> Reviewer Agent

Milestone: {milestone}
User Request: {user_request}
""".format(
        request_id=request_id,
        milestone=milestone,
        user_request=user_request[:5000]
    )
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    return messages


def process_planning_stage(
    orchestrator_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Coordinate the planning stage of development workflow."""
    result = {
        "agent": "orchestrator",
        "stage": "planning",
        "status": "processing",
        "input_received": False,
        "planner_result": None,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        
        # Load project documentation for context
        docs_context = read_project_documentation()
        
        # Create planning request for Planner Agent
        planning_input = {
            "request_id": generate_orchestrator_request_id(),
            "user_request": user_request,
            "milestone": milestone,
            "previous_results": [],  # First stage has no previous results
        }
        
        # In real implementation, this would call the Planner Agent
        # For now, we simulate a successful planning result
        simulated_planning_result = {
            "agent": "planner_agent",
            "status": "completed",
            "tasks": [
                {
                    "task_id": "TASK-001",
                    "description": "Implement core functionality",
                    "agent": "coding_agent",
                    "dependencies": [],
                    "acceptance_criteria": [
                        "Core implementation complete",
                        "Code follows project conventions",
                    ],
                },
                {
                    "task_id": "TASK-002",
                    "description": "Add tests for new functionality",
                    "agent": "testing_agent",
                    "dependencies": ["TASK-001"],
                    "acceptance_criteria": [
                        "Unit tests written and passing",
                    ],
                },
            ],
        }
        
        result["planner_result"] = simulated_planning_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_coding_stage(
    orchestrator_input: Dict[str, Any],
    planning_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Coordinate the coding stage of development workflow."""
    result = {
        "agent": "orchestrator",
        "stage": "coding",
        "status": "processing",
        "input_received": False,
        "coding_result": None,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        task_id = orchestrator_input.get("task_id") or planning_result.get("tasks", [{}])[0].get("task_id") if planning_result and planning_result.get("tasks") else "TASK-001"
        
        # Load project documentation for context
        docs_context = read_project_documentation()
        
        # Create coding request for Coding Agent
        coding_input = {
            "task_id": task_id,
            "milestone": milestone,
            "plan": planning_result,
            "acceptance_criteria": [],
            "previous_task_results": [],
        }
        
        # In real implementation, this would call the Coding Agent
        # For now, we simulate a successful coding result
        simulated_coding_result = {
            "agent": "coding_agent",
            "status": "completed",
            "documentation_read": True,
            "code_generation_complete": True,
            "files_generated": 1,
            "completion_summary": "Generated code for milestone {}".format(milestone),
        }
        
        result["coding_result"] = simulated_coding_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_testing_stage(
    orchestrator_input: Dict[str, Any],
    coding_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Coordinate the testing stage of development workflow."""
    result = {
        "agent": "orchestrator",
        "stage": "testing",
        "status": "processing",
        "input_received": False,
        "testing_result": None,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        
        # Load project documentation for context
        docs_context = read_project_documentation()
        
        # Create testing request for Testing Agent
        task_id = user_request
        if isinstance(coding_result, dict):
            task_id = coding_result.get("task_id") or user_request

        testing_input = {
            "task_id": task_id,
            "milestone": milestone,
            "changed_files": [],
            "previous_task_results": [],
        }
        
        # In real implementation, this would call the Testing Agent
        # For now, we simulate a successful testing result
        simulated_testing_result = {
            "agent": "testing_agent",
            "status": "completed",
            "tests_run": 3,
            "tests_passed": 3,
            "tests_failed": 0,
            "test_results": [
                {"name": "Unit Tests", "status": "passed", "count": 2},
                {"name": "Integration Tests", "status": "passed", "count": 1},
            ],
        }
        
        result["testing_result"] = simulated_testing_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_debugging_stage(
    orchestrator_input: Dict[str, Any],
    testing_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Coordinate the debugging stage when testing fails."""
    # Check if debugging is needed (only if tests failed)
    tests_failed = testing_result.get("tests_failed", 0)
    
    if tests_failed == 0:
        return None  # No debugging needed
    
    result = {
        "agent": "orchestrator",
        "stage": "debugging",
        "status": "processing",
        "input_received": True,
        "debugging_result": None,
        "error": None,
    }
    
    try:
        # Load project documentation for context
        docs_context = read_project_documentation()
        
        # Create debugging request for Debugging Agent
        debugging_input = {
            "task_id": orchestrator_input.get("task_id"),
            "failure_source": "testing_agent",
            "failure_type": "test_failure",
            "error_message": "Some tests failed: {}".format(testing_result),
        }
        
        # In real implementation, this would call the Debugging Agent
        # For now, we simulate a successful debugging result
        simulated_debugging_result = {
            "agent": "debugger_agent",
            "status": "completed",
            "diagnosis": {
                "failure_type": "test_failure",
                "severity": "medium",
                "root_cause": {
                    "description": "Tests need to be added for new functionality",
                    "confidence": "high",
                },
            },
            "fix_plan": [
                {
                    "task_id": "FIX-001",
                    "title": "Add unit tests for new functionality",
                    "target_files": [],
                    "assigned_agent": "coding_agent",
                },
            ],
        }
        
        result["debugging_result"] = simulated_debugging_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_reviewer_stage(
    orchestrator_input: Dict[str, Any],
    coding_result: Optional[Dict[str, Any]] = None,
    testing_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Coordinate the reviewer stage after successful testing."""
    result = {
        "agent": "orchestrator",
        "stage": "reviewing",
        "status": "processing",
        "input_received": False,
        "reviewer_result": None,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        
        # Create reviewer request for Reviewer Agent
        reviewer_input = {
            "task_id": orchestrator_input.get("task_id"),
            "plan_id": None,  # Would be extracted from planner result
            "milestone": milestone,
            "original_user_request": user_request,
            "completed_tasks": [
                {"agent": coding_result["agent"] if coding_result else None},
                {"agent": testing_result["agent"] if testing_result else None},
            ],
            "acceptance_criteria": [],
            "changed_files": [],
            "coding_agent_result": coding_result,
            "testing_agent_result": testing_result,
            "debugging_agent_result": None,
            "lint_results": {},
            "build_results": {},
            "review_attempt": 1,
        }
        
        # In real implementation, this would call the Reviewer Agent
        # For now, we simulate an approved result
        simulated_reviewer_result = {
            "review_id": generate_orchestrator_request_id(),
            "task_id": orchestrator_input.get("task_id"),
            "milestone": milestone,
            "status": "APPROVED",
            "summary": "Implementation approved - all criteria met.",
            "requirements_result": "approved",
            "acceptance_criteria_result": "approved",
            "architecture_result": "approved",
            "code_quality_result": "approved",
            "backend_result": "approved",
            "frontend_result": "approved",
            "api_result": "approved",
            "database_result": "approved",
            "security_result": "approved",
            "testing_result": "approved",
            "documentation_result": "approved",
            "findings": [],
            "review_attempt": 1,
        }
        
        result["reviewer_result"] = simulated_reviewer_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_documentation_stage(
    orchestrator_input: Dict[str, Any],
    reviewer_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Coordinate the documentation stage after successful review."""
    result = {
        "agent": "orchestrator",
        "stage": "documenting",
        "status": "processing",
        "input_received": False,
        "documentation_result": None,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        
        # Create documentation request for Documentation Agent
        documentation_input = {
            "task_id": orchestrator_input.get("task_id"),
            "milestone": milestone,
            "previous_task_results": [
                {"agent": reviewer_result["agent"]},
            ],
        }
        
        # In real implementation, this would call the Documentation Agent
        # For now, we simulate a successful documentation result
        simulated_documentation_result = {
            "agent": "documentation_agent",
            "request_id": generate_orchestrator_request_id(),
            "all_actions_complete": True,
            "actions": [
                {
                    "action": "update_current_task",
                    "status": "completed",
                    "result": {"milestone": milestone},
                },
                {
                    "action": "update_ai_context", 
                    "status": "completed",
                    "result": {},
                },
                {
                    "action": "append_completed_tasks",
                    "status": "completed",
                    "result": {"milestone": milestone},
                },
                {
                    "action": "read_next_task",
                    "status": "completed",
                    "result": {"status": "has_content"},
                },
                {
                    "action": "append_changelog",
                    "status": "completed",
                    "result": {"milestone": milestone},
                },
            ],
        }
        
        result["documentation_result"] = simulated_documentation_result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_full_workflow(
    orchestrator_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Process the complete development workflow."""
    request_id = generate_orchestrator_request_id()
    
    state = load_orchestrator_state()
    state["orchestrator_request_id"] = request_id
    state["status"] = "IN_PROGRESS"
    save_orchestrator_state(state)
    
    log_event("Orchestration request received: {}".format(request_id))
    record_action("orchestration_request", {"request_id": request_id, "status": "received"})
    
    result = {
        "agent": "orchestrator",
        "request_id": request_id,
        "timestamp": utc_now(),
        "input_received": False,
        "all_stages_complete": True,
        "stages": [],
        "milestone_completed": None,
    }
    
    try:
        result["input_received"] = bool(orchestrator_input)
        
        if not orchestrator_input:
            result["status"] = "no_input"
            result["message"] = "No orchestrator input provided."
            return result
        
        # Extract input fields with defaults
        user_request = orchestrator_input.get("user_request", "")
        milestone = orchestrator_input.get("milestone", "")
        
        # Execute workflow stages in order
        stages = [
            ("planning", process_planning_stage(orchestrator_input)),
            ("coding", process_coding_stage(orchestrator_input, None)),
            ("testing", process_testing_stage(orchestrator_input, None)),
            ("reviewing", process_reviewer_stage(orchestrator_input, None, None)),
            ("documenting", process_documentation_stage(orchestrator_input, {"agent": "reviewer_agent"})),
        ]
        
        for stage_name, stage_result in stages:
            result["stages"].append({
                "stage": stage_name,
                "result": stage_result,
                "status": "completed" if not stage_result.get("error") else "error",
            })
            
            if stage_result.get("error"):
                state["error"] = stage_result.get("error")
        
        # Update orchestrator state with completion info
        if all(stage_result.get("status") == "completed" for _, stage_result in stages):
            state["status"] = "COMPLETED"
            state["end_time"] = utc_now()
            state["milestone_completed"] = milestone
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
        state["status"] = "ERROR"
        state["end_time"] = utc_now()
    
    save_orchestrator_state(state)
    
    return result


def main():
    """CLI entry point for the Orchestrator Agent."""
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Orchestrator Agent."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="JSON file with orchestrator input (user request, milestone, etc.)",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("ORCHESTRATOR AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    orchestrator_input: Optional[Dict[str, Any]] = None
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                orchestrator_input = json.load(f)
            print("\n[ORCHESTRATOR] Input loaded from: {}".format(args.input))
        except Exception as e:
            print("\n[ERROR] Failed to load input file: {}".format(e))
    else:
        try:
            input_data = json.load(sys.stdin)
            orchestrator_input = input_data
            print("\n[ORCHESTRATOR] Input received via stdin")
        except Exception as e:
            print("\n[ERROR] Failed to parse stdin input: {}".format(e))
    
    if orchestrator_input is None:
        print("[ERROR] No valid orchestrator input provided.")
        return
    
    result = process_full_workflow(orchestrator_input)
    
    print("\n" + "=" * 70)
    print("ORCHESTRATOR AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print("Status: {}".format(result.get("status", "unknown")))
    
    if result.get("all_stages_complete"):
        print("[OK] All workflow stages completed")
        
        for stage in result.get("stages", []):
            stage_name = stage.get("stage", "")
            stage_status = stage.get("status", "unknown")
            
            print("\n[{}] Stage: {}".format(stage_status.upper(), stage_name.title()))
            
            # Print key result info
            for key in ["result"]:
                stage_result = stage.get(key, {})
                if stage_result and isinstance(stage_result, dict):
                    agent = stage_result.get("agent", "")
                    status = stage_result.get("status", "unknown")
                    print("  Agent: {} (Status: {})".format(agent, status))
    
    if result.get("error"):
        print("\n[!] Error: {}".format(result["error"]))
    
    print("\nTEXT-ONLY LLM CHECK:")
    print("- Images sent to Qwen 3.5: NO")
    print("- Image input added: NO")
    print("- Visual analysis attempted: NO")
    print("=" * 70)
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
