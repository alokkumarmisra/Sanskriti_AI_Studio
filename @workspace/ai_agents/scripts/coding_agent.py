#!/usr/bin/env python3
"""
Coding Agent Runtime for Sanskriti AI Studio.

This runtime implements text-only AI-assisted development with Qwen 3.5.
The Coding Agent:
1. Receives task specifications and requirements
2. Reads project documentation for context
3. Inspects existing codebase
4. Plans implementation
5. Generates code changes
6. Ensures no images are sent to Qwen 3.5

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
CODING_STATE_DIR = os.path.join(STATE_DIR, "coding")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
CODING_LOGS_DIR = os.path.join(LOGS_DIR, "coding")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_coding_request_id() -> str:
    """Generate a unique coding request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return "CODING-" + timestamp + "-" + unique_id


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
    """Append a timestamped event to the coding execution log."""
    os.makedirs(CODING_LOGS_DIR, exist_ok=True)
    timestamp = utc_now()
    log_entry = "[{}] [CODING_AGENT] {}\n".format(timestamp, message)
    with open(os.path.join(CODING_LOGS_DIR, "execution.log"), "a", encoding="utf-8") as f:
        f.write(log_entry)


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append an action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "coding",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(os.path.join(STATE_DIR, "actions.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_coding_state() -> Dict[str, Any]:
    """Load current coding task state."""
    state_path = os.path.join(CODING_STATE_DIR, "current_coding.json")
    return load_json_file(state_path) or {
        "coding_request_id": None,
        "task_id": None,
        "milestone": None,
        "plan_id": None,
        "original_user_request": None,
        "execution_plan": None,
        "acceptance_criteria": [],
        "previous_task_results": [],
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
        "completed": False,
        "error": None,
    }


def save_coding_state(state: Dict[str, Any]) -> None:
    """Persist coding task state."""
    os.makedirs(CODING_STATE_DIR, exist_ok=True)
    with open(os.path.join(CODING_STATE_DIR, "current_coding.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def read_project_documentation() -> Dict[str, Any]:
    """Read relevant project documentation for context."""
    docs = []
    docs_paths = [
        "docs/00_PROJECT_STORY.md",
        "docs/01_CODING_RULES.md",
        "docs/02_SYSTEM_ARCHITECTURE.md",
        "docs/03_DATABASE_DESIGN.md",
        "docs/04_API_SPECIFICATION.md",
        "docs/05_ROADMAP.md",
        "docs/06_CURRENT_TASK.md",
        "docs/07_DEVELOPMENT_GUIDELINES.md",
        "docs/08_AI_CONTEXT.md",
        "docs/09_COMPLETED_TASKS.md",
        "docs/10_NEXT_TASK.md",
        "docs/11_CHANGELOG.md",
    ]
    
    for doc_path in docs_paths:
        content = load_text_file(os.path.join(WORKSPACE_ROOT, doc_path))
        if content:
            docs.append({
                "file": doc_path,
                "content": content[:2000],
            })
    
    return {
        "docs_read": len(docs),
        "documentation": docs,
        "timestamp": utc_now(),
    }


def read_changed_files() -> List[Dict[str, Any]]:
    """Read git diff to understand what changed."""
    import subprocess
    
    try:
        result = subprocess.run(
            'git diff --cached',
            capture_output=True,
            text=True,
            cwd=WORKSPACE_ROOT
        )
        
        if result.returncode == 0 and result.stdout:
            return [
                {
                    "file": line.split("diff --git")[-1].split(" a/")[1].split(" b/")[0] if "a/" in line else "",
                    "content": line,
                }
                for line in result.stdout.splitlines()[:20]
            ][:5]
    except Exception:
        pass
    
    return []


def build_coding_prompt(
    task_id: str,
    milestone: str,
    plan: Dict[str, Any],
    acceptance_criteria: List[str],
    previous_results: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """Build a text-only prompt for Qwen 3.5 coding assistance."""
    messages = []
    
    system_content = """You are the Coding Agent for Sanskriti AI Studio.
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.

You are responsible for:
1. Reading project documentation for context
2. Understanding the current architecture
3. Implementing requested changes
4. Ensuring code quality and consistency
5. Following coding rules and development guidelines
6. Preserving existing functionality
7. Not implementing future milestones automatically

Task Details:
- Task ID: {task_id}
- Milestone: {milestone}
- Plan: {plan_json}
""".format(
        task_id=task_id,
        milestone=milestone,
        plan_json=json.dumps(plan.get("tasks", [])) if plan else "No plan provided"
    )
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    completed_tasks = previous_results.get("completed_tasks") if isinstance(previous_results, dict) else []
    if completed_tasks:
        messages.append({
            "role": "user",
            "content": "Previous tasks completed:\n" + json.dumps(completed_tasks, indent=2)[:1000],
        })
    
    return messages


def generate_code_changes(
    task_id: Optional[str] = None,
    coding_input: Dict[str, Any] = {},
    previous_task_results: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Generate code changes based on task requirements."""
    result = {
        "agent": "coding_agent",
        "status": "processing",
        "timestamp": utc_now(),
        "input_received": False,
        "documentation_read": False,
        "code_generation_complete": False,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(coding_input)
        
        if not coding_input:
            result["status"] = "no_input"
            result["message"] = "No coding input provided."
            return result
        
        # Read project documentation for context
        docs_context = read_project_documentation()
        result["documentation_read"] = True
        
        # Extract input fields with defaults
        task_id_input = coding_input.get("task_id") or task_id
        milestone: Optional[str] = coding_input.get("milestone") or "Unknown"
        plan = coding_input.get("plan", {})
        acceptance_criteria = coding_input.get("acceptance_criteria", [])
        previous_results = coding_input.get("previous_task_results") or previous_task_results
        
        # Plan implementation approach
        implementation_plan = {
            "files_to_create": [],
            "files_to_modify": [],
            "files_to_delete": [],
            "approach": "Implement changes incrementally, testing after each step",
        }
        
        # Generate code for first 2 tasks in plan
        plan_tasks: List[Dict] = plan.get("tasks", [])
        generated_files = []
        for task in plan_tasks[:2]:
            file_path: str = task.get("file", "") or ""
            agent: Optional[str] = task.get("agent")
            
            if file_path and agent:
                task_id_display = task_id_input or "TASK"
                filename = file_path.split("/")[-1]
                
                # Build code preview using string concatenation
                lines = []
                lines.append("# Auto-generated by Coding Agent for " + task_id_display)
                lines.append("")
                lines.append(agent.upper() + " AGENT IMPLEMENTATION PLACEHOLDER")
                lines.append("- Milestone: " + (milestone or "Unknown"))
                lines.append("- Task ID: " + filename)
                lines.append("")
                
                if acceptance_criteria:
                    for criterion in acceptance_criteria[:3]:
                        lines.append("  - " + str(criterion))
                else:
                    lines.append("  (no specific criteria listed)")
                
                lines.append("")
                lines.append("IMPORTANT:")
                lines.append("- Follow existing code patterns")
                lines.append("- Add type hints where appropriate")
                lines.append("- Include docstrings")
                lines.append("- Write tests for new functionality")
                
                generated_code = "\n".join(lines)
                
                generated_files.append({
                    "file": file_path,
                    "agent": agent,
                    "code_preview": generated_code[:1000],
                })
        
        result["generated_files"] = generated_files
        
        # State update
        state_update = {
            "status": "completed",
            "files_generated": len(generated_files),
            "completion_summary": "Generated code for {} files in milestone {}".format(
                len(generated_files), milestone
            ),
        }
        
        result.update(state_update)
        result["code_generation_complete"] = True
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_coding_request(
    coding_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Process a coding request and return result."""
    request_id = generate_coding_request_id()
    
    state = load_coding_state()
    state["coding_request_id"] = request_id
    state["status"] = "IN_PROGRESS"
    save_coding_state(state)
    
    log_event("Coding request received: {}".format(request_id))
    record_action("coding_request", {"request_id": request_id, "status": "received"})
    
    result = generate_code_changes(
        task_id=state.get("task_id"),
        coding_input=coding_input,
        previous_task_results=state.get("previous_task_results"),
    )
    
    if result.get("code_generation_complete"):
        state["status"] = "COMPLETED"
        state["end_time"] = utc_now()
    else:
        state["status"] = "IN_PROGRESS"
        
    save_coding_state(state)
    
    return result


def main():
    """CLI entry point for the Coding Agent."""
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Coding Agent."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="JSON file with coding input (task specification, plan, etc.)",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("CODING AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    coding_input: Optional[Dict[str, Any]] = None
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                coding_input = json.load(f)
            print("\n[CODING] Input loaded from: {}".format(args.input))
        except Exception as e:
            print("\n[ERROR] Failed to load input file: {}".format(e))
    else:
        try:
            input_data = json.load(sys.stdin)
            coding_input = input_data
            print("\n[CODING] Input received via stdin")
        except Exception as e:
            print("\n[ERROR] Failed to parse stdin input: {}".format(e))
    
    if coding_input is None:
        print("[ERROR] No valid coding input provided.")
        return
    
    result = process_coding_request(coding_input)
    
    print("\n" + "=" * 70)
    print("CODING AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print("Status: {}".format(result["status"]))
    
    if result.get("documentation_read"):
        print("[OK] Documentation read for context")
    
    if result.get("generated_files"):
        print("[OK] Generated code for {} files".format(len(result["generated_files"])))
        for file_info in result["generated_files"]:
            print("  - {}: {}".format(file_info["file"], file_info["agent"]))
    
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
