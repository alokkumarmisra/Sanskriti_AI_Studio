#!/usr/bin/env python3
"""
Self-Healing Development Loop Controller for Sanskriti AI Studio.

This controller implements an autonomous execution loop that continuously attempts to fix
implementation issues until the project passes all validation or reaches a configurable retry limit.

PHASES:
Phase 1 — LOOP CONTROLLER: Start execution, Monitor state, Track retry count, Stop on success/failure
Phase 2 — LOOP FLOW: Planner -> Coding -> Testing -> Vision -> UI Validation -> Reviewer (PASS/FAIL)
Phase 3 — RETRY POLICY: Configurable retries with exponential backoff
Phase 4 — FAILURE ANALYSIS: Categorize and track all failure types
Phase 5 — LOOP HISTORY: Persist execution state and history
Phase 6 — RECOVERY: Support recovery from various failure scenarios
Phase 7 — REVIEWER INTEGRATION: Final PASS/FAIL decision based on Reviewer Agent
Phase 8 — DOCUMENTATION: Update architecture docs

CRITICAL: Qwen 3.5 is TEXT-ONLY - This controller never sends images or visual data.

Version: 1.0
Last Updated: 2026-08-07 (STEP 23.8)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
LOOP_STATE_DIR = os.path.join(STATE_DIR, "loop")
EXECUTION_ID_FILE = os.path.join(LOOP_STATE_DIR, "current_execution_id.txt")
LOOP_STATUS_PATH = os.path.join(LOOP_STATE_DIR, "loop_status.json")

# Retry policy configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 30  # seconds


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_execution_id() -> str:
    """Generate a unique execution ID for this loop run."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    return f"LOOP-{timestamp}-{unique_id}"


def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON object from disk."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data.setdefault("_source", path)
            return data
        return {"value": data, "_source": path}
    except Exception as e:
        print(f"[LOOP] Error loading {path}: {e}")
        return None


