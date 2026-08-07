#!/usr/bin/env python3
"""
Coding Agent Runtime for Sanskriti AI Studio AI Agents

This module provides the Coding Agent implementation that:
1. Loads global rules and agent definitions
2. Reads task plans from shared state
3. Identifies assigned tasks
4. Reads relevant project files
5. Sends TEXT-ONLY requests to Qwen 3.5 (NO images)
6. Allows reasoning before code changes
7. Applies modifications only when instructed
8. Records actions in state
9. Returns structured status

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images or visual data.

Version: 1.0
Last Updated: 2026-07-29
"""


from typing import Any, Dict, List, Optional

# Explicit exports for module discovery
__all__ = ["load_config", "load_global_rules", "load_coder_definition", 
            "load_task_plan", "load_project_file", "load_multiple_files",
            "build_coding_prompt", "record_action", "send_to_coding_model",
            "process_task", "main"]


import json
import os
from datetime import datetime, timezone

# Import from config.py for LM Studio connection
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CONFIG_MODULE_PATH = os.path.join(PROJECT_ROOT, 'scripts', 'config.py')


def load_config() -> dict:
    """
    Load configuration from config module.
    
    Returns:
        Dictionary with configuration values
    """
    import sys
    
    # Add parent to path if needed
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    
    try:
        import config as config_module
        
        return {
            'base_url': config_module.get_base_url(),
            'coding_model': config_module.get_coding_model(),
            'vision_model': config_module.get_vision_model(),
        }
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return {
            'base_url': 'http://localhost:1234/v1',
            'coding_model': '',
            'vision_model': '',
        }


def load_global_rules() -> str:
    """
    Load the global rules document.
    
    Returns:
        Content of global_rules.md file
    """
    path = os.path.join(PROJECT_ROOT, 'agents', 'global_rules.md')
    
    if not os.path.exists(path):
        print(f"[WARN] Global rules not found at {path}")
        return "# [Missing] Global Rules\n\n"
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_coder_definition() -> str:
    """
    Load the coder agent definition.
    
    Returns:
        Content of coder.md file
    """
    path = os.path.join(PROJECT_ROOT, 'agents', 'coder.md')
    
    if not os.path.exists(path):
        print(f"[WARN] Coder definition not found at {path}")
        return "# [Missing] Coding Agent Definition\n\n"
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_task_plan() -> Optional[Dict[str, Any]]:
    """
    Load the task plan from shared state.
    
    The task plan is stored in ai_agents/state/task_plan.json
    and contains structured task information from the Planner Agent.
    
    Returns:
        Task plan dictionary if exists, None otherwise
    
    Expected structure:
        {
            "task_id": "...",
            "task_type": "implementation|fix|refactor|test",
            "priority": "high|medium|low",
            "assigned_to": "coding_agent",
            "description": "...",
            "requirements": [...],
            "acceptance_criteria": [...],
            "files_to_create": [...],
            "files_to_modify": [...],
            "dependencies": [...],
            "context": {...}
        }
    """
    path = os.path.join(PROJECT_ROOT, 'state', 'task_plan.json')
    
    if not os.path.exists(path):
        print(f"[INFO] No task plan found at {path}. Waiting for Planner Agent to assign task.")
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse task_plan.json: {e}")
            return None


def load_project_file(rel_path: str) -> Optional[str]:
    """
    Load a project file from the root workspace.
    
    Args:
        rel_path: Path relative to project root (e.g., "backend/app/main.py")
    
    Returns:
        File content as string, or None if file not found
    
    IMPORTANT: This reads only - never modifies files outside ai_agents/
               without explicit instruction from workflow.
    """
    full_path = os.path.join(PROJECT_ROOT, rel_path)
    
    if not os.path.exists(full_path):
        print(f"[INFO] Project file not found: {rel_path}")
        return None
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_multiple_files(rel_paths: List[str]) -> Dict[str, Optional[str]]:
    """
    Load multiple project files at once.
    
    Args:
        rel_paths: List of paths relative to project root
    
    Returns:
        Dictionary mapping relative path to file content
    """
    results = {}
    for path in rel_paths:
        content = load_project_file(path)
        results[path] = content
    return results


