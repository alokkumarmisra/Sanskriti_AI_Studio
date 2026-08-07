from typing import Any, Dict, List


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
    
    if queue:
        print(f"[OK] Restored queue with {len(queue)} tasks")
    
    # Initialize actions to avoid unbound variable error when history is empty/None
    actions: List[Any] = []
    
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