def save_json_file(path: str, data: Dict[str, Any]) -> bool:
    """Save a JSON object to disk."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[LOOP] Error saving {path}: {e}")
        return False


def run_agent_command(agent_path: str) -> Dict[str, Any]:
    """Execute an agent script and return the result."""
    import subprocess
    
    start_time = datetime.now(timezone.utc)
    result = {"stage": os.path.basename(agent_path), "status": "running", "duration_ms": 0}
    
    try:
        proc = subprocess.run(
            ["python", agent_path],
            capture_output=True, text=True, timeout=600, cwd=WORKSPACE_ROOT
        )
        
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout[:2000] if proc.stdout else ""
        result["stderr"] = proc.stderr[:2000] if proc.stderr else ""
        
        if proc.returncode == 0:
            result["status"] = "executed"
        else:
            error_msg = proc.stderr[:500] if proc.stderr else proc.stdout[:500]
            result["error_message"] = error_msg or "Unknown error"
            result["status"] = "failed"
            
    except subprocess.TimeoutExpired as e:
        result["status"] = "timeout"
        result["error_message"] = f"Process timed out after 600 seconds"
        
    except Exception as e:
        result["status"] = "exception"
        result["error_message"] = str(e)[:500]
    
    end_time = datetime.now(timezone.utc)
    duration_ms = (end_time - start_time).total_seconds() * 1000
    result["duration_ms"] = int(duration_ms)
    result["timestamp"] = utc_now()
    
    return result


class LoopController:
    """Self-Healing Development Loop Controller."""
    
    def __init__(self):
        self.workspace_root = WORKSPACE_ROOT
        self.state_dir = STATE_DIR
        self.loop_state_dir = LOOP_STATE_DIR
        
        # Load execution ID
        exec_id_path = EXECUTION_ID_FILE
        data = load_json_file(exec_id_path)
        if data and "execution_id" in data:
            self.execution_id = data["execution_id"]
        else:
            self.execution_id = generate_execution_id()
            save_json_file(exec_id_path, {"execution_id": self.execution_id})
        
        # Default retry policy (can be overridden via config file)
        self.max_retries = DEFAULT_MAX_RETRIES
        self.retry_delay = DEFAULT_RETRY_DELAY
        
        print(f"[LOOP] Execution ID: {self.execution_id}")
        print(f"[LOOP] Max retries: {self.max_retries}")
        print(f"[LOOP] Retry delay: {self.retry_delay}s")
    
    def _log(self, message: str) -> None:
        """Print log message with timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{timestamp}] [LOOP-{self.execution_id[:8]}] {message}")
    
    def run_workflow_stage(self, agent_name: str, agent_path: str) -> Dict[str, Any]:
        """Run a single workflow stage (agent execution)."""
        self._log(f"Starting stage: {agent_name}")
        
        start_time = datetime.now(timezone.utc)
        result = {"stage": agent_name, "status": "executing", "duration_ms": 0}
        
        try:
            # Execute the agent
            subprocess_result = run_agent_command(agent_path)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            result["subprocess"] = subprocess_result
            result["duration_ms"] = int(duration_ms)
            result["timestamp"] = utc_now()
            
            if subprocess_result.get("status") == "executed":
                result["status"] = "executed"
                self._log(f"Stage {agent_name} completed successfully in {result['duration_ms']}ms")
            else:
                error_msg = subprocess_result.get("error_message", "")[:200]
                self._log(f"Stage {agent_name} FAILED after {result['duration_ms']}ms: {error_msg}")
                
        except Exception as e:
            result["status"] = "exception"
            result["error_message"] = str(e)[:500]
            self._log(f"Stage {agent_name} FAILED with exception: {e}")
        
        return result
    
    def run_loop(self, initial_task_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete self-healing development loop."""
        self._log("=" * 60)
        self._log("STARTING SELF-HEALING DEVELOPMENT LOOP")
        self._log("=" * 60)
        
        task_id = initial_task_id or "loop-init"
        
        # Initialize state
        state = {
            "execution_id": self.execution_id,
            "task_id": task_id,
            "retry_count": 0,
            "current_stage": None,
            "current_agent": None,
            "failure_history": [],
            "applied_fixes": [],
            "start_time": utc_now(),
            "status": "RUNNING",
            "final_status": None,
        }
        save_json_file(LOOP_STATUS_PATH, state)
        
        # Define agent paths
        agents = {
            "planner_agent": "ai_agents/scripts/planner_agent.py",
            "coding_agent": "ai_agents/scripts/coder_agent.py",
            "testing_agent": "ai_agents/scripts/tester_agent.py",
            "debugging_agent": "ai_agents/scripts/debugger_agent.py",
            "reviewer_agent": "ai_agents/scripts/reviewer_agent_complete.py",
            "documentation_agent": "ai_agents/scripts/documentation_agent.py",
        }
        
        # Phase 2: Initial workflow execution through reviewer agent
        self._log("\n--- PHASE 2: INITIAL WORKFLOW EXECUTION ---")
        initial_flow = [
            ("Planner Agent", agents["planner_agent"]),
            ("Coding Agent", agents["coding_agent"]),
            ("Testing Agent", agents["testing_agent"]),
            ("Browser Runtime", "ai_agents/scripts/browser_runtime.py"),
            ("Screenshot Service", "ai_agents/scripts/screenshot_service.py"),
            ("Vision Agent", "ai_agents/scripts/vision_agent.py"),
            ("UI Validation Engine", "ai_agents/scripts/validation_engine.py"),
        ]
        
        for agent_name, agent_path in initial_flow:
            result = self.run_workflow_stage(agent_name, agent_path)
            state["failure_history"].append({
                "stage": agent_name,
                "status": result["status"],
                "error": result.get("error_message", "")[:200],
                "timestamp": utc_now(),
            })
        
        # Run Reviewer Agent for initial decision
        reviewer_result = self.run_workflow_stage("Reviewer Agent", agents["reviewer_agent"])
        
        # Check reviewer result for PASS/FAIL decision
        reviewer_status = reviewer_result.get("status", "").upper()
        
        state["retry_count"] = 1
        
        if reviewer_status == "PASS":
            state["final_status"] = "PASS"
            state["status"] = "COMPLETED"
            self._log("\n--- LOOP COMPLETED: PASS ---")
            
        elif reviewer_status == "FAIL":
            # Enter self-healing loop: Debugging -> Coding -> Testing -> Reviewer
            if state["retry_count"] < self.max_retries:
                self._log(f"\n--- ENTERING SELF-HEALING LOOP (Retry {state['retry_count']} of {self.max_retries}) ---")
                
                while reviewer_status != "PASS" and state["retry_count"] <= self.max_retries:
                    state["current_stage"] = "debugging_agent"
                    self._log("Executing Debugging Agent...")
                    
                    # Debugging Agent analysis
                    debug_result = self.run_workflow_stage("Debugging Agent", agents["debugging_agent"])
                    state["failure_history"].append({
                        "stage": "Debugging Agent",
                        "status": debug_result["status"],
                        "error": debug_result.get("error_message", "")[:200],
                        "timestamp": utc_now(),
                    })
                    
                    if debug_result.get("status") == "executed":
                        state["current_stage"] = "coding_agent"
                        self._log("Executing Coding Agent...")
                        
                        # Coding Agent fix application
                        coding_result = self.run_workflow_stage("Coding Agent", agents["coding_agent"])
                        state["failure_history"].append({
                            "stage": "Coding Agent",
                            "status": coding_result["status"],
                            "error": coding_result.get("error_message", "")[:200],
                            "timestamp": utc_now(),
                        })
                        
                        if coding_result.get("status") == "executed":
                            state["current_stage"] = "testing_agent"
                            self._log("Executing Testing Agent...")
                            
                            # Testing Agent validation
                            testing_result = self.run_workflow_stage("Testing Agent", agents["testing_agent"])
                            state["failure_history"].append({
                                "stage": "Testing Agent",
                                "status": testing_result["status"],
                                "error": testing_result.get("error_message", "")[:200],
                                "timestamp": utc_now(),
                            })
                            
                            if testing_result.get("status") == "executed":
                                state["current_stage"] = "reviewer_agent"
                                self._log("Executing Reviewer Agent...")
                                
                                # Reviewer Agent final decision
                                reviewer_result = self.run_workflow_stage("Reviewer Agent", agents["reviewer_agent"])
                                state["failure_history"].append({
                                    "stage": "Reviewer Agent",
                                    "status": reviewer_result["status"],
                                    "error": reviewer_result.get("error_message", "")[:200],
                                    "timestamp": utc_now(),
                                })
                                
                                reviewer_status = reviewer_result.get("status", "").upper()
                                
                                if reviewer_status == "PASS":
                                    state["final_status"] = "PASS"
                                    self._log("\n--- LOOP COMPLETED: PASS ---")
                                    break
                                else:
                                    # Retry logic
                                    state["retry_count"] += 1
                                    if state["retry_count"] <= self.max_retries:
                                        delay = self.retry_delay * (2 ** (state["retry_count"] - 1))
                                        self._log(f"\nWaiting {delay}s before next retry...")
                                        time.sleep(delay)
                                    else:
                                        state["status"] = "RETRY_LIMIT_REACHED"
                                        state["final_status"] = "RETRY_LIMIT_REACHED"
                                        self._log("\n--- LOOP TERMINATED: Retry limit reached ---")
                            else:
                                state["status"] = testing_result.get("status", "failed")
                                state["final_status"] = testing_result.get("error_message", "Testing failed")[:100]
                        else:
                            state["status"] = coding_result.get("status", "failed")
                            state["final_status"] = coding_result.get("error_message", "Coding failed")[:100]
                    else:
                        state["status"] = debug_result.get("status", "failed")
                        state["final_status"] = debug_result.get("error_message", "Debugging failed")[:100]
            else:
                state["status"] = "RETRY_LIMIT_REACHED"
                state["final_status"] = "RETRY_LIMIT_REACHED"
                self._log("\n--- LOOP TERMINATED: Retry limit reached ---")
            
        elif reviewer_status in ["ERROR", "EXCEPTION"]:
            state["final_status"] = "FAILURE"
            state["status"] = "TERMINATED"
        
        # Save final state
        state["end_time"] = utc_now()
        from datetime import timedelta
        start_dt = datetime.fromisoformat(state["start_time"]) if state.get("start_time") else datetime.now(timezone.utc)
        state["duration_ms"] = (datetime.now(timezone.utc) - start_dt).total_seconds() * 1000
        save_json_file(LOOP_STATUS_PATH, state)
        
        self._log("\n" + "=" * 60)
        self._log("LOOP EXECUTION SUMMARY")
        self._log("=" * 60)
        self._log(f"Execution ID: {state['execution_id']}")
        self._log(f"Task ID: {state['task_id']}")
        self._log(f"Final Status: {state.get('final_status', 'UNKNOWN')}")
        self._log(f"Total Retries: {state['retry_count']}")
        self._log("=" * 60)
        
        return state
    
    def stop_loop(self, reason: str = "") -> None:
        """Stop the loop early."""
        state = load_json_file(LOOP_STATUS_PATH)
        if state:
            state["status"] = "STOPPED"
            state["stop_reason"] = reason
            state["end_time"] = utc_now()
            save_json_file(LOOP_STATUS_PATH, state)
        
        self._log(f"Loop stopped: {reason}")


def main():
    """CLI entry point for the Self-Healing Development Loop."""
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Self-Healing Development Loop."
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Task ID to run the loop for",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Override maximum retry count",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=None,
        help="Override retry delay in seconds",
    )
    args = parser.parse_args()
    
    # Initialize controller
    controller = LoopController()
    
    if args.retries:
        controller.max_retries = args.retries
    if args.delay:
        controller.retry_delay = args.delay
    
    print("=" * 70)
    print("SELF-HEALING DEVELOPMENT LOOP - Sanskriti AI Studio")
    print("=" * 70)
    
    # Run the loop
    result = controller.run_loop(initial_task_id=args.task)
    
    # Print summary
    print("\n" + "=" * 70)
    print("LOOP EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Execution ID: {result.get('execution_id', 'N/A')}")
    print(f"Task ID: {result.get('task_id', 'N/A')}")
    print(f"Final Status: {result.get('final_status', 'UNKNOWN')}")
    print(f"Total Retries: {result.get('retry_count', 0)}")
    
    if result.get("final_status") == "PASS":
        print("\n[SUCCESS] Loop completed with PASS status")
    elif result.get("final_status") == "RETRY_LIMIT_REACHED":
        print(f"\n[RETRY_LIMIT] Reached retry limit ({controller.max_retries})")
    else:
        print(f"\n[FAILURE] Loop terminated with status: {result.get('final_status', 'UNKNOWN')}")
    
    print("\nLoop state saved to:", LOOP_STATUS_PATH)
    print("=" * 70)
    
    return 0 if result.get("final_status") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
