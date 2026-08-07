#!/usr/bin/env python3
import re

with open('ai_agents/scripts/checkpoint_manager.py', 'r') as f:
    content = f.read()

# Fix save_state method - compute next_version before conditional branch
old_save_state = '''        if not isinstance(state, dict):
            raise ValueError("State must be a dictionary")
        
        # Determine version
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            # Find next available version
            existing_versions = [int(p[1:]) 
                                for p in os.listdir(self.checkpoint_dir) 
                                if p.startswith("v") and p[1:].isdigit()]
            if not existing_versions:
                next_version = 0
            else:
                next_version = max(existing_versions) + 1
            
            target_dir = self._get_version_path(next_version)
        
        # Create checkpoint directory
        state_path = os.path.join(target_dir, CheckpointConfig.STATE_FILE)
        
        # Calculate checksum for integrity tracking
        state_json = json.dumps(state, sort_keys=True, default=str)
        checksum = hashlib.sha256(state_json.encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "state",
            "version": next_version if version_hint is None else version_hint,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": state,
        }'''

new_save_state = '''        if not isinstance(state, dict):
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
        }'''

content = content.replace(old_save_state, new_save_state)

# Fix save_queue method - same pattern
old_save_queue = '''        if not isinstance(tasks, list):
            raise ValueError("Tasks must be a list")
        
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            existing_versions = [int(p[1:]) 
                                for p in os.listdir(self.checkpoint_dir) 
                                if p.startswith("v") and p[1:].isdigit()]
            if not existing_versions:
                next_version = 0
            else:
                next_version = max(existing_versions) + 1
            
            target_dir = self._get_version_path(next_version)
        
        # Use queue name to identify this checkpoint (queue_state, queue_history, etc.)
        queue_name = "queue"
        queue_path = os.path.join(target_dir, f"{CheckpointConfig.QUEUE_FILE}.{queue_name}")
        
        checksum = hashlib.sha256(json.dumps(tasks, sort_keys=True).encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "queue",
            "name": queue_name,
            "version": next_version if version_hint is None else version_hint,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": tasks,
        }'''

new_save_queue = '''        if not isinstance(tasks, list):
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
        }'''

content = content.replace(old_save_queue, new_save_queue)

# Fix save_history method - same pattern
old_save_history = '''        if not isinstance(history, dict):
            raise ValueError("History must be a dictionary")
        
        if version_hint is not None:
            target_dir = self._get_version_path(version_hint)
        else:
            existing_versions = [int(p[1:]) 
                                for p in os.listdir(self.checkpoint_dir) 
                                if p.startswith("v") and p[1:].isdigit()]
            if not existing_versions:
                next_version = 0
            else:
                next_version = max(existing_versions) + 1
            
            target_dir = self._get_version_path(next_version)
        
        history_path = os.path.join(target_dir, CheckpointConfig.HISTORY_FILE)
        
        checksum = hashlib.sha256(json.dumps(history, sort_keys=True, default=str).encode('utf-8')).hexdigest()
        
        checkpoint = {
            "type": "history",
            "version": next_version if version_hint is None else version_hint,
            "timestamp": utc_now(),
            "checksum": checksum,
            "data": history,
        }'''

new_save_history = '''        if not isinstance(history, dict):
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
        }'''

content = content.replace(old_save_history, new_save_history)

with open('ai_agents/scripts/checkpoint_manager.py', 'w') as f:
    f.write(content)

print("File updated successfully")
