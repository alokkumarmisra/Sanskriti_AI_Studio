"""
Execution History Module for Sanskriti AI Studio AI Agents.

This module provides execution history and tracking for all messages routed through the Communication Bus.
It maintains a log of all communication events with metadata about senders, receivers, timing,
and outcomes.

Tracking Capabilities:
    - Sender/Receiver identification
    - Start/end time tracking
    - Success/failure status
    - Retry attempts count
    - Correlation ID preservation
    - Message type classification

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images in historical records.

Version: 1.0
Last Updated: 2026-08-05
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    """
    Represents a single entry in the execution history.
    
    Tracks all aspects of message communication including:
    - Which agent sent the message
    - Which agents received it
    - When it was sent and completed
    - Whether it succeeded or failed
    - How many retry attempts were made
    """
    
    # Message identification
    message_id: str                          # Unique message ID
    correlation_id: str = ""                 # Correlation ID for linked operations
    
    # Routing information
    source_agent: str = ""                   # Agent that sent the message
    destination_agents: List[str] = field(default_factory=list)  # Recipients
    
    # Message classification
    message_type: str = "EVENT"              # Type of communication (REQUEST/RESPONSE/ERROR/etc.)
    
    # Timing information
    created_at: str = ""                     # When message was created
    sent_at: str = ""                        # When message was sent
    completed_at: str = ""                   # When message completed (success or failure)
    
    # Outcome tracking
    success: bool = False                    # Whether the message succeeded
    error_type: str = ""                     # Error type if failed
    error_message: str = ""                  # Error description if failed
    
    # Retry information
    retry_count: int = 0                     # How many times this was retried
    
    # Additional metadata
    payload_summary: str = ""                # Brief summary of payload (for indexing)
    
    # Status
    status: str = "PENDING"                  # Current status (PENDING/SENT/DONE)
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "source_agent": self.source_agent,
            "destination_agents": self.destination_agents,
            "message_type": self.message_type,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "completed_at": self.completed_at,
            "success": self.success,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "payload_summary": self.payload_summary,
            "status": self.status,
        }


class ExecutionHistory:
    """
    Maintains and manages execution history for all messages.
    
    The History tracks:
    - All messages sent through the bus
    - Message flow and routing decisions
    - Success/failure outcomes
    - Retry attempts and dead-letter queue entries
    
    Usage:
        history = ExecutionHistory()
        
        # Add a message to history
        entry = HistoryEntry(
            message_id="MSG-001",
            source_agent="planner_agent",
            destination_agents=["coding_agent"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        history.add(entry)
        
        # Query for messages by agent
        planner_messages = history.get_by_source("planner_agent")
    """
    
    def __init__(self, max_entries: int = 10000):
        """
        Initialize the execution history.
        
        Args:
            max_entries: Maximum number of entries to keep (oldest removed when exceeded)
        """
        self.entries: List[HistoryEntry] = []
        self.max_entries = max_entries
    
    def add(self, entry: HistoryEntry) -> None:
        """
        Add a new entry to the history.
        
        Args:
            entry: History entry to add
        
        Raises:
            ValueError: If entry is missing required fields
        """
        # Validate required fields
        if not entry.message_id:
            raise ValueError("Entry must have a message_id")
        
        # Add entry
        self.entries.append(entry)
        
        # Remove oldest entries if over limit
        while len(self.entries) > self.max_entries:
            self.entries.pop(0)
    
    def add_batch(self, entries: List[HistoryEntry]) -> None:
        """
        Add multiple entries to the history.
        
        Args:
            entries: List of entries to add
        """
        for entry in entries:
            self.add(entry)
    
    def get_by_message_id(self, message_id: str) -> Optional[HistoryEntry]:
        """
        Get an entry by message ID.
        
        Args:
            message_id: Message ID to look up
        
        Returns:
            HistoryEntry if found, None otherwise
        """
        for entry in self.entries:
            if entry.message_id == message_id:
                return entry
        return None
    
    def get_by_correlation_id(self, correlation_id: str) -> List[HistoryEntry]:
        """
        Get all entries associated with a correlation ID.
        
        Args:
            correlation_id: Correlation ID to look up
        
        Returns:
            List of matching history entries
        """
        return [e for e in self.entries if e.correlation_id == correlation_id]
    
    def get_by_source_agent(self, source_agent: str) -> List[HistoryEntry]:
        """
        Get all messages sent by a specific agent.
        
        Args:
            source_agent: Agent name to filter by
        
        Returns:
            List of entries from this agent
        """
        return [e for e in self.entries if e.source_agent == source_agent]
    
    def get_by_destination_agent(self, destination_agent: str) -> List[HistoryEntry]:
        """
        Get all messages sent to a specific agent.
        
        Args:
            destination_agent: Agent name to filter by
        
        Returns:
            List of entries for this agent
        """
        return [e for e in self.entries if destination_agent in e.destination_agents]
    
    def get_by_type(self, msg_type: str) -> List[HistoryEntry]:
        """
        Get all messages of a specific type.
        
        Args:
            msg_type: Message type (REQUEST/RESPONSE/ERROR/etc.)
        
        Returns:
            List of entries with this type
        """
        return [e for e in self.entries if e.message_type == msg_type]
    
    def get_by_status(self, status: str) -> List[HistoryEntry]:
        """
        Get all messages with a specific status.
        
        Args:
            status: Status to filter by (PENDING/SENT/DONE/FAILED)
        
        Returns:
            List of entries with this status
        """
        return [e for e in self.entries if e.status == status]
    
    def get_successful_messages(self) -> List[HistoryEntry]:
        """
        Get all successful messages.
        
        Returns:
            List of successful entries
        """
        return [e for e in self.entries if e.success]
    
    def get_failed_messages(self) -> List[HistoryEntry]:
        """
        Get all failed messages.
        
        Returns:
            List of failed entries
        """
        return [e for e in self.entries if not e.success]
    
    def get_pending_messages(self) -> List[HistoryEntry]:
        """
        Get all pending messages (not yet completed).
        
        Returns:
            List of pending entries
        """
        return [e for e in self.entries if e.status == "PENDING"]
    
    def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[HistoryEntry]:
        """
        Get messages within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            List of entries within the range
        """
        start_str = start_time.isoformat()
        end_str = end_time.isoformat()
        
        return [
            e for e in self.entries
            if start_str <= e.created_at <= end_str
        ]
    
    def get_by_retry_count(self, retry_count: int) -> List[HistoryEntry]:
        """
        Get messages with a specific retry count.
        
        Args:
            retry_count: Number of retries to filter by
        
        Returns:
            List of entries with this retry count
        """
        return [e for e in self.entries if e.retry_count == retry_count]
    
    def get_correlation_group(self, correlation_id: str) -> Dict[str, Any]:
        """
        Get all messages in a correlation group.
        
        Args:
            correlation_id: Correlation ID to look up
        
        Returns:
            Dictionary with correlation group information
        """
        entries = self.get_by_correlation_id(correlation_id)
        
        if not entries:
            return {
                "correlation_id": correlation_id,
                "message_count": 0,
                "entries": [],
            }
        
        # Get all unique source/destination combinations
        sources = set(e.source_agent for e in entries)
        destinations = set()
        for e in entries:
            destinations.update(e.destination_agents)
        
        # Count by type
        by_type = {}
        for e in entries:
            t = e.message_type
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "correlation_id": correlation_id,
            "message_count": len(entries),
            "sources": list(sources),
            "destinations": list(destinations),
            "by_type": by_type,
            "entries": [e._to_dict() for e in entries],
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.entries)
        successful = len(self.get_successful_messages())
        failed = len(self.get_failed_messages())
        pending = len(self.get_pending_messages())
        errors = len(self.get_by_type("ERROR"))
        
        return {
            "total_messages": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "errors": errors,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }
    
    def clear(self) -> None:
        """Clear all history entries."""
        self.entries.clear()
    
    def truncate(self, keep: int) -> int:
        """
        Truncate history to keep only most recent entries.
        
        Args:
            keep: Number of entries to keep
        
        Returns:
            Number of entries removed
        """
        removed = len(self.entries) - keep
        self.entries = self.entries[-keep:] if keep > 0 else []
        return removed
    
    def clear_by_agent(self, agent: str) -> int:
        """
        Clear all messages from/to a specific agent.
        
        Args:
            agent: Agent name to filter by
        
        Returns:
            Number of entries removed
        """
        initial_len = len(self.entries)
        self.entries = [e for e in self.entries if agent not in e.source_agent and agent not in e.destination_agents]
        return initial_len - len(self.entries)


# Convenience function to create an entry
def create_history_entry(
    message_id: str,
    source_agent: str,
    destination_agents: List[str],
    message_type: str = "EVENT",
    success: bool = True,
    correlation_id: Optional[str] = None,
) -> HistoryEntry:
    """
    Create a history entry for the given message.
    
    Args:
        message_id: Message ID
        source_agent: Sending agent
        destination_agents: Recipient agents
        message_type: Type of communication
        success: Whether it succeeded
        correlation_id: Correlation ID (optional)
    
    Returns:
        HistoryEntry instance
    """
    now = datetime.now(timezone.utc).isoformat()
    
    return HistoryEntry(
        message_id=message_id,
        source_agent=source_agent,
        destination_agents=destination_agents,
        message_type=message_type,
        success=success,
        correlation_id=correlation_id or "",
        created_at=now,
        sent_at=now,
        completed_at=now,
    )
