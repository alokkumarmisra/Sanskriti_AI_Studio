#!/usr/bin/env python3
"""
Human Approval Workflow State Machine for Sanskriti AI Studio.

This module provides the approval workflow infrastructure that keeps users in control
of every important execution stage during milestone execution.

States:
    WAITING_FOR_APPROVAL - Agent completed work, awaiting user decision
    APPROVED - User approved, proceed to next step
    REJECTED - User rejected, return to previous agent
    PAUSED - Execution paused, waiting for user input
    STOPPED - Execution stopped by user
    SKIPPED - Task skipped with confirmation
    RESUMED - Paused execution resumed

Approval Actions:
    Continue     - Proceed to next task
    Pause        - Suspend execution temporarily
    Resume       - Resume from paused state
    Retry        - Retrying failed/prompt action
    Reject       - Reject current work, return to agent
    Skip         - Skip this task (requires confirmation)
    Stop         - Stop execution entirely
    Edit Prompt  - Modify prompt/acceptance criteria before retry
    Manual Override - Direct user intervention

Version: 1.0
Last Updated: 2026-08-05
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


class ApprovalState(str, Enum):
    """Approval workflow states."""
    
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"  # Awaiting user decision
    APPROVED = "APPROVED"                          # User approved
    REJECTED = "REJECTED"                          # User rejected  
    PAUSED = "PAUSED"                              # Execution paused
    STOPPED = "STOPPED"                            # Execution stopped by user
    SKIPPED = "SKIPPED"                            # Task skipped with confirmation
    RESUMED = "RESUMED"                            # Paused execution resumed


class ApprovalAction(str, Enum):
    """Available approval actions."""
    
    CONTINUE = "continue"           # Proceed to next task
    PAUSE = "pause"                 # Suspend execution temporarily
    RESUME = "resume"               # Resume from paused state
    RETRY = "retry"                 # Retry current action/task
    REJECT = "reject"               # Reject current work, return to agent
    SKIP = "skip"                   # Skip this task (requires confirmation)
    STOP = "stop"                   # Stop execution entirely
    EDIT_PROMPT = "edit_prompt"     # Edit prompt/acceptance criteria
    MANUAL_OVERRIDE = "manual_override"  # Direct user intervention


@dataclass
class ApprovalDecision:
    """Represents a single approval decision."""
    
    # Identification (no defaults)
    decision_id: str
    milestone_id: str
    task_id: str
    agent_id: str
    
    # State tracking
    current_state: ApprovalState
    previous_state: Optional[ApprovalState] = None
    
    # Decision details
    decision: Optional[ApprovalAction] = None
    decision_timestamp: str = ""
    
    # Prompt editing (for retry scenarios)
    edited_prompt: Optional[str] = None
    original_prompt: Optional[str] = None
    
    # Reasoning
    reason: str = ""
    
    # Metadata
    confirmation_required: bool = False
    confirmed_by: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert approval decision to dictionary."""
        return {
            "decision_id": self.decision_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "decision": self.decision.value if self.decision else None,
            "decision_timestamp": self.decision_timestamp,
            "edited_prompt": self.edited_prompt,
            "original_prompt": self.original_prompt,
            "reason": self.reason,
            "confirmation_required": self.confirmation_required,
            "confirmed_by": self.confirmed_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalDecision":
        """Create ApprovalDecision from dictionary."""
        return cls(
            decision_id=data.get("decision_id", ""),
            milestone_id=data.get("milestone_id", ""),
            task_id=data.get("task_id", ""),
            agent_id=data.get("agent_id", ""),
            current_state=ApprovalState(data.get("current_state", "WAITING_FOR_APPROVAL")),
            previous_state=ApprovalState(data.get("previous_state")) if data.get("previous_state") else None,
            decision=ApprovalAction(data.get("decision")) if data.get("decision") else None,
            decision_timestamp=data.get("decision_timestamp", ""),
            edited_prompt=data.get("edited_prompt"),
            original_prompt=data.get("original_prompt"),
            reason=data.get("reason", ""),
            confirmation_required=data.get("confirmation_required", False),
            confirmed_by=data.get("confirmed_by", ""),
        )


@dataclass
class ApprovalRequest:
    """Represents an approval request from an agent."""
    
    # Identification (no defaults)
    request_id: str
    milestone_id: str
    task_id: str
    agent_id: str
    
    # Acceptance criteria status (fields with defaults)
    acceptance_criteria_met: List[str] = field(default_factory=list)
    acceptance_criteria_missing: List[str] = field(default_factory=list)
    
    # Current state
    state: ApprovalState = ApprovalState.WAITING_FOR_APPROVAL
    
    # Pending action tracking
    pending_action: Optional[ApprovalAction] = None
    
    # Metadata
    request_timestamp: str = ""
    timeout_seconds: int = 300
    
    # Additional fields with defaults
    task_title: str = ""
    description: str = ""
    agent_output: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert approval request to dictionary."""
        return {
            "request_id": self.request_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "description": self.description,
            "agent_id": self.agent_id,
            "agent_output": self.agent_output,
            "acceptance_criteria_met": self.acceptance_criteria_met,
            "acceptance_criteria_missing": self.acceptance_criteria_missing,
            "state": self.state.value,
            "pending_action": self.pending_action.value if self.pending_action else None,
            "request_timestamp": self.request_timestamp,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalRequest":
        """Create ApprovalRequest from dictionary."""
        return cls(
            request_id=data.get("request_id", ""),
            milestone_id=data.get("milestone_id", ""),
            task_id=data.get("task_id", ""),
            task_title=data.get("task_title", ""),
            description=data.get("description", ""),
            agent_id=data.get("agent_id", ""),
            agent_output=data.get("agent_output"),
            acceptance_criteria_met=data.get("acceptance_criteria_met", []),
            acceptance_criteria_missing=data.get("acceptance_criteria_missing", []),
            state=ApprovalState(data.get("state", "WAITING_FOR_APPROVAL")),
            pending_action=ApprovalAction(data.get("pending_action")) if data.get("pending_action") else None,
            request_timestamp=data.get("request_timestamp", ""),
            timeout_seconds=data.get("timeout_seconds", 300),
        )


@dataclass
class ApprovalHistoryEntry:
    """Represents a state transition in approval history."""
    
    entry_id: str
    decision_id: str
    transition_from: ApprovalState
    transition_to: ApprovalState
    action_taken: Optional[ApprovalAction] = None
    timestamp: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert history entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "decision_id": self.decision_id,
            "transition_from": self.transition_from.value,
            "transition_to": self.transition_to.value,
            "action_taken": self.action_taken.value if self.action_taken else None,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalHistoryEntry":
        """Create ApprovalHistoryEntry from dictionary."""
        return cls(
            entry_id=data.get("entry_id", ""),
            decision_id=data.get("decision_id", ""),
            transition_from=ApprovalState(data.get("transition_from")),
            transition_to=ApprovalState(data.get("transition_to")),
            action_taken=ApprovalAction(data.get("action_taken")) if data.get("action_taken") else None,
            timestamp=data.get("timestamp", ""),
            notes=data.get("notes", ""),
        )


class ApprovalStateMachine:
    """
    State machine for managing approval workflow transitions.
    
    Supports all required transitions:
    - WAITING_FOR_APPROVAL → APPROVED (Continue)
    - WAITING_FOR_APPROVAL → REJECTED (Reject)
    - WAITING_FOR_APPROVAL → PAUSED (Pause)
    - WAITING_FOR_APPROVAL → SKIPPED (Skip with confirmation)
    - PAUSED → RESUMED (Resume)
    - Any state → STOPPED (Stop)
    """
    
    # Valid transitions from each state
    VALID_TRANSITIONS = {
        ApprovalState.WAITING_FOR_APPROVAL: [
            ApprovalState.APPROVED,
            ApprovalState.REJECTED,
            ApprovalState.PAUSED,
            ApprovalState.STOPPED,
            ApprovalState.SKIPPED,
        ],
        ApprovalState.APPROVED: [ApprovalState.APPROVED],  # Terminal state
        ApprovalState.REJECTED: [ApprovalState.REJECTED],  # Terminal state
        ApprovalState.PAUSED: [ApprovalState.RESUMED, ApprovalState.STOPPED],
        ApprovalState.RESUMED: [ApprovalState.RESUMED],  # Terminal state
        ApprovalState.STOPPED: [ApprovalState.STOPPED],  # Terminal state
        ApprovalState.SKIPPED: [ApprovalState.SKIPPED],  # Terminal state
    }
    
    def __init__(self):
        self._current_decision: Optional[ApprovalDecision] = None
    
    def set_current_decision(self, decision: ApprovalDecision) -> None:
        """Set the current active approval decision."""
        self._current_decision = decision
    
    def get_current_decision(self) -> Optional[ApprovalDecision]:
        """Get the current active approval decision."""
        return self._current_decision
    
    def is_waiting_for_approval(self) -> bool:
        """Check if currently waiting for user approval."""
        if not self._current_decision:
            return False
        return self._current_decision.current_state == ApprovalState.WAITING_FOR_APPROVAL
    
    def is_paused(self) -> bool:
        """Check if execution is paused."""
        if not self._current_decision:
            return False
        return self._current_decision.current_state == ApprovalState.PAUSED
    
    def is_terminal_state(self) -> bool:
        """Check if in a terminal state (no further transitions)."""
        if not self._current_decision:
            return False
        terminal_states = [
            ApprovalState.APPROVED,
            ApprovalState.REJECTED,
            ApprovalState.STOPPED,
            ApprovalState.SKIPPED,
        ]
        return self._current_decision.current_state in terminal_states
    
    def transition(self, action: ApprovalAction) -> tuple[bool, Optional[str]]:
        """
        Process an approval action and transition state.
        
        Args:
            action: The approval action to take
            
        Returns:
            (success, error_message) tuple
        """
        if not self._current_decision:
            return False, "No active decision"
        
        current_state = self._current_decision.current_state
        valid_transitions = self.VALID_TRANSITIONS.get(current_state, [])
        
        if action not in valid_transitions:
            return False, f"Action '{action.value}' not valid for state '{current_state.value}'"
        
        # Record previous state before transition
        previous_state = self._current_decision.current_state
        self._current_decision.previous_state = previous_state
        
        # Apply the new state and action
        new_state_str = action.value.upper() if action.value else current_state.value
        new_state = ApprovalState(new_state_str) if new_state_str in [s.value for s in ApprovalState] else current_state
        self._current_decision.current_state = new_state
        self._current_decision.decision = action
        
        return True, None
    
    def stop(self) -> tuple[bool, Optional[str]]:
        """Stop execution from any state."""
        if not self._current_decision:
            return False, "No active decision"
        
        previous_state = self._current_decision.current_state
        self._current_decision.previous_state = previous_state
        self._current_decision.current_state = ApprovalState.STOPPED
        self._current_decision.decision = ApprovalAction.STOP
        
        return True, None


class ApprovalStateManager:
    """
    Manager for persistence and retrieval of approval state.
    
    Tracks:
    - Current pending approvals
    - Historical decisions
    - Execution pauses/resumes
    - State transitions
    """
    
    def __init__(self, state_dir: str = "ai_agents/state"):
        self.state_dir = state_dir
        self.approvals_file = f"{state_dir}/approval_decisions.json"
        self.history_file = f"{state_dir}/approval_history.jsonl"
        self.pending_file = f"{state_dir}/pending_approvals.json"
    
    def load_pending(self) -> List[ApprovalRequest]:
        """Load all pending approvals from disk."""
        try:
            if not self._file_exists(self.pending_file):
                return []
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [ApprovalRequest.from_dict(d) for d in data]
        except Exception:
            return []
    
    def save_pending(self, requests: List[ApprovalRequest]) -> None:
        """Save pending approvals to disk."""
        try:
            import os
            os.makedirs(self.state_dir, exist_ok=True)
            
            # Filter out terminal states (they're not really pending)
            terminal_states = [ApprovalState.APPROVED, ApprovalState.REJECTED, 
                             ApprovalState.STOPPED, ApprovalState.SKIPPED]
            active_requests = [r for r in requests 
                            if r.state not in terminal_states]
            
            data = {r.request_id: r.to_dict() for r in active_requests}
            
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[ApprovalManager] Failed to save pending approvals: {e}")
    
    def load_decisions(self) -> List[ApprovalDecision]:
        """Load all historical decisions from disk."""
        try:
            if not self._file_exists(self.approvals_file):
                return []
            with open(self.approvals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [ApprovalDecision.from_dict(d) for d in data]
        except Exception:
            return []
    
    def save_decision(self, decision: ApprovalDecision) -> None:
        """Save an approval decision to disk."""
        try:
            import os
            os.makedirs(self.state_dir, exist_ok=True)
            
            # Load existing decisions
            decisions = self.load_decisions()
            
            # Add new decision
            if decision.decision_id not in [d.decision_id for d in decisions]:
                decisions.append(decision)
            
            # Sort by timestamp
            decisions.sort(key=lambda d: d.decision_timestamp, reverse=True)
            
            with open(self.approvals_file, 'w', encoding='utf-8') as f:
                json.dump([d.to_dict() for d in decisions], f, indent=2)
                
        except Exception as e:
            print(f"[ApprovalManager] Failed to save decision: {e}")
    
    def load_history(self) -> List[ApprovalHistoryEntry]:
        """Load approval history from journal."""
        try:
            history = []
            if not self._file_exists(self.history_file):
                return history
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry = ApprovalHistoryEntry.from_dict(data)
                        if entry.entry_id not in [h.entry_id for h in history]:
                            history.append(entry)
                    except Exception:
                        continue
            
            return sorted(history, key=lambda h: h.timestamp)
            
        except Exception:
            return []
    
    def record_transition(self, decision: ApprovalDecision, 
                         transition_from: ApprovalState,
                         transition_to: ApprovalState,
                         action_taken: Optional[ApprovalAction] = None,
                         notes: str = "") -> None:
        """Record a state transition in history."""
        try:
            entry = ApprovalHistoryEntry(
                entry_id="TRANS-{}".format(len(self.load_history()) + 1),
                decision_id=decision.decision_id,
                transition_from=transition_from,
                transition_to=transition_to,
                action_taken=action_taken,
                timestamp=datetime.now(timezone.utc).isoformat(),
                notes=notes,
            )
            self.load_history()  # Ensure we have existing entries for ID uniqueness
            
            with open(self.history_file, 'a', encoding='utf-8') as f:
                json_str = json.dumps(entry.to_dict()) + "\n"
                f.write(json_str)
                
        except Exception as e:
            print(f"[ApprovalManager] Failed to record transition: {e}")
    
    def _file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        import os
        return os.path.exists(path)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of approval state."""
        pending = self.load_pending()
        decisions = self.load_decisions()
        
        return {
            "pending_count": len(pending),
            "decision_count": len(decisions),
            "history_entries": len(self.load_history()),
            "has_pending_waiting": any(
                p.state == ApprovalState.WAITING_FOR_APPROVAL 
                for p in pending
            ),
            "has_paused": any(
                p.state == ApprovalState.PAUSED for p in pending
            ),
        }


def get_approval_prompt(task: Dict[str, Any], agent_output: Optional[Dict] = None) -> str:
    """
    Generate a prompt for user approval decision.
    
    Args:
        task: Task information (title, description, acceptance criteria)
        agent_output: Agent's output/work to review
        
    Returns:
        Formatted prompt string with options
    """
    task_title = task.get("title", "Task")
    task_desc = task.get("description", "")[:500]  # Limit length
    
    lines = [
        "=" * 70,
        f"📋 APPROVAL REQUEST - {task_title}",
        "=" * 70,
        "",
        "📝 Task Description:",
        "-" * 40,
    ]
    
    if task_desc:
        lines.append(task_desc)
        lines.append("")
    
    lines.extend([
        "📊 Agent Output Review:",
        "-" * 40,
        "(See attached output below)" if agent_output else "No output to review",
        "",
        "⚡ Acceptance Criteria Status:",
    ])
    
    # Add criteria status
    for criterion in task.get("acceptance_criteria", []):
        lines.append(f"  ✓ {criterion}")
    
    lines.extend([
        "",
        "💡 RECOMMENDATION:",
        "-" * 40,
        "Review agent's work and choose an action:",
        "",
    ])
    
    options = [
        "[C] Continue - Approve and proceed to next task",
        "[P] Pause     - Suspend execution temporarily",
        "[R] Resume    - Resume from paused state",
        "[Re] Retry    - Retrying the current action",
        "[J] Reject    - Reject work, return to agent for revision",
        "[Sk] Skip     - Skip this task (requires confirmation)",
        "[St] Stop     - Stop execution entirely",
        "[Ed] Edit Prompt - Modify prompt/acceptance criteria before retry",
        "[Mo] Manual Override - Direct user intervention",
    ]
    
    lines.extend(options)
    lines.append("=" * 70)
    
    return "\n".join(lines)


def get_pause_resume_prompt(reason: Optional[str] = None) -> str:
    """Generate pause/resume prompt."""
    prefix = reason or "Execution was paused."
    lines = [
        "=" * 70,
        "⏸️  EXECUTION PAUSED",
        "=" * 70,
        "",
        prefix,
        "",
        "💡 You can now choose to:",
        "",
        "[R] Resume - Continue execution from where it left off",
        "[St] Stop  - Permanently stop this milestone",
    ]
    
    return "\n".join(lines)


def get_retry_prompt(task: Dict[str, Any], agent: str) -> str:
    """Generate retry prompt with optional edit."""
    lines = [
        "=" * 70,
        f"🔄 RETRY REQUEST for {task.get('title', 'Task')}",
        "=" * 70,
        "",
        f"Agent: {agent}",
        "",
        "⚡ Would you like to:",
        "",
        "[Y] Yes - Retry with current prompt/acceptance criteria",
        "[N] No  - Edit prompt/acceptance criteria first",
    ]
    
    if task.get("acceptance_criteria"):
        lines.extend([
            "",
            "💡 Current Acceptance Criteria:",
        ])
        for i, crit in enumerate(task.get("acceptance_criteria", []), 1):
            lines.append(f"  {i}. {crit}")
    
    return "\n".join(lines)


def get_edit_prompt_prompt(task: Dict[str, Any], agent: str) -> str:
    """Generate prompt editing interface."""
    lines = [
        "=" * 70,
        "✏️  EDIT PROMPT/ACCEPTANCE CRITERIA",
        "=" * 70,
        "",
        f"Agent: {agent}",
        f"Task: {task.get('title', 'Task')}",
        "",
        "📝 You can modify:",
    ]
    
    fields = [
        ("Prompt", task.get("prompt", "")),
        ("Acceptance Criteria", str(task.get("acceptance_criteria", []))),
        ("Additional Notes/Instructions", ""),
    ]
    
    for field_name, field_value in fields:
        lines.append(f"  {field_name} (current):")
        if field_value:
            truncated = repr(field_value)[:200]
            lines.append(f"      {truncated}")
        else:
            lines.append("      <empty>")
    
    return "\n".join(lines)
