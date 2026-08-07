import os
import json
import argparse
from typing import Dict, Any, List, Optional
from enum import Enum


class FailureType(Enum):
    """Types of failure scenarios that the recovery manager can handle."""
    UNEXPECTED_SHUTDOWN = "UNEXPECTED_SHUTDOWN"
    LM_STUDIO_DISCONNECT = "LM_STUDIO_DISCONNECT"
    MODEL_LOADING_ERROR = "MODEL_LOADING_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"


class CheckpointStorage:
    """Handles checkpoint storage and retrieval operations."""

    def load_state(self, version: int) -> Optional[Dict[str, Any]]:
        """Load state from a checkpoint version."""
        pass

    def load_queue(self, version: int) -> List[Dict[str, Any]]:
        """Load task queue from a checkpoint version."""
        return []

    def load_history(self, version: int) -> Optional[Dict[str, Any]]:
        """Load execution history from a checkpoint version."""
        pass

    def verify_integrity(self, version: str) -> Dict[str, Any]:
        """Verify the integrity of a checkpoint."""
        return {"valid": False, "reason": "No version found"}

    def get_latest_version(self) -> Optional[str]:
        """Get the latest checkpoint version."""
        return None

    def list_versions(self) -> List[str]:
        """List all available checkpoint versions."""
        return []

    def rollback(self) -> Dict[str, Any]:
        """Rollback to previous checkpoint."""
        return {"success": False, "rolled_back_to": None}


class EnvironmentValidator:
    """Validates the environment state before resuming execution."""

    def verify_all(self) -> Dict[str, Any]:
        """Verify all environment conditions."""
        return {
            "success": True,
            "errors": []
        }


class FailureDetector:
    """Detects and classifies failure types."""

    def detect_failure(self, failure_type: Optional[FailureType] = None) -> Dict[str, Any]:
        """Detect the current failure type."""
        return {
            "failure_type": failure_type or FailureType.UNEXPECTED_SHUTDOWN,
            "manual_intervention_required": False,
            "recommended_strategy": {"action": "RESTORE_AND_RESUME"}
        }


