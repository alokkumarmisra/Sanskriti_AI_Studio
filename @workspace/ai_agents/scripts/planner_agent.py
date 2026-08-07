#!/usr/bin/env python3
"""
Planner Agent Runtime for Sanskriti AI Studio.

This runtime transforms high-level development requests into structured execution plans.
The Planner Agent:
1. Receives high-level development requests from Orchestrator
2. Reads project documentation for context
3. Breaks requests into granular tasks with dependencies
4. Assigns appropriate agents per task type
5. Generates acceptance criteria and complexity estimates

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
PLANNER_STATE_DIR = os.path.join(STATE_DIR, "planner")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
PLANNER_LOGS_DIR = os.path.join(LOGS_DIR, "planner")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_planner_request_id() -> str:
    """Generate a unique planner request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return "PLANNER-" + timestamp + "-" + unique_id


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
    """Append a timestamped event to the planner execution log."""
    os.makedirs(PLANNER_LOGS_DIR, exist_ok=True)
    timestamp = utc_now()
    log_entry = "[{}] [PLANNER] {}\n".format(timestamp, message)
    with open(os.path.join(PLANNER_LOGS_DIR, "execution.log"), "a", encoding="utf-8") as f:
        f.write(log_entry)


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append an action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "planner",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(os.path.join(STATE_DIR, "actions.jsonl"), "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_planner_state() -> Dict[str, Any]:
    """Load current planner task state."""
    state_path = os.path.join(PLANNER_STATE_DIR, "current_plan.json")
    return load_json_file(state_path) or {
        "planner_request_id": None,
        "task_id": None,
        "milestone": None,
        "original_user_request": None,
        "execution_plan": None,
        "status": "PENDING",
        "start_time": None,
        "end_time": None,
    }


def save_planner_state(state: Dict[str, Any]) -> None:
    """Persist planner task state."""
    os.makedirs(PLANNER_STATE_DIR, exist_ok=True)
    with open(os.path.join(PLANNER_STATE_DIR, "current_plan.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# --- Planning Workflow Functions -------------------------------------------

def read_project_state() -> Dict[str, Any]:
    """Read relevant project documentation to understand current state."""
    docs_to_read = [
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
        "docs/11_CHANGELOG.md",
    ]
    
    state = {
        "completed_milestones": [],
        "current_task": None,
        "next_task_hint": None,
    }
    
    # Check current task for active milestone
    current_task_content = load_text_file(os.path.join(WORKSPACE_ROOT, "docs", "06_CURRENT_TASK.md"))
    if current_task_content:
        lines = current_task_content.split("\n")
        for i, line in enumerate(lines):
            if "## Milestone" in line or "## STEP" in line:
                # Extract milestone number and status
                for j in range(i, min(i + 5, len(lines))):
                    if "Status:" in lines[j]:
                        status = lines[j].strip().split(":")[1].strip()
                        if "COMPLETED" not in status.upper():
                            state["current_task"] = {
                                "milestone": line.split("--")[0].strip(),
                                "status": status,
                            }
                        break
    
    # Check completed tasks for finished milestones
    completed_content = load_text_file(os.path.join(WORKSPACE_ROOT, "docs", "09_COMPLETED_TASKS.md"))
    if completed_content:
        state["completed_milestones"] = [
            m.strip() for m in completed_content.split("## Milestone")[-1].split("--")[0].split("\n") 
            if "Milestone" in m or "COMPLETED" in m
        ][:5]
    
    return state


def build_planning_prompt(
    request_id: str,
    user_request: str,
    project_state: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Build a text-only prompt for Qwen 3.5 planning assistance."""
    messages = []
    
    system_content = """You are the Planner Agent for Sanskriti AI Studio.
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.

Your responsibilities:
1. Read project documentation thoroughly
2. Understand current architecture and completed work
3. Break high-level requests into granular, executable subtasks
4. Identify task dependencies and execution order
5. Assign appropriate agents (documentation_agent, coding_agent, testing_agent) per task type
6. Define clear acceptance criteria for each subtask
7. Estimate complexity levels
8. Identify potential risks and blockers

Project State:
- Current Milestone: {current_milestone}
- Completed Milestones: {completed_list}
""".format(
        request_id=request_id,
        current_milestone=project_state.get("current_task", {}).get("milestone", "None"),
        completed_list=json.dumps(project_state.get("completed_milestones", []))
    )
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    messages.append({
        "role": "user",
        "content": user_request[:5000],  # Limit request to 5000 chars
    })
    
    return messages


def decompose_task(
    task_description: str,
    project_state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Decompose a high-level task into executable subtasks."""
    
    # Default agent assignments based on task type
    agent_map = {
        "documentation": "documentation_agent",
        "coding": "coding_agent", 
        "testing": "testing_agent",
    }
    
    # Default complexity levels
    complexity_map = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }
    
    # Generate subtasks based on description keywords
    subtasks = []
    description_lower = task_description.lower()
    
    if "workspace" in description_lower:
        subtasks.append({
            "task_id": "TASK-001",
            "description": "Create workspace route and layout",
            "agent": agent_map.get("coding", "coding_agent"),
            "dependencies": [],
            "acceptance_criteria": [
                "Workspace route is accessible at /project-workspace",
                "Layout includes project overview section",
                "Navigation to production sections works",
            ],
            "complexity": "medium",
        })
        
        subtasks.append({
            "task_id": "TASK-002", 
            "description": "Implement navigation components",
            "agent": agent_map.get("coding", "coding_agent"),
            "dependencies": ["TASK-001"],
            "acceptance_criteria": [
                "Navigation links work correctly",
                "Responsive design on all screen sizes",
            ],
            "complexity": "low",
        })
        
    elif "database" in description_lower:
        subtasks.append({
            "task_id": "TASK-001",
            "description": "Review database schema requirements",
            "agent": agent_map.get("documentation", "documentation_agent"),
            "dependencies": [],
            "acceptance_criteria": [
                "Schema documented in docs/03_DATABASE_DESIGN.md",
                "Models verified against migration history",
            ],
            "complexity": "low",
        })
        
    elif "api" in description_lower or "endpoint" in description_lower:
        subtasks.append({
            "task_id": "TASK-001",
            "description": "Define API contracts and schemas",
            "agent": agent_map.get("documentation", "documentation_agent"),
            "dependencies": [],
            "acceptance_criteria": [
                "API specification documented",
                "Pydantic schemas created",
                "Validation rules defined",
            ],
            "complexity": "medium",
        })
        
    else:
        # Default generic subtasks
        subtasks.append({
            "task_id": "TASK-001",
            "description": "Review requirements and documentation",
            "agent": agent_map.get("documentation", "documentation_agent"),
            "dependencies": [],
            "acceptance_criteria": [
                "Requirements understood",
                "Documentation reviewed",
            ],
            "complexity": "low",
        })
        
        subtasks.append({
            "task_id": "TASK-002",
            "description": "Implement core functionality",
            "agent": agent_map.get("coding", "coding_agent"),
            "dependencies": ["TASK-001"],
            "acceptance_criteria": [
                "Core implementation complete",
                "Code follows project conventions",
                "Existing tests pass",
            ],
            "complexity": "medium",
        })
        
        subtasks.append({
            "task_id": "TASK-003",
            "description": "Add tests for new functionality",
            "agent": agent_map.get("testing", "testing_agent"),
            "dependencies": ["TASK-002"],
            "acceptance_criteria": [
                "Unit tests written and passing",
                "Integration tests for API endpoints",
            ],
            "complexity": "low",
        })
    
    return subtasks


def generate_planning_plan(
    planner_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a structured execution plan for the development request."""
    result = {
        "agent": "planner_agent",
        "status": "processing",
        "timestamp": utc_now(),
        "input_received": False,
        "plan_generated": False,
        "error": None,
    }
    
    try:
        result["input_received"] = bool(planner_input)
        
        if not planner_input:
            result["status"] = "no_input"
            result["message"] = "No planning input provided."
            return result
        
        # Extract input fields with defaults
        request_id = planner_input.get("request_id") or generate_planner_request_id()
        user_request = planner_input.get("user_request", "")
        milestone = planner_input.get("milestone", "")
        
        # Read project state for context
        project_state = read_project_state()
        
        # Step 1: Build planning prompt
        messages = build_planning_prompt(
            request_id=request_id,
            user_request=user_request,
            project_state=project_state,
        )
        
        result["messages"] = messages
        
        # Step 2: Decompose task into subtasks (deterministic for now)
        plan_tasks = decompose_task(user_request, project_state)
        
        result["tasks"] = plan_tasks
        result["plan_structure"] = {
            "total_tasks": len(plan_tasks),
            "agent_distribution": {
                "coding_agent": sum(1 for t in plan_tasks if t.get("agent") == "coding_agent"),
                "testing_agent": sum(1 for t in plan_tasks if t.get("agent") == "testing_agent"),
                "documentation_agent": sum(1 for t in plan_tasks if t.get("agent") == "documentation_agent"),
            },
        }
        
        result["plan_generated"] = True
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = "{}: {}".format(type(e).__name__, str(e))
    
    return result


def process_planning_request(
    planner_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Process a planning request and return structured execution plan."""
    request_id = generate_planner_request_id()
    
    state = load_planner_state()
    state["planner_request_id"] = request_id
    state["status"] = "IN_PROGRESS"
    save_planner_state(state)
    
    log_event("Planning request received: {}".format(request_id))
    record_action("planning_request", {"request_id": request_id, "status": "received"})
    
    result = generate_planning_plan(planner_input)
    
    # Update state with result
    if result.get("plan_generated"):
        state["status"] = "COMPLETED"
        state["end_time"] = utc_now()
        state["execution_plan"] = result.get("tasks", [])
        
        # Extract milestone from input or plan tasks
        milestone = planner_input.get("milestone")
        if not milestone and result.get("tasks"):
            for task in result["tasks"]:
                if "TASK-001" in task.get("task_id", ""):
                    # Try to infer milestone from filename
                    file_path = task.get("file", "") or ""
                    parts = file_path.split("/")
                    if len(parts) > 0 and len(parts) < 5:
                        milestone = "Milestone " + "".join(p for p in parts if p.isdigit())
        
        state["milestone"] = milestone
    
    save_planner_state(state)
    
    return result


def main():
    """CLI entry point for the Planner Agent."""
    import sys
    
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Planner Agent."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="JSON file with planning input (user request, milestone, etc.)",
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("PLANNER AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    planner_input: Optional[Dict[str, Any]] = None
    
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                planner_input = json.load(f)
            print("\n[PLANNER] Input loaded from: {}".format(args.input))
        except Exception as e:
            print("\n[ERROR] Failed to load input file: {}".format(e))
    else:
        try:
            input_data = json.load(sys.stdin)
            planner_input = input_data
            print("\n[PLANNER] Input received via stdin")
        except Exception as e:
            print("\n[ERROR] Failed to parse stdin input: {}".format(e))
    
    if planner_input is None:
        print("[ERROR] No valid planning input provided.")
        return
    
    result = process_planning_request(planner_input)
    
    print("\n" + "=" * 70)
    print("PLANNER AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print("Status: {}".format(result["status"]))
    
    if result.get("plan_generated"):
        plan_tasks = result.get("tasks", [])
        print("[OK] Plan generated with {} tasks".format(len(plan_tasks)))
        
        print("\nTask Breakdown:")
        for task in plan_tasks:
            task_id = task.get("task_id", "")
            description = task.get("description", "")
            agent = task.get("agent", "")
            dependencies = task.get("dependencies", [])
            complexity = task.get("complexity", "")
            
            print("\n  Task: {}".format(task_id))
            print("    Description: {}".format(description))
            print("    Agent: {}".format(agent))
            print("    Dependencies: {}".format(", ".join(dependencies) if dependencies else "None"))
            print("    Complexity: {}".format(complexity))
        
        print("\nAgent Distribution:")
        for agent_type, count in result.get("plan_structure", {}).get("agent_distribution", {}).items():
            print("  - {}: {}".format(agent_type.replace("_", " ").title(), count))
    
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