def build_coding_prompt(
    task_plan: Dict[str, Any],
    global_rules: str,
    coder_def: str,
    file_contents: Optional[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    """
    Build a text-only prompt for Qwen 3.5 coding model.
    
    IMPORTANT: This prompt contains TEXT ONLY. Never include images or visual data.
               If visual analysis is needed, Vision Agent must analyze first and
               provide text diagnosis.
    
    Args:
        task_plan: The assigned task plan
        global_rules: Content of global rules
        coder_def: Content of coder agent definition
        file_contents: Dictionary of file paths to their content (optional)
    
    Returns:
        List of message dictionaries for chat completion
    
    Structure:
        [
            {"role": "system", "content": "System instruction with global rules"},
            {"role": "user", "content": "Task description and context"}
        ]
    """
    messages = []
    
    # System message with critical TEXT-ONLY rule
    system_content = f"""You are the Coding Agent for Sanskriti AI Studio. 
Your primary model is Qwen 3.5, which is TEXT-ONLY.

CRITICAL RULE: NEVER send images, screenshots, or visual data to Qwen 3.5.
                If visual analysis is required, the Vision Agent must analyze first
                and provide a TEXT diagnosis before you proceed.

You will receive text-only input and must reason about code changes before
applying any modifications. Only apply code changes when explicitly instructed
by the task execution workflow.

GLOBAL RULES:
"""
    system_content += global_rules[:2000]  # Include essential rules
    
    messages.append({
        "role": "system",
        "content": system_content,
    })
    
    # Task information
    task_id = task_plan.get('task_id', 'N/A')
    task_type = task_plan.get('task_type', 'implementation')
    description = task_plan.get('description', '')
    
    # Build requirements section
    requirements = task_plan.get('requirements', ['No specific requirements stated'])
    if not requirements:
        requirements = ['No specific requirements stated']
    requirements_str = '\n'.join(str(r) for r in requirements)
    
    # Build acceptance criteria section  
    acceptance_criteria = task_plan.get('acceptance_criteria', ['No acceptance criteria stated'])
    if not acceptance_criteria:
        acceptance_criteria = ['No acceptance criteria stated']
    acceptance_criteria_str = '\n'.join(str(ac) for ac in acceptance_criteria)
    
    # Build files to create section
    files_to_create = task_plan.get('files_to_create', [])
    files_to_create_str = '\n'.join(f'- {f}' for f in files_to_create) if files_to_create else 'None specified'
    
    # Build files to modify section
    files_to_modify = task_plan.get('files_to_modify', [])
    files_to_modify_str = '\n'.join(f'- {f}' for f in files_to_modify) if files_to_modify else 'None specified'
    
    # Build dependencies section (using simple string join, not chr(10))
    dependencies = task_plan.get('dependencies', ['No dependencies'])
    dependencies_str = '\n'.join(str(d) for d in dependencies) if dependencies else 'None'
    
    user_content = f"""## Task Assignment

**Task ID:** {task_id}
**Type:** {task_type}
**Priority:** {task_plan.get('priority', 'medium')}
**Assigned To:** coding_agent

## Task Description

{description}

## Requirements

{requirements_str}

## Acceptance Criteria

{acceptance_criteria_str}

## Files to Create/Modify

### Files to Create:
{files_to_create_str}

### Files to Modify:
{files_to_modify_str}

## Dependencies
{dependencies_str}

## Context
"""
    # Include file contents if provided
    if file_contents:
        for path, content in file_contents.items():
            if content:
                user_content += f"\n### {path}\n"
                # Truncate long files for context window management
                lines = content.split('\n')
                if len(lines) <= 50:
                    user_content += '\n'.join(lines[:20]) + "..."
                else:
                    user_content += '\n'.join(lines[:15]) + "\n... file truncated ...\n"
    
    user_content += f"""

## Your Responsibilities

1. **READ** the task plan and requirements carefully
2. **INSPECT** existing code before creating changes
3. **REASON** about implementation approach
4. **REQUEST** clarification if anything is unclear
5. **REPORT** progress updates when stuck or blocked
6. **APPLY** code changes ONLY when explicitly instructed by workflow
7. **TEST** any modifications thoroughly
8. **REPORT** structured status at completion

## CRITICAL: Text-Only Operation

- All communication with Qwen 3.5 must be text-only
- Never send images, screenshots, or visual data
- If visual analysis is needed: Vision Agent → Text Diagnosis → You
- Do not implement future milestones without instruction
- Protect Git history - no auto-push, reset, or force push

## Expected Output Format

When you complete a task (or need clarification), use this format:

```markdown
# Coding Agent Status Report

## Task ID
<task_id>

## Current State
[ANALYZING | READY_TO_IMPLEMENT | NEEDS_CLARIFICATION | BLOCKED]

## Summary
Brief description of current understanding and plan.

## Questions (if any)
[List unclear requirements or need for clarification]

## Files to Change
[List files you intend to modify/create]

## Next Action Requested
[What the user/workflow should do next]
```

Remember: Qwen 3.5 is TEXT-ONLY. Images are prohibited.
"""
    
    messages.append({
        "role": "user",
        "content": user_content,
    })
    
    return messages


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """
    Record an action in the agent state store.
    
    Args:
        action_type: Type of action ('read', 'reason', 'apply', 'test', etc.)
        details: Dictionary of action details
    
    State is stored in ai_agents/state/actions.jsonl (JSON Lines format)
    """
    actions_path = os.path.join(PROJECT_ROOT, 'state', 'actions.jsonl')
    
    action_record = {
        'agent': 'coder',
        'action_type': action_type,
        'details': details,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    # Ensure state directory exists
    os.makedirs(os.path.dirname(actions_path), exist_ok=True)
    
    with open(actions_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(action_record) + '\n')


def send_to_coding_model(
    messages: List[Dict[str, str]],
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Send a text-only request to the coding model.
    
    IMPORTANT: This method validates and sends TEXT-ONLY messages only.
               Never pass images or image data to this method.
    
    Args:
        messages: List of message dictionaries (text content only)
        base_url: LM Studio base URL (uses env var if not provided)
        model: Model name (uses env var if not provided)
    
    Returns:
        Response dictionary or None on error
    
    Raises:
        ValueError: If messages contain image data (TEXT-ONLY violation)
    """
    from scripts.lmstudio_client import LMStudioClient, chat_with_coding_model
    
    # Use default values for Optional parameters
    actual_base_url = base_url if base_url else os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
    actual_model = model if model else os.getenv('CODING_MODEL', '')
    
    # Validate text-only before sending
    for msg in messages:
        content = msg.get('content', '')
        
        # Check for image indicators
        if isinstance(content, str):
            image_indicators = [
                'data:image/',
                'base64,',
                '<image',
                '![](',
            ]
            for indicator in image_indicators:
                if indicator.lower() in content.lower():
                    raise ValueError(
                        "TEXT-ONLY VIOLATION detected. Never send images to Qwen 3.5."
                    )
    
    return chat_with_coding_model(messages=messages, base_url=actual_base_url, model=actual_model)


def process_task(task_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main task processing function for the Coding Agent.
    
    This function orchestrates the coding agent workflow:
    1. Load configuration and definitions
    2. Identify assigned task (from state or plan file)
    3. Read relevant project files
    4. Build prompt for Qwen 3.5 reasoning
    5. Send TEXT-ONLY request to model
    6. Record actions
    7. Return structured status
    
    Args:
        task_plan: Optional task plan (reads from state if None)
    
    Returns:
        Status dictionary with processing results
    """
    result = {
        'agent': 'coding_agent',
        'status': 'processing',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'actions_taken': [],
        'response': None,
        'error': None,
    }
    
    # Step 1: Load configuration
    config = load_config()
    result['config'] = {
        'base_url': config['base_url'],
        'coding_model': config['coding_model'] or '(not set - will use default)',
    }
    
    record_action('init', {'config_loaded': True, 'model': config['coding_model']})
    
    # Step 2: Load definitions (always load for context)
    global_rules = load_global_rules()
    coder_def = load_coder_definition()
    result['loaded'] = {
        'global_rules': bool(global_rules),
        'coder_def': bool(coder_def),
    }
    
    # Step 3: Load task plan (if not provided)
    if task_plan is None:
        task_plan = load_task_plan()
        if task_plan is None:
            result['status'] = 'no_task_assigned'
            result['message'] = "No task assigned. Waiting for Planner Agent."
            record_action('state', {
                'task_plan': None,
                'status': 'waiting_for_assignment',
            })
            return result
    
    # Step 4: Identify task and load relevant files
    task_id = task_plan.get('task_id', 'unknown')
    files_to_load = task_plan.get('files_to_read', [])
    
    if files_to_load:
        file_contents = load_multiple_files(files_to_load)
        result['files_loaded'] = list(file_contents.keys())
    else:
        file_contents = {}
    
    record_action('identify_task', {
        'task_id': task_id,
        'type': task_plan.get('task_type'),
        'files_count': len(file_contents),
    })
    
    # Step 5: Build prompt for TEXT-ONLY reasoning
    # Filter out None values to satisfy Dict[str, str] type requirement
    if file_contents:
        filtered_file_contents = {path: content for path, content in file_contents.items() if content}
    else:
        filtered_file_contents = {}
    
    messages = build_coding_prompt(
        task_plan=task_plan,
        global_rules=global_rules,
        coder_def=coder_def,
        file_contents=filtered_file_contents,
    )
    
    record_action('prompt_built', {
        'message_count': len(messages),
        'roles': [m['role'] for m in messages],
        'files_included': list(filtered_file_contents.keys()),
    })
    
    # Step 6: Send to coding model (TEXT-ONLY)
    try:
        result['response'] = send_to_coding_model(messages=messages, **config)
        
        if result['response']:
            response_content = result['response'].get('choices', [{}])[0].get('message', {}).get('content', '')
            result['model_response'] = response_content[:2000] if response_content else None
            
            record_action('reasoning_complete', {
                'has_response': True,
                'response_length': len(response_content) if response_content else 0,
                'status': result['response'].get('usage', {}).get('completion_tokens', 0),
            })
        else:
            result['status'] = 'model_error'
            result['error'] = "Model returned no response. Check LM Studio connection."
            
    except ValueError as e:
        result['status'] = 'text_only_violation'
        result['error'] = str(e)
        record_action('error', {'type': 'text_only_violation', 'message': str(e)})
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"{type(e).__name__}: {str(e)}"
        record_action('error', {'type': type(e).__name__, 'message': str(e)})
    
    # Step 7: Determine next action based on response
    if result['response'] and result.get('model_response'):
        # Analyze response for implementation instructions
        content = result['model_response']
        
        # Check for explicit "apply changes" instruction
        needs_implementation = False
        if isinstance(content, str) and content:
            if any(keyword in content.lower() for keyword in [
                'implement', 'create', 'write', 'add', 
                'modify this file', 'replace with', 'change to'
            ]):
                needs_implementation = True
        
        next_action = "Review response and wait for user confirmation before implementing changes."
        
        result['next_action'] = next_action
        result['requires_confirmation'] = needs_implementation
    
    else:
        result['next_action'] = f"Check model response or address error: {result.get('error', 'Unknown')}"
    
    record_action('process_complete', result)
    
    return result


def main():
    """
    Main entry point for running the Coding Agent.
    
    Can be run directly to process assigned tasks from state.
    
    Usage:
        python coder_agent.py
    """
    print("=" * 60)
    print("CODING AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 60)
    print()
    
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    print()
    
    # Process task from state (if available)
    task_plan = load_task_plan()
    
    if task_plan is None:
        print("[INFO] No active task in state. Agent will wait for assignment.")
        return
    
    print(f"[INFO] Active Task ID: {task_plan.get('task_id', 'N/A')}")
    print(f"[INFO] Task Type: {task_plan.get('task_type', 'N/A')}")
    print()
    
    # Run processing
    result = process_task(task_plan)
    
    # Print structured result
    print()
    print("=" * 60)
    print("CODING AGENT PROCESSING COMPLETE")
    print("=" * 60)
    print()
    
    print(f"Agent: {result['agent']}")
    print(f"Status: {result['status']}")
    
    if result.get('response'):
        print("Response received from model.")
        
    # Check for implementation instruction
    content = result.get('model_response', '')
    if isinstance(content, str) and content and any(kw in content.lower() for kw in ['implement', 'create', 'modify']):
        print("[!] Response contains implementation instructions.")
        print("[!] WAITING FOR USER CONFIRMATION before applying changes.")
    
    if result.get('error'):
        print(f"[ERROR] {result['error']}")
    
    print()
    
    print("NEXT ACTION:")
    print(result.get('next_action', 'No next action determined.'))
    
    print()
    
    print("=" * 60)
    print("TEXT-ONLY LLM CHECK:")
    print("- Images sent to Qwen 3.5: NO")
    print("- Image input added: NO")
    print("- Visual analysis attempted: NO (or YES, routed through Vision Model)")
    print("=" * 60)


if __name__ == '__main__':
    main()