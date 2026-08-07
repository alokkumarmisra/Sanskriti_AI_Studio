#!/usr/bin/env python3
"""
Milestone Execution Manager for Sanskriti AI Studio.

This module manages milestone execution by:
1. Loading execution plans from the Planner Agent
2. Orchestrating agent workflows for each task
3. Managing state and progress tracking
4. Handling failures and retries
5. Generating execution reports

CRITICAL: Qwen 3.5 is TEXT-ONLY. This manager never sends images or visual data.

Version: 1.0
Last Updated: 2026-08-05
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


class MilestoneExecutionManager:
    """Milestone Execution Manager for Sanskriti AI Studio."""

    def __init__(self):
        """Initialize the milestone execution manager."""
        self.workspace_root = WORKSPACE_ROOT
        self.ai_agents_root = AI_AGENTS_ROOT
        self.state_dir = os.path.join(AI_AGENTS_ROOT, "state")
        self.logs_dir = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
        self.milestones_dir = os.path.join(self.state_dir, "milestones")
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_execution_plan(self, plan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load an execution plan from state."""
        if not plan_id:
            # Try to find the most recent plan
            plan_path = os.path.join(self.milestones_dir, "current_plan.json")
            if os.path.exists(plan_path):
                try:
                    with open(plan_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            return None
        
        plan_path = os.path.join(self.milestones_dir, f"plan_{plan_id}.json")
        if os.path.exists(plan_path):
            try:
                with open(plan_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None

    def save_execution_plan(self, plan: Dict[str, Any], plan_id: Optional[str] = None) -> str:
        """Save an execution plan to state."""
        if not plan_id:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            plan_id = f"PLAN-{timestamp}"
        
        plan_path = os.path.join(self.milestones_dir, f"plan_{plan_id}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, default=str)
        
        return plan_id

    def load_orchestrator_state(self) -> Optional[Dict[str, Any]]:
        """Load orchestrator state for task coordination."""
        state_path = os.path.join(self.milestones_dir, "orchestrator_state.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save_orchestrator_state(self, state: Dict[str, Any]) -> None:
        """Save orchestrator state."""
        os.makedirs(self.milestones_dir, exist_ok=True)
        with open(os.path.join(self.milestones_dir, "orchestrator_state.json"), "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

    def get_available_agents(self) -> List[str]:
        """Get list of available agents for execution."""
        agents = []
        
        # Core development agents
        agent_files = [
            ("coder_agent", "ai_agents/scripts/coder_agent.py"),
            ("tester_agent", "ai_agents/scripts/tester_agent.py"),
            ("debugger_agent", "ai_agents/scripts/debugger_agent.py"),
            ("reviewer_agent", "ai_agents/scripts/reviewer_agent.py"),
            ("documentation_agent", "ai_agents/agents/documentation_agent.py"),
        ]
        
        for name, path in agent_files:
            full_path = os.path.join(self.workspace_root, path)
            if os.path.exists(full_path):
                agents.append(name)
        
        # Orchestration agents
        if os.path.exists(os.path.join(self.workspace_root, "ai_agents/scripts/orchestrator.py")):
            agents.append("orchestrator")
        if os.path.exists(os.path.join(self.workspace_root, "ai_agents/scripts/planner_agent.py")):
            agents.append("planner_agent")
        
        return agents

    def execute_task_sequence(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sequence of tasks from an execution plan."""
        task_id = plan.get("plan_id", "unknown")
        request = plan.get("request", "No request provided")
        
        print("=" * 70)
        print("MILESTONE EXECUTION MANAGER - Sanskriti AI Studio")
        print("=" * 70)
        print(f"Plan ID: {task_id}")
        print(f"Request: {request[:200]}...")
        print("=" * 70)
        
        available_agents = self.get_available_agents()
        missing_agents = set(t.get("agent", "") for t in plan.get("tasks", [])).difference(available_agents)
        
        if missing_agents:
            print(f"\n[!] Missing agents: {', '.join(missing_agents)}")
            print("\nAvailable agents:")
            for agent in available_agents:
                print(f"  - {agent}")
            return {
                "status": "BLOCKED",
                "task_id": task_id,
                "error": f"Missing required agents: {', '.join(missing_agents)}",
            }
        
        # Save orchestrator state
        self.save_orchestrator_state({
            "plan_id": task_id,
            "request": request,
            "tasks_completed": [],
            "tasks_failed": [],
            "status": "IN_PROGRESS",
            "timestamp": utc_now(),
        })
        
        # Execute tasks in order
        for i, task in enumerate(plan.get("tasks", [])):
            task_id = task.get("task_id")
            title = task.get("title", f"Task {i+1}")
            agent = task.get("agent", "unknown")
            
            print(f"\n--- Executing Task {i+1} ---")
            print(f"  Task ID: {task_id}")
            print(f"  Title: {title}")
            print(f"  Agent: {agent}")
            
            # Skip completed tasks
            if task.get("status") == "completed":
                print(f"  [SKIP] Task already completed")
                continue
            
            # Check dependencies
            deps = task.get("dependencies", [])
            if deps:
                missing_deps = [d for d in deps if d not in self.milestones_dir.replace("milestones", "") + "/"]
                if missing_deps:
                    print(f"  [SKIP] Missing dependencies: {missing_deps}")
                    continue
            
            # Execute agent (placeholder - actual execution done by orchestrator)
            task_result = {
                "task_id": task_id,
                "title": title,
                "agent": agent,
                "status": "PENDING",  # Will be updated by orchestrator
                "execution_order": i + 1,
            }
            
            # Fixed: Load existing state first to avoid unpacking None
            loaded_state = self.load_orchestrator_state() or {}
            state_to_save = {
                **loaded_state,
                "tasks_completed": [t["task_id"] for t in plan.get("tasks", []) if t.get("status") == "completed"],
                "tasks_failed": [t["task_id"] for t in plan.get("tasks", []) if t.get("status") in ["FAILED", "REJECTED"]],
            }
            self.save_orchestrator_state(state_to_save)
        
        # Save final state
        self.save_orchestrator_state({
            "plan_id": task_id,
            "request": request,
            "tasks_completed": [],  # Will be populated by orchestrator
            "tasks_failed": [],
            "status": "READY_FOR_EXECUTION",
            "timestamp": utc_now(),
        })
        
        return {
            "status": "READY",
            "task_id": task_id,
            "message": f"Plan {task_id} is ready for execution. Use Orchestrator Agent to run tasks.",
        }

    def generate_execution_report(self, plan: Dict[str, Any], result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a report for milestone execution."""
        plan_id = plan.get("plan_id", "unknown")
        
        state = self.load_orchestrator_state() or {}
        
        report = {
            "report_type": "milestone_execution",
            "plan_id": plan_id,
            "timestamp": utc_now(),
            "status": result.get("status", "UNKNOWN") if result else "NOT_EXECUTED",
            "tasks": [
                {
                    "task_id": t.get("task_id"),
                    "title": t.get("title"),
                    "agent": t.get("agent"),
                    "status": t.get("status", "PENDING"),
                    "accepted_criteria": t.get("acceptance_criteria", []),
                }
                for t in plan.get("tasks", [])
            ],
            "state_summary": {
                "total_tasks": len(plan.get("tasks", [])),
                "completed_tasks": len(state.get("tasks_completed", [])),
                "failed_tasks": len(state.get("tasks_failed", [])),
            },
        }
        
        return report

    def bootstrap(self) -> Dict[str, Any]:
        """Execute the milestone execution manager bootstrap."""
        print("=" * 70)
        print("MILESTONE EXECUTION MANAGER BOOTSTRAP")
        print("=" * 70)
        
        # Ensure directories exist
        os.makedirs(self.milestones_dir, exist_ok=True)
        print(f"[OK] Milestones directory: {self.milestones_dir}")
        
        # Check available agents
        available_agents = self.get_available_agents()
        print(f"\n[OK] Available agents: {', '.join(available_agents)}")
        
        # Load any existing plan
        existing_plan = self.load_execution_plan()
        if existing_plan:
            print(f"[OK] Existing plan found: {existing_plan.get('plan_id')}")
        else:
            print("[!] No existing execution plan found. Use Orchestrator Agent to create a plan.")
        
        # Generate initial report
        report = self.generate_execution_report({"plan_id": "INITIAL"})
        
        return {
            "success": True,
            "available_agents": available_agents,
            "existing_plan": existing_plan is not None,
            "report": report,
        }


def main() -> None:
    """CLI entry point for the Milestone Execution Manager."""
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Milestone Execution Manager."
    )
    parser.add_argument(
        "--plan",
        type=str,
        help="Plan ID to execute (optional)",
    )
    args = parser.parse_args()

    manager = MilestoneExecutionManager()
    result = manager.bootstrap()

    print("\n" + "=" * 70)
    if result["success"]:
        print("MILESTONE EXECUTION MANAGER BOOTSTRAP COMPLETE")
        print("=" * 70)
    else:
        print("MILESTONE EXECUTION MANAGER BOOTSTRAP FAILED")
        print("=" * 70)


if __name__ == "__main__":
    main()
