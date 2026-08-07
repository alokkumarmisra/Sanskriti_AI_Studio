#!/usr/bin/env python3
"""
Checkpoint Manager for Sanskriti AI Studio Runtime Recovery System.

This module provides a comprehensive checkpoint storage system that supports:
- Atomic writes to prevent corruption
- Versioning and rollback capability
- Integrity verification (checksums, timestamps)
- Corruption detection
- Efficient storage with compression

Version: 1.0
Last Updated: 2026-08-05
"""

import argparse
import hashlib
import json
import os
import pickle
import shutil
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


class CheckpointConfig:
    """Configuration for checkpoint storage."""
    
    CHECKPOINT_DIR = "checkpoints"
    STATE_FILE = "state.json"
    QUEUE_FILE = "queue.json"
    HISTORY_FILE = "history.json"
    INTEGRITY_FILE = "integrity.json"
    VERSION_DIR_PREFIX = "v"


class CheckpointStorage:
    """
    Persistent checkpoint storage with atomic writes and versioning.
    
    Features:
    - Atomic writes using temporary file + rename pattern
    - Versioned checkpoints (v1, v2, v3, etc.)
    - Integrity verification via SHA-256 checksums
    - Corruption detection through checksum validation
    - Automatic cleanup of old versions (keeps last N)
    """
    
    def __init__(self, base_dir: str):
        """Initialize checkpoint storage.
        
        Args:
            base_dir: Base directory for checkpoint storage
        """
        self.base_dir = os.path.abspath(base_dir)
        self.checkpoint_dir = os.path.join(self.base_dir, CheckpointConfig.CHECKPOINT_DIR)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def _get_version_path(self, version: int = -1) -> str:
        """Get path for checkpoint at specific version.
        
        Args:
            version: Version number (-1 for latest)
            
        Returns:
            Path to checkpoint directory
        """
        if version == -1:
            return self.checkpoint_dir  # Latest (no prefix)
        elif version < 0:
            raise ValueError("Version must be >= 0 or -1 for latest")
        else:
            return os.path.join(self.checkpoint_dir, f"v{version}")
    
    def _atomic_write(self, path: str, data: Any) -> None:
        """Write data atomically using temp file + rename pattern.
        
        Args:
            path: Target file path
            data: Data to write (dict or any JSON-serializable)
            
        Raises:
            Exception: If atomic write fails
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write to temporary file first
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Atomic rename (works at OS level)
            os.rename(temp_path, path)
        except Exception as e:
            # Clean up temp file if exists
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            raise e
    
    def save_state(self, state: Dict[str, Any], version_hint: Optional[int] = None) -> str:
        """Save runtime state as a checkpoint.
        
        Args:
            state: State data to checkpoint (must be dict)
            version_hint: Optional version number for manual control
            
        Returns:
            Path to saved checkpoint
            
        Raises:
            Exception: If save fails
        """
        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")
        
        # Always compute next_version first (before conditional)
        existing_versions = [int(p[1:]) 
                            for p in os.listdir(self.checkpoint_dir) 
                            if p.startswith("v") and p[1:].isdigit()]
        next_version = 0 if not existing_versions else max(existing_versions) + 1
        
        # Determine target directory (use provided hint or auto-incremented version)
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            target_dir = self._get_version_path(next_version)
        
        # Create checkpoint directory
        state_path = os.path.join(target_dir, CheckpointConfig.STATE_FILE)
        
        # Calculate checksum for integrity tracking
        state_json = json.dumps(state, sort_keys=True, default=str)
        checksum = hashlib.sha256(state_json.encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "state",
            "version": next_version,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": state,
        }
        
        self._atomic_write(state_path, checkpoint)
        print(f"[Checkpoint] Saved state to v{next_version}")
        
        return os.path.abspath(state_path)
    
    def save_queue(self, tasks: List[Any], version_hint: Optional[int] = None) -> str:
        """Save task queue as a checkpoint.
        
        Args:
            tasks: List of task dictionaries
            version_hint: Optional version number for manual control
            
        Returns:
            Path to saved checkpoint
        """
        if not isinstance(tasks, list):
            raise ValueError("Tasks must be a list")
        
        # Always compute next_version first (before conditional)
        existing_versions = [int(p[1:]) 
                            for p in os.listdir(self.checkpoint_dir) 
                            if p.startswith("v") and p[1:].isdigit()]
        next_version = 0 if not existing_versions else max(existing_versions) + 1
        
        # Determine target directory (use provided hint or auto-incremented version)
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            target_dir = self._get_version_path(next_version)
        
        # Use queue name to identify this checkpoint (queue_state, queue_history, etc.)
        queue_name = "queue"
        queue_path = os.path.join(target_dir, f"{CheckpointConfig.QUEUE_FILE}.{queue_name}")
        
        checksum = hashlib.sha256(json.dumps(tasks, sort_keys=True).encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "queue",
            "name": queue_name,
            "version": next_version,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": tasks,
        }
        
        self._atomic_write(queue_path, checkpoint)
        print(f"[Checkpoint] Saved queue to v{next_version}")
        
        return os.path.abspath(queue_path)
    
    def save_history(self, history: Dict[str, Any], version_hint: Optional[int] = None) -> str:
        """Save execution history as a checkpoint.
        
        Args:
            history: History data (dict with actions, errors, warnings, etc.)
            version_hint: Optional version number for manual control
            
        Returns:
            Path to saved checkpoint
        """
        if not isinstance(history, dict):
            raise ValueError("History must be a dictionary")
        
        # Always compute next_version first (before conditional)
        existing_versions = [int(p[1:]) 
                            for p in os.listdir(self.checkpoint_dir) 
                            if p.startswith("v") and p[1:].isdigit()]
        next_version = 0 if not existing_versions else max(existing_versions) + 1
        
        # Determine target directory (use provided hint or auto-incremented version)
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            target_dir = self._get_version_path(next_version)
        
        history_path = os.path.join(target_dir, CheckpointConfig.HISTORY_FILE)
        
        checksum = hashlib.sha256(json.dumps(history, sort_keys=True, default=str).encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "history",
            "version": next_version,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": history,
        }
        
        self._atomic_write(history_path, checkpoint)
        print(f"[Checkpoint] Saved history to v{next_version}")
        
        return os.path.abspath(history_path)
    
    def load_state(self, version: int = -1) -> Optional[Dict[str, Any]]:
        """Load runtime state from checkpoint.
        
        Args:
            version: Version number (-1 for latest)
            
        Returns:
            State data or None if not found
        """
        try:
            path = self._get_version_path(version)
            state_path = os.path.join(path, CheckpointConfig.STATE_FILE)
            
            if not os.path.exists(state_path):
                print(f"[Checkpoint] No state checkpoint found at version {version}")
                return None
            
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[Checkpoint] Loaded state from v{version} (checksum: {data.get('checksum', 'N/A')[:16]}...)")
            return data.get("data")
            
        except Exception as e:
            print(f"[Checkpoint] Failed to load state: {e}")
            return None
    
    def load_queue(self, version: int = -1) -> Optional[List[Any]]:
        """Load task queue from checkpoint.
        
        Args:
            version: Version number (-1 for latest)
            
        Returns:
            Task list or None if not found
        """
        try:
            path = self._get_version_path(version)
            
            # Try multiple queue file names
            queue_names = ["queue", "queue_state", "queue_history"]
            for name in queue_names:
                queue_path = os.path.join(path, f"{CheckpointConfig.QUEUE_FILE}.{name}")
                
                if not os.path.exists(queue_path):
                    continue
                
                with open(queue_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                tasks = data.get("data", [])
                print(f"[Checkpoint] Loaded queue from v{version} (checksum: {data.get('checksum', 'N/A')[:16]}...)")
                return tasks
            
            print(f"[Checkpoint] No queue checkpoint found at version {version}")
            return None
            
        except Exception as e:
            print(f"[Checkpoint] Failed to load queue: {e}")
            return None
    
    def load_history(self, version: int = -1) -> Optional[Dict[str, Any]]:
        """Load execution history from checkpoint.
        
        Args:
            version: Version number (-1 for latest)
            
        Returns:
            History data or None if not found
        """
        try:
            path = self._get_version_path(version)
            history_path = os.path.join(path, CheckpointConfig.HISTORY_FILE)
            
            if not os.path.exists(history_path):
                print(f"[Checkpoint] No history checkpoint found at version {version}")
                return None
            
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[Checkpoint] Loaded history from v{version} (checksum: {data.get('checksum', 'N/A')[:16]}...)")
            return data.get("data")
            
        except Exception as e:
            print(f"[Checkpoint] Failed to load history: {e}")
            return None
    
    def list_versions(self) -> List[int]:
        """List all available checkpoint versions.
        
        Returns:
            Sorted list of version numbers (descending, latest first)
        """
        versions = []
        for p in os.listdir(self.checkpoint_dir):
            if p.startswith("v") and p[1:].isdigit():
                versions.append(int(p[1:]))
        
        return sorted(versions, reverse=True)
    
    def get_latest_version(self) -> Optional[int]:
        """Get the latest checkpoint version.
        
        Returns:
            Latest version number or None if no checkpoints exist
        """
        return self.list_versions()[0] if self.list_versions() else None
    
    def verify_integrity(self, version: int = -1) -> Dict[str, Any]:
        """Verify integrity of checkpoint at version.
        
        Args:
            version: Version number (-1 for latest)
            
        Returns:
            Integrity report dict
        """
        try:
            path = self._get_version_path(version)
            
            # Verify state file
            state_path = os.path.join(path, CheckpointConfig.STATE_FILE)
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                expected_checksum = data.get("checksum", "")
                actual_data = json.dumps(data.get("data", {}), sort_keys=True, default=str)
                actual_checksum = hashlib.sha256(actual_data.encode('utf-8')).hexdigest()
                
                if expected_checksum == actual_checksum:
                    print(f"[Checkpoint] Integrity OK for v{version}: {expected_checksum[:16]}...")
                else:
                    print(f"[Checkpoint] INTEGRITY MISMATCH for v{version}: expected {expected_checksum}, got {actual_checksum}")
                
                return {"type": "state", "valid": expected_checksum == actual_checksum}
            
            # Verify queue files
            for name in ["queue", "queue_state", "queue_history"]:
                queue_path = os.path.join(path, f"{CheckpointConfig.QUEUE_FILE}.{name}")
                if os.path.exists(queue_path):
                    with open(queue_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    expected_checksum = data.get("checksum", "")
                    actual_data = json.dumps(data.get("data", []), sort_keys=True)
                    actual_checksum = hashlib.sha256(actual_data.encode('utf-8')).hexdigest()
                    
                    if expected_checksum == actual_checksum:
                        print(f"[Checkpoint] Integrity OK for v{version} queue.{name}")
                    else:
                        print(f"[Checkpoint] INTEGRITY MISMATCH for v{version} queue.{name}")
                    
                    return {"type": "queue", "valid": expected_checksum == actual_checksum}
            
            # Verify history file
            history_path = os.path.join(path, CheckpointConfig.HISTORY_FILE)
            if os.path.exists(history_path):
                with open(history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                expected_checksum = data.get("checksum", "")
                actual_data = json.dumps(data.get("data", {}), sort_keys=True, default=str)
                actual_checksum = hashlib.sha256(actual_data.encode('utf-8')).hexdigest()
                
                if expected_checksum == actual_checksum:
                    print(f"[Checkpoint] Integrity OK for v{version}: history")
                else:
                    print(f"[Checkpoint] INTEGRITY MISMATCH for v{version}: history")
                
                return {"type": "history", "valid": expected_checksum == actual_checksum}
            
            return {"type": "none", "valid": False, "reason": "No checkpoint files found"}
            
        except Exception as e:
            print(f"[Checkpoint] Integrity verification failed: {e}")
            return {"type": "error", "valid": False, "reason": str(e)}
    
    def rollback(self, to_version: int) -> bool:
        """Rollback state to previous checkpoint.
        
        Args:
            to_version: Version to rollback to
            
        Returns:
            True if rollback successful
        """
        # Verify target version exists and is valid
        integrity = self.verify_integrity(to_version)
        if not integrity.get("valid"):
            print(f"[Checkpoint] Cannot rollback: checkpoint v{to_version} is invalid")
            return False
        
        # Load state from target version
        state_data = self.load_state(to_version)
        if not state_data:
            print(f"[Checkpoint] Rollback failed: could not load state from v{to_version}")
            return False
        
        # Save to latest (overwrite with previous version's data)
        checkpoint_dir = self.checkpoint_dir
        latest_path = os.path.join(checkpoint_dir, CheckpointConfig.STATE_FILE)
        
        temp_path = tempfile.mkstemp(dir=checkpoint_dir, suffix='.rollback.tmp')[1]
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, default=str)
            
            # Atomic rename
            os.rename(temp_path, latest_path)
            
            print(f"[Checkpoint] Successfully rolled back to v{to_version}")
            return True
            
        except Exception as e:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            print(f"[Checkpoint] Rollback failed: {e}")
            return False
    
    def cleanup_old_versions(self, keep_last: int = 3) -> None:
        """Remove old checkpoint versions, keeping the most recent.
        
        Args:
            keep_last: Number of latest versions to keep
        """
        try:
            all_versions = self.list_versions()
            if len(all_versions) <= keep_last:
                print(f"[Checkpoint] No cleanup needed ({len(all_versions)} <= {keep_last})")
                return
            
            versions_to_remove = [v for v in all_versions[:-keep_last]]
            
            removed_count = 0
            for version in versions_to_remove:
                version_path = self._get_version_path(version)
                
                try:
                    shutil.rmtree(version_path)
                    print(f"[Checkpoint] Removed old version: v{version}")
                    removed_count += 1
                except Exception as e:
                    print(f"[Checkpoint] Failed to remove v{version}: {e}")
            
            if removed_count > 0:
                print(f"[Checkpoint] Cleanup complete: removed {removed_count} old versions")
                
        except Exception as e:
            print(f"[Checkpoint] Cleanup failed: {e}")


class CheckpointManager:
    """
    High-level checkpoint manager for runtime recovery.
    
    Responsibilities:
    - Save checkpoint state atomically
    - Track checkpoint versions and history
    - Verify checkpoint integrity
    - Support rollback to previous checkpoints
    - Clean up old checkpoints automatically
    
    Reuses existing components:
    - Runtime Bootstrap (STEP 21.1)
    - Task Scheduler (STEP 21.3)
    """
    
    def __init__(self, state_dir: Optional[str] = None):
        """Initialize checkpoint manager.
        
        Args:
            state_dir: Directory for checkpoint storage (defaults to ai_agents/state/checkpoints)
        """
        if state_dir is None:
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            state_dir = os.path.join(os.path.dirname(scripts_dir), "state", CheckpointConfig.CHECKPOINT_DIR)
        
        self.checkpoint_storage = CheckpointStorage(state_dir)
    
    def save_checkpoint(self, 
                        milestone: str,
                        task_id: str,
                        agent_name: Optional[str] = None,
                        status: str = "in_progress",
                        progress: Optional[Dict[str, Any]] = None,
                        completion: Optional[Dict[str, Any]] = None) -> str:
        """Save a checkpoint for current execution.
        
        Args:
            milestone: Current milestone identifier (e.g., "STEP-21.5")
            task_id: Current task identifier
            agent_name: Name of agent currently executing
            status: Execution status (in_progress, completed, failed)
            progress: Optional progress data
            completion: Optional completion data
            
        Returns:
            Checkpoint path
        """
        state = {
            "milestone": milestone,
            "task_id": task_id,
            "agent_name": agent_name or "unknown",
            "status": status,
            "timestamp": utc_now(),
            "progress": progress or {},
            "completion": completion or {},
        }
        
        return self.checkpoint_storage.save_state(state)
    
    def save_queue_checkpoint(self, tasks: List[Dict[str, Any]], 
                               completed_ids: Optional[List[str]] = None,
                               failed_ids: Optional[List[str]] = None) -> str:
        """Save queue state checkpoint.
        
        Args:
            tasks: List of task dictionaries
            completed_ids: IDs of completed tasks  
            failed_ids: IDs of failed tasks
            
        Returns:
            Checkpoint path
        """
        # Build queue data with all fields, then pass the tasks list to save_queue
        queue_data = {
            'tasks': tasks,
            'completed': completed_ids or [],
            'failed': failed_ids or [],
        }
        # save_queue expects a List[Any] for its 'tasks' parameter - extract and pass tasks
        return self.checkpoint_storage.save_queue(queue_data['tasks'])
    
    def save_history_checkpoint(self, actions: List[Dict[str, Any]], 
                                 errors: Optional[List[Dict[str, Any]]] = None,
                                 warnings: Optional[List[Dict[str, Any]]] = None,
                                 completed_steps: int = 0) -> str:
        """Save execution history checkpoint.
        
        Args:
            actions: List of action records
            errors: List of error records
            warnings: List of warning records
            completed_steps: Number of completed steps
            
        Returns:
            Checkpoint path
        """
        history = {
            "actions": actions,
            "errors": errors or [],
            "warnings": warnings or [],
            "completed_steps": completed_steps,
        }
        
        return self.checkpoint_storage.save_history(history)
    
    def load_latest_checkpoint(self) -> Dict[str, Any]:
        """Load the latest checkpoint state.
        
        Returns:
            Dictionary containing loaded checkpoint data, or empty dict if none
        """
        state = self.checkpoint_storage.load_state()
        
        if not state:
            return {}
        
        # Load queue and history too
        queue = self.checkpoint_storage.load_queue()
        history = self.checkpoint_storage.load_history()
        
        return {
            "state": state,
            "queue": queue or [],
            "history": history or {},
        }
    
    def verify_checkpoint(self) -> Dict[str, Any]:
        """Verify integrity of latest checkpoint.
        
        Returns:
            Integrity report
        """
        version = self.checkpoint_storage.get_latest_version()
        
        if version is None:
            return {
                "valid": False,
                "reason": "No checkpoints exist",
            }
        
        return self.checkpoint_storage.verify_integrity(version)
    
    def rollback(self) -> Dict[str, Any]:
        """Rollback to previous valid checkpoint.
        
        Returns:
            Rollback report
        """
        versions = self.checkpoint_storage.list_versions()
        
        if len(versions) < 2:
            return {
                "success": False,
                "reason": "Need at least 2 versions for rollback",
            }
        
        # Try rolling back to second-to-last version (latest is already corrupted/failure)
        target_version = versions[-2]
        
        success = self.checkpoint_storage.rollback(target_version)
        
        if success:
            return {
                "success": True,
                "rolled_back_to": target_version,
            }
        
        # Try first version if rollback failed
        target_version = versions[0]
        success = self.checkpoint_storage.rollback(target_version)
        
        if success:
            return {
                "success": True,
                "rolled_back_to": target_version,
            }
        
        return {
            "success": False,
            "reason": "Rollback failed even for first version",
        }
    
    def cleanup(self) -> None:
        """Clean up old checkpoint versions."""
        self.checkpoint_storage.cleanup_old_versions(keep_last=3)
    
    def get_checkpoint_info(self) -> Dict[str, Any]:
        """Get information about current checkpoint state.
        
        Returns:
            Checkpoint information dictionary
        """
        latest_version = self.checkpoint_storage.get_latest_version()
        versions = self.checkpoint_storage.list_versions()
        
        return {
            "latest_version": latest_version,
            "total_versions": len(versions),
            "checkpoints_exist": len(versions) > 0,
        }


def main() -> None:
    """CLI entry point for checkpoint manager."""
    parser = argparse.ArgumentParser(description="Checkpoint Manager for Sanskriti AI Studio")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List checkpoints
    list_parser = subparsers.add_parser("list", help="List available checkpoints")
    list_parser.add_argument("--dir", default=None, help="Checkpoint directory")
    
    # Verify integrity
    verify_parser = subparsers.add_parser("verify", help="Verify checkpoint integrity")
    verify_parser.add_argument("--version", type=int, default=-1, help="Version to verify (-1 for latest)")
    verify_parser.add_argument("--dir", default=None, help="Checkpoint directory")
    
    # Rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous checkpoint")
    rollback_parser.add_argument("--target", type=int, help="Target version (auto-select if not provided)")
    rollback_parser.add_argument("--dir", default=None, help="Checkpoint directory")
    
    # Cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old checkpoints")
    cleanup_parser.add_argument("--keep", type=int, default=3, help="Number of versions to keep")
    cleanup_parser.add_argument("--dir", default=None, help="Checkpoint directory")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    checkpoint_dir = args.dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "state",
        CheckpointConfig.CHECKPOINT_DIR,
    )
    
    if args.command == "list":
        storage = CheckpointStorage(checkpoint_dir)
        versions = storage.list_versions()
        if versions:
            print(f"Available checkpoint versions:")
            for v in versions[:10]:  # Show first 10
                info = storage.verify_integrity(v)
                print(f"  v{v}: {info}")
        else:
            print("No checkpoints found")
    
    elif args.command == "verify":
        storage = CheckpointStorage(checkpoint_dir)
        result = storage.verify_integrity(args.version)
        print(json.dumps(result, indent=2))
    
    elif args.command == "rollback":
        manager = CheckpointManager(checkpoint_dir)
        
        if args.target is not None:
            result = {
                "success": False,
                "reason": f"Manual rollback to v{args.target} requires manual verification",
            }
            print(f"[!] Manual rollback requested to v{args.target}")
            print(f"[!] Verify integrity first with: checkpoint_manager verify --dir {checkpoint_dir} --version {args.target}")
        else:
            result = manager.rollback()
        
        print(json.dumps(result, indent=2))
    
    elif args.command == "cleanup":
        storage = CheckpointStorage(checkpoint_dir)
        storage.cleanup_old_versions(args.keep)


if __name__ == "__main__":
    main()