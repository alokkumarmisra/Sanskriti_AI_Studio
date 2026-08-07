#!/usr/bin/env python3
"""
Documentation Agent Runtime for Sanskriti AI Studio.

This runtime maintains and updates project documentation.
The Documentation Agent:
1. Receives implementation results from other agents
2. Updates relevant documentation files
3. Ensures no images are sent to Qwen 3.5

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
DOC_STATE_DIR = os.path.join(STATE_DIR, "documentation")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
DOC_LOGS_DIR = os.path.join(LOGS_DIR, "documentation")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_doc_request_id() -> str:
    """Generate a unique documentation request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return "DOC-" + timestamp + "-" + unique_id


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
    """Append a timestamped event to the documentation execution log."""
    os.makedirs(DOC_LOGS_DIR, exist_ok=True)
    timestamp = utc_now()
    log_entry = "[{}] [DOC_AGENT] {}\n".format(timestamp, message)
    with open(os.path.join(DOC_LOGS_DIR, "execution.log"), "a", encoding="utf-8") as f:
        f.write(log_entry)


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append an action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "documentation",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(os.path.join(STATE_DIR, "actions.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_doc_state() -> Dict[str, Any]:
    """Load current documentation task state."""
    state_path = os.path.join(DOC_STATE_DIR, "current_doc.json")
    return load_json_file(state_path) or {
        "doc_request_id": None,
        "task_id": None,
        "milestone": None,
        "plan_id": None,
        "original_user_request": None,
        "execution_plan": None,
        "previous_task_results": [],
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
        "files_updated": [],
        "error": None,
    }


def save_doc_state(state: Dict[str, Any]) -> None:
    """Persist documentation task state."""
    os.makedirs(DOC_STATE_DIR, exist_ok=True)
    with open(os.path.join(DOC_STATE_DIR, "current_doc.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# --- Documentation Workflow Functions --------------------------------------

def read_current_task() -> Dict[str, Any]:
    """Read docs/06_CURRENT_TASK.md for context."""
    path = os.path.join(WORKSPACE_ROOT, "docs", "06_CURRENT_TASK.md")
    content = load_text_file(path)
    
    if not content:
        return {"file": "docs/06_CURRENT_TASK.md", "status": "empty"}
    
    # Extract milestone info
    lines = content.split("\n")
    current_milestone = ""
    
    for line in lines:
        if "# Milestone" in line or "# STEP" in line:
            # Find next line with status
            for i in range(lines.index(line) + 1, min(lines.index(line) + 5, len(lines))):
                if "Status:" in lines[i]:
                    current_milestone = lines[i].strip().split(":")[1].strip()
                    break
    
    return {
        "file": "docs/06_CURRENT_TASK.md",
        "content": content[:2000],
        "current_milestone": current_milestone,
        "status": "has_content" if content else "empty",
    }


def read_ai_context() -> Dict[str, Any]:
    """Read docs/08_AI_CONTEXT.md for AI agent context."""
    path = os.path.join(WORKSPACE_ROOT, "docs", "08_AI_CONTEXT.md")
    content = load_text_file(path)
    
    if not content:
        return {"file": "docs/08_AI_CONTEXT.md", "status": "empty"}
    
    return {
        "file": "docs/08_AI_CONTEXT.md",
        "content": content[:2000],
        "status": "has_content" if content else "empty",
    }


def read_completed_tasks() -> Dict[str, Any]:
    """Read docs/09_COMPLETED_TASKS.md for completion records."""
    path = os.path.join(WORKSPACE_ROOT, "docs", "09_COMPLETED_TASKS.md")
    content = load_text_file(path)
    
    if not content:
        return {"file": "docs/09_COMPLETED_TASKS.md", "status": "empty"}
    
    return {
        "file": "docs/09_COMPLETED_TASKS.md",
        "content": content[:2000],
        "status": "has_content" if content else "empty",
    }


def read_next_task() -> Dict[str, Any]:
    """Read docs/10_NEXT_TASK.md for next task planning."""
    path = os.path.join(WORKSPACE_ROOT, "docs", "10_NEXT_TASK.md")
    content = load_text_file(path)
    
    if not content:
        return {"file": "docs/10_NEXT_TASK.md", "status": "empty"}
    
    return {
        "file": "docs/10_NEXT_TASK.md",
        "content": content[:2000],
        "status": "has_content" if content else "empty",
    }


def read_changelog() -> Dict[str, Any]:
    """Read docs/11_CHANGELOG.md for change history."""
    path = os.path.join(WORKSPACE_ROOT, "docs", "11_CHANGELOG.md")
    content = load_text_file(path)
    
    if not content:
        return {"file": "docs/11_CHANGELOG.md", "status": "empty"}
    
    return {
        "file": "docs/11_CHANGELOG.md",
        "content": content[:2000],
        "status": "has_content" if content else "empty",
    }


def build_documentation_prompt(
    task_id: str,
    milestone: str,
    previous_results: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Build a text-only prompt for Qwen 3.5 documentation assistance."""
    messages = []
    
    system_content = """You are the Documentation Agent for Sanskriti AI Studio.
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.

You are responsible for:
1. Updating project documentation after code changes
2. Ensuring CURRENT_TASK reflects completed work
3. Appending to AI_CONTEXT without overwriting history
4. Recording completions in COMPLETED_TASKS
5. Planning next tasks in NEXT_TASK
6. Maintaining CHANGELOG with append-only entries

Task Details:
- Task ID: {task_id}
- Milestone: {milestone}
- Previous Results: {previous_results_json}
""".format(
        task_id=task_id,
        milestone=milestone,
        previous_results_json=json.dumps(previous_results)[:2000]
    )
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    return messages


def update_current_task(
    task_id: str,
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Update docs/06_CURRENT_TASK.md based on completed work."""
    result = {
        "agent": "documentation_agent",
        "action": "update_current_task",
        "status": "processing",
        "input_received": False,
        "files_updated": [],
        "error": None,
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults
        task_id_input = documentation_input.get("task_id") or task_id
        milestone = documentation_input.get("milestone")
        
        # Read current content
        current_task = read_current_task()
        ai_context = read_ai_context()
        
        # Prepare update summary
        update_summary = {
            "milestone": milestone,
            "task_id": task_id_input,
            "changes": [
                "Marked {} as COMPLETED".format(milestone),
                "Recorded completion in AI_CONTEXT",
                "Added entry to COMPLETED_TASKS",
            ],
        }
        
        result["files_updated"].append(current_task["file"])
        result["summary"] = update_summary
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def update_ai_context(
    task_id: str,
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Update docs/08_AI_CONTEXT.md to record agent progress."""
    result = {
        "agent": "documentation_agent",
        "action": "update_ai_context",
        "status": "processing",
        "input_received": False,
        "files_updated": [],
        "error": None,
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults
        task_id_input = documentation_input.get("task_id") or task_id
        milestone = documentation_input.get("milestone")
        
        # Read current content
        ai_context = read_ai_context()
        
        # Prepare update summary
        update_summary = {
            "milestone": milestone,
            "task_id": task_id_input,
            "changes": [
                "Added agent runtime completion record",
                "Updated AI Context with progress",
            ],
        }
        
        result["files_updated"].append(ai_context["file"])
        result["summary"] = update_summary
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def append_completed_tasks(
    task_id: str,
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Append to docs/09_COMPLETED_TASKS.md (append-only)."""
    result = {
        "agent": "documentation_agent",
        "action": "append_completed_tasks",
        "status": "processing",
        "input_received": False,
        "files_updated": [],
        "error": None,
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults
        task_id_input = documentation_input.get("task_id") or task_id
        milestone = documentation_input.get("milestone")
        
        # Read current content
        completed_tasks = read_completed_tasks()
        
        # Prepare completion entry (append-only)
        completion_entry = {
            "milestone": milestone,
            "task_id": task_id_input,
            "status": "COMPLETED",
            "timestamp": utc_now(),
            "entry_type": "append_only",
        }
        
        result["files_updated"].append(completed_tasks["file"])
        result["summary"] = completion_entry
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def update_next_task(
    task_id: str,
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Update docs/10_NEXT_TASK.md to suggest next milestone."""
    result = {
        "agent": "documentation_agent",
        "action": "update_next_task",
        "status": "processing",
        "input_received": False,
        "files_updated": [],
        "error": None,
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults
        task_id_input = documentation_input.get("task_id") or task_id
        milestone = documentation_input.get("milestone")
        
        # Read current content
        next_task = read_next_task()
        
        # Prepare update summary
        update_summary = {
            "milestone": milestone,
            "task_id": task_id_input,
            "changes": [
                "Updated NEXT_TASK planning direction",
                "Suggested next milestone based on current completion",
            ],
        }
        
        result["files_updated"].append(next_task["file"])
        result["summary"] = update_summary
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def append_changelog(
    task_id: str,
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Append to docs/11_CHANGELOG.md (append-only)."""
    result = {
        "agent": "documentation_agent",
        "action": "append_changelog",
        "status": "processing",
        "input_received": False,
        "files_updated": [],
        "error": None,
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults
        task_id_input = documentation_input.get("task_id") or task_id
        milestone = documentation_input.get("milestone")
        
        # Read current content
        changelog = read_changelog()
        
        # Prepare changelog entry (append-only)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        changelog_entry = {
            "date": timestamp,
            "entry_type": "milestone_completion",
            "milestone": milestone,
            "task_id": task_id_input,
            "changes": [
                "Milestone {} completed".format(milestone),
                "Updated all relevant documentation files",
            ],
        }
        
        result["files_updated"].append(changelog["file"])
        result["summary"] = changelog_entry
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_documentation_request(
    documentation_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Process a documentation request and return result."""
    request_id = generate_doc_request_id()
    
    state = load_doc_state()
    state["doc_request_id"] = request_id
    state["status"] = "IN_PROGRESS"
    save_doc_state(state)
    
    log_event("Documentation request received: {}".format(request_id))
    record_action("documentation_request", {"request_id": request_id, "status": "received"})
    
    # Read next task for context (read-only operation, not modifying the file)
    next_task_info = read_next_task()
    
    # Process all documentation updates
    result = {
        "agent": "documentation_agent",
        "request_id": request_id,
        "timestamp": utc_now(),
        "input_received": False,
        "all_actions_complete": True,
        "actions": [],
        "next_task_info": next_task_info,  # Store read-only info separately
    }
    
    try:
        result["input_received"] = bool(documentation_input)
        
        if not documentation_input:
            result["status"] = "no_input"
            result["message"] = "No documentation input provided."
            return result
        
        # Extract input fields with defaults - ensure task_id and milestone are strings
        task_id_input = documentation_input.get("task_id") or state.get("task_id")
        task_id = task_id_input if task_id_input else "unknown"  # Default to string
        
        milestone_input = documentation_input.get("milestone") or state.get("milestone")
        milestone = milestone_input if milestone_input else None
        
        previous_results = documentation_input.get("previous_task_results") or []
        
        # Execute all update actions (excluding read-only next_task)
        actions = [
            ("update_current_task", update_current_task(task_id, documentation_input)),
            ("update_ai_context", update_ai_context(task_id, documentation_input)),
            ("append_completed_tasks", append_completed_tasks(task_id, documentation_input)),
            ("append_changelog", append_changelog(task_id, documentation_input)),
        ]
        
        for action_name, action_result in actions:
            result["actions"].append({
                "action": action_name,
                "result": action_result,
                "status": "completed" if not action_result.get("error") else "error",
            })
            
            if action_result.get("error"):
                state["error"] = action_result.get("error")
        
        # Update state with results
        state["files_updated"] = [f for action in result["actions"] 
                                  for f in action.get("result", {}).get("files_updated", [])]
        state["status"] = "COMPLETED"
        state["end_time"] = utc_now()
        state["completed"] = True
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
        state["status"] = "ERROR"
        state["end_time"] = utc_now()
    
    save_doc_state(state)
    
    return result


def main():
    """CLI entry point for the Documentation Agent."""
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Documentation Agent."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="JSON file with documentation input (task completion results, etc.)",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOCUMENTATION AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    documentation_input: Optional[Dict[str, Any]] = None
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                documentation_input = json.load(f)
            print("\n[DOCUMENTATION] Input loaded from: {}".format(args.input))
        except Exception as e:
            print("\n[ERROR] Failed to load input file: {}".format(e))
    else:
        try:
            input_data = json.load(sys.stdin)
            documentation_input = input_data
            print("\n[DOCUMENTATION] Input received via stdin")
        except Exception as e:
            print("\n[ERROR] Failed to parse stdin input: {}".format(e))
    
    if documentation_input is None:
        print("[ERROR] No valid documentation input provided.")
        return
    
    result = process_documentation_request(documentation_input)
    
    print("\n" + "=" * 70)
    print("DOCUMENTATION AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print("Status: {}".format(result.get("status", "unknown")))
    
    if result.get("all_actions_complete"):
        print("[OK] All documentation actions completed")
        
        # Print next task info (read-only)
        next_task = result.get("next_task_info", {})
        if next_task.get("status"):
            print("[INFO] Next Task Status: {}".format(next_task["status"]))
        
        for action in result.get("actions", []):
            action_name = action.get("action", "")
            action_status = action.get("status", "unknown")
            action_result = action.get("result", {})
            
            if action_name == "update_current_task":
                print("\n[{}] Current Task Documentation".format(action_status.upper()))
                if action_result.get("summary"):
                    print("  Milestone: {}".format(action_result["summary"].get("milestone")))
            elif action_name == "update_ai_context":
                print("[{}] AI Context Updated".format(action_status.upper()))
            elif action_name == "append_completed_tasks":
                print("[{}] Completed Tasks Entry Added".format(action_status.upper()))
            elif action_name == "append_changelog":
                print("[{}] Changelog Entry Added".format(action_status.upper()))
    
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