class RecoveryManager:
    """Manages recovery operations for the AI agent system."""

    def __init__(self):
        self.checkpoint_storage = CheckpointStorage()
        self.env_validator = EnvironmentValidator()
        self.failure_detector = FailureDetector()

    def validate_checkpoint_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the current checkpoint."""
        return {"valid": True, "reason": ""}

    def restore_runtime_state(self) -> Dict[str, Any]:
        """Restore runtime state from checkpoint."""
        print("=" * 60)
        print("Restoring Runtime State")
        print("=" * 60)
        
        integrity = self.validate_checkpoint_integrity()
        
        if not integrity.get("valid"):
            print(f"[!] Checkpoint validation failed: {integrity.get('reason')}")
            return {"restored": False, "reason": f"Checkpoint validation failed: {integrity.get('reason')}"}
        
        # Load and restore state components
        state = self.checkpoint_storage.load_state(-1)
        queue = self.checkpoint_storage.load_queue(-1)
        history = self.checkpoint_storage.load_history(-1)
        
        if not state:
            print("[!] Failed to load checkpoint state")
            return {"restored": False, "reason": "Failed to load checkpoint state"}
        
        milestone = state.get("milestone", "")
        task_id = state.get("task_id", "")
        agent_name = state.get("agent_name", "")
        status = state.get("status", "restored_from_checkpoint")
        
        print(f"[OK] Restored milestone: {milestone}")
        print(f"[OK] Restored task: {task_id}")
        print(f"[OK] Restored agent: {agent_name}")
        print(f"[OK] Restored status: {status}")
        
        # Initialize actions to avoid unbound variable error when history is empty/None
        actions: List[Any] = []
        
        if queue:
            print(f"[OK] Restored queue with {len(queue)} tasks")
        
        if history:
            actions = history.get("actions", []) or []
            errors = history.get("errors", []) or []
            warnings = history.get("warnings", []) or []
            completed_steps = history.get("completed_steps", 0) or 0
            print(f"[OK] Restored history ({len(actions)} actions, {completed_steps} steps)")
        
        return {
            "restored": True,
            "milestone": milestone,
            "task_id": task_id,
            "agent_name": agent_name,
            "status": status,
            "tasks_restored": len(queue) if queue else 0,
            "actions_restored": len(actions),
        }

    def verify_environment_before_resume(self) -> Dict[str, Any]:
        """Verify environment is ready for resume."""
        print("=" * 60)
        print("Verifying Environment Before Resume")
        print("=" * 60)
        
        env_results = self.env_validator.verify_all()
        
        state_files = [
            "ai_agents/state/startup_report.json",
            "ai_agents/state/actions.jsonl",
            "ai_agents/state/milestone_status.json",
        ]
        
        missing_state = []
        for file in state_files:
            if not os.path.exists(file):
                missing_state.append(file)
        
        all_valid = (env_results["success"] and len(missing_state) == 0)
        
        return {
            "environment_ready": all_valid,
            "errors": env_results.get("errors", []),
            "missing_state_files": missing_state,
        }

    def resume_execution(self) -> Dict[str, Any]:
        """Resume execution from latest checkpoint."""
        print("=" * 60)
        print("Resuming Execution")
        print("=" * 60)
        
        env_report = self.verify_environment_before_resume()
        
        if not env_report["environment_ready"]:
            errors = env_report.get("errors", []) + env_report.get("missing_state_files", [])
            return {"resumed": False, "reason": f"Environment verification failed: {len(errors)} issues", "errors": errors}
        
        restore_report = self.restore_runtime_state()
        
        if not restore_report["restored"]:
            return {"resumed": False, "reason": restore_report.get("reason")}
        
        latest_version = self.checkpoint_storage.get_latest_version()
        if latest_version:
            integrity = self.checkpoint_storage.verify_integrity(latest_version)
            
            if integrity.get("valid"):
                print("\n" + "=" * 60)
                print("[SUCCESS] Runtime state restored successfully")
                print("=" * 60)
                
                interrupted_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "state",
                    "checkpoints",
                    f"v{latest_version}",
                    "_interrupted.json"
                )
                
                if os.path.exists(interrupted_path):
                    try:
                        os.remove(interrupted_path)
                        print(f"[OK] Removed interruption marker")
                    except Exception as e:
                        print(f"[!] Could not remove interruption marker: {e}")
                
                return {
                    "resumed": True,
                    "from_checkpoint": latest_version,
                    "milestone": restore_report.get("milestone", ""),
                    "task_id": restore_report.get("task_id", ""),
                    "tasks_ready": restore_report.get("tasks_restored", 0),
                }
        
        return {"resumed": False, "reason": "Integrity verification failed after state restoration"}

    def handle_failure(self, failure_type: Optional[FailureType] = None) -> Dict[str, Any]:
        """Handle a detected failure with appropriate recovery."""
        if not failure_type:
            failure_type = FailureType.UNEXPECTED_SHUTDOWN
        
        # Step 1: Detect and classify failure
        failure_report = self.failure_detector.detect_failure(failure_type)
        
        # Step 2: Check if manual intervention required
        if failure_report.get("manual_intervention_required"):
            return {
                "handled": False,
                "failure_type": failure_report["failure_type"],
                "reason": "Manual intervention required",
                "recovery_actions": failure_report.get("recovery_actions", []),
            }
        
        # Step 3: Get recommended strategy
        strategy = failure_report.get("recommended_strategy", {})
        strategy_name = strategy.get("action", "unknown")
        
        print(f"\n[Strategy] {strategy_name}")
        
        # Step 4: Attempt recovery based on strategy
        if strategy_name == "RECONNECT":
            return self._handle_reconnect_failure()
        
        elif strategy_name in ["RETRY_WITH_BACKOFF", "RESTORE_AND_RESUME"]:
            return self.handle_restore_and_resume(failure_report)
        
        else:
            return {
                "handled": False,
                "failure_type": failure_report["failure_type"],
                "strategy": strategy_name,
                "reason": f"Unknown recovery strategy: {strategy_name}",
            }

    def _handle_reconnect_failure(self) -> Dict[str, Any]:
        """Handle failures that just need reconnection."""
        print("[Recovery] Performing reconnect for temporary failure")
        
        return {
            "handled": True,
            "failure_type": FailureType.LM_STUDIO_DISCONNECT.value,
            "strategy": "RECONNECT",
            "action": "Retry next operation with backoff",
            "notes": "Temporary failures will be handled by automatic retry logic",
        }

    def handle_restore_and_resume(self, failure_report: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failures that require state restoration and resume."""
        print("[Recovery] Performing restore and resume")
        
        restore_result = self.restore_runtime_state()
        
        if restore_result["restored"]:
            resume_result = self.resume_execution()
            
            if resume_result["resumed"]:
                return {
                    "handled": True,
                    "failure_type": failure_report.get("failure_type"),
                    "strategy": "RESTORE_AND_RESUME",
                    "result": resume_result,
                }
        
        print("[Recovery] Attempting rollback to previous checkpoint")
        
        rollback_result = self.checkpoint_storage.rollback()
        
        if rollback_result.get("success"):
            print(f"[Recovery] Rolled back to version {rollback_result.get('rolled_back_to')}")
            
            restore_result = self.restore_runtime_state()
            if restore_result["restored"]:
                resume_result = self.resume_execution()
                
                if resume_result["resumed"]:
                    return {
                        "handled": True,
                        "failure_type": failure_report.get("failure_type"),
                        "strategy": "ROLLBACK_AND_RESUME",
                        "rollback_version": rollback_result.get("rolled_back_to"),
                        "result": resume_result,
                    }
        
        return {
            "handled": False,
            "failure_type": failure_report.get("failure_type"),
            "reason": "Failed to restore and resume execution",
            "rollback_attempted": True,
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main() -> None:
    """CLI entry point for Recovery Manager."""
    parser = argparse.ArgumentParser(description="Recovery Manager for Sanskriti AI Studio")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    detect_parser = subparsers.add_parser("detect", help="Detect current failure type")
    detect_parser.add_argument(
        "--failure-type",
        choices=[e.value for e in FailureType],
        default=None,
        help="Override auto-detection with specific failure type"
    )
    
    handle_parser = subparsers.add_parser("handle", help="Handle a detected failure")
    handle_parser.add_argument(
        "--failure-type",
        choices=[e.value for e in FailureType],
        default=None,
        help="Failure type to handle"
    )
    
    list_parser = subparsers.add_parser("list-checkpoints", help="List available checkpoints")
    verify_parser = subparsers.add_parser("verify-checkpoint", help="Verify latest checkpoint integrity")
    restore_parser = subparsers.add_parser("restore-state", help="Restore runtime state from checkpoint")
    resume_parser = subparsers.add_parser("resume", help="Resume execution from checkpoint")
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous checkpoint")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    recovery_manager = RecoveryManager()
    
    if args.command == "detect":
        failure_type_str = args.failure_type or FailureType.UNEXPECTED_SHUTDOWN.value
        try:
            failure_type = FailureType(failure_type_str)
        except ValueError:
            print(f"[!] Unknown failure type: {failure_type_str}")
            return
        
        report = recovery_manager.failure_detector.detect_failure(failure_type)
        print(json.dumps(report, indent=2))
    
    elif args.command == "handle":
        if not args.failure_type:
            print("[!] --failure-type is required")
            return
        
        try:
            failure_type = FailureType(args.failure_type)
        except ValueError:
            print(f"[!] Unknown failure type: {args.failure_type}")
            return
        
        result = recovery_manager.handle_failure(failure_type)
        print(json.dumps(result, indent=2))
    
    elif args.command == "list-checkpoints":
        versions = recovery_manager.checkpoint_storage.list_versions()
        if versions:
            for v in versions[:10]:
                info = recovery_manager.checkpoint_storage.verify_integrity(v)
                print(f"  v{v}: {info}")
        else:
            print("No checkpoints found")
    
    elif args.command == "verify-checkpoint":
        result = recovery_manager.validate_checkpoint_integrity()
        print(json.dumps(result, indent=2))
    
    elif args.command == "restore-state":
        result = recovery_manager.restore_runtime_state()
        print(json.dumps(result, indent=2))
    
    elif args.command == "resume":
        result = recovery_manager.resume_execution()
        print(json.dumps(result, indent=2))
    
    elif args.command == "rollback":
        result = recovery_manager.checkpoint_storage.rollback()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
