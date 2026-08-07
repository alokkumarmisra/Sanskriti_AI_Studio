"""
Message Model for Sanskriti AI Studio AI Agents.

This module defines the standard message schema used by all agents for communication.
The Message model provides a canonical format for all agent-to-agent interactions.

Message Schema:
    {
        "message_id": "UNIQUE-ID-001",           # Unique identifier for this message
        "correlation_id": "CORR-001",            # Links related operations across messages
        "source_agent": "planner_agent",         # Agent that sent the message
        "destination_agent": ["coder_agent"],   # Primary recipient(s) - can be single or list for broadcast
        "message_type": "REQUEST|RESPONSE|EVENT|ERROR",  # Type of communication
        "task_id": "STEP-PLANNER-202608051530",    # Task being worked on
        "milestone_id": "MILESTONE-6.6",         # Milestone context
        "timestamp": "2026-08-05T15:30:00Z",   # ISO-8601 timestamp
        "payload": {...},                        # Message-specific data
        "priority": "HIGH|MEDIUM|LOW",           # Processing priority
        "retry_count": 0,                        # How many times this has been retried
        "status": "PENDING|SENT|DELIVERED|FAILED"  # Current message status
    }

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images or visual data in message payloads.

Version: 1.0
Last Updated: 2026-08-05
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


def _ensure_destination_list(dest: Union[str, List[str]]) -> List[str]:
    """Ensure destination is a flat list of strings."""
    if isinstance(dest, str):
        return [dest]
    elif isinstance(dest, list):
        # Flatten nested lists and filter empty strings
        result = []
        for d in dest:
            if isinstance(d, str) and d.strip():
                result.append(d.strip())
        return result
    return []


class MessageType(Enum):
    """Types of messages in the communication bus."""
    
    REQUEST = "REQUEST"              # Request for action/response from another agent
    RESPONSE = "RESPONSE"            # Response to a previous request
    EVENT = "EVENT"                  # Event notification (fire-and-forget)
    ERROR = "ERROR"                  # Error or exception notification
    
    @classmethod
    def is_request(cls, msg_type: str) -> bool:
        """Check if message type represents a request."""
        return msg_type == cls.REQUEST.value
    
    @classmethod
    def is_response(cls, msg_type: str) -> bool:
        """Check if message type represents a response."""
        return msg_type == cls.RESPONSE.value
    
    @classmethod
    def is_event(cls, msg_type: str) -> bool:
        """Check if message type represents an event."""
        return msg_type == cls.EVENT.value
    
    @classmethod
    def is_error(cls, msg_type: str) -> bool:
        """Check if message type represents an error."""
        return msg_type == cls.ERROR.value


class MessageStatus(Enum):
    """Status of a message in transit or processing."""
    
    PENDING = "PENDING"              # Message created, waiting to be sent
    SENT = "SENT"                    # Message has been sent to router
    DELIVERED = "DELIVERED"          # Message was successfully delivered
    FAILED = "FAILED"                # Message failed delivery (moved to DDLQ if retries exhausted)
    
    @classmethod
    def is_pending(cls, status: str) -> bool:
        return status == cls.PENDING.value
    
    @classmethod
    def is_sent(cls, status: str) -> bool:
        return status in [cls.SENT.value, cls.DELIVERED.value]
    
    @classmethod
    def is_failed(cls, status: str) -> bool:
        return status == cls.FAILED.value


class MessagePriority(Enum):
    """Priority levels for message processing."""
    
    CRITICAL = "CRITICAL"            # Must be processed immediately (e.g., system errors)
    HIGH = "HIGH"                    # High priority (should be processed soon)
    MEDIUM = "MEDIUM"                # Normal priority (default)
    LOW = "LOW"                      # Low priority (can wait for other tasks)


@dataclass
class Message:
    """
    Standard message schema for agent communication.
    
    All agents must use this dataclass to create and process messages.
    The router will validate that all required fields are present.
    """
    
    # Identification
    message_id: str                  # Unique identifier (auto-generated if not provided)
    correlation_id: str              # Links related operations across messages
    
    # Routing information
    source_agent: str                # Agent that sent this message
    destination_agent: List[str]     # Primary recipient(s) - single or multiple for broadcast
    
    # Message classification
    message_type: MessageType        # Type of communication
    payload: Dict[str, Any] = field(default_factory=dict)                     # Message-specific data
    
    # Task context
    task_id: str = ""                # Optional task identifier
    milestone_id: str = ""           # Optional milestone identifier
    
    # Timing and status
    timestamp: str = ""              # ISO-8601 formatted timestamp
    priority: MessagePriority = MessagePriority.MEDIUM                         # Processing priority
    
    # Retry tracking
    retry_count: int = 0             # How many times this message has been retried
    
    # Lifecycle status
    status: MessageStatus = MessageStatus.PENDING                              # Current status
    
    @classmethod
    def create_request(
        cls,
        source_agent: str,
        destination_agent: Union[str, List[str]],
        task_id: str,
        milestone_id: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM,
        correlation_id: Optional[str] = None,
    ) -> "Message":
        """Create a new request message with auto-generated ID."""
        
        if correlation_id is None:
            correlation_id = f"CORR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{source_agent}"
        
        dest_list = _ensure_destination_list(destination_agent)
        
        message_id = f"{source_agent.upper()}->{dest_list[0].upper()}-{int(datetime.now().timestamp())}{correlation_id[-6:]}"
        
        return cls(
            message_id=message_id,
            correlation_id=correlation_id,
            source_agent=source_agent,
            destination_agent=dest_list,
            message_type=MessageType.REQUEST,
            payload=payload,
            task_id=task_id,
            milestone_id=milestone_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            priority=priority,
            retry_count=0,
            status=MessageStatus.PENDING,
        )
    
    @classmethod
    def create_response(
        cls,
        source_agent: str,
        destination_agent: Union[str, List[str]],
        correlation_id: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.RESPONSE,
    ) -> "Message":
        """Create a response message to a previous request."""
        
        dest_list = _ensure_destination_list(destination_agent)
        
        message_id = f"{source_agent.upper()}-{correlation_id[-6:]}"
        
        return cls(
            message_id=message_id,
            correlation_id=correlation_id,
            source_agent=source_agent,
            destination_agent=dest_list,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            retry_count=0,
            status=MessageStatus.PENDING,
        )
    
    @classmethod
    def create_event(
        cls,
        source_agent: str,
        destination_agent: Union[str, List[str]],
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.EVENT,
    ) -> "Message":
        """Create an event notification message (fire-and-forget)."""
        
        dest_list = _ensure_destination_list(destination_agent)
        
        message_id = f"{source_agent.upper()}-EVENT-{int(datetime.now().timestamp())}"
        
        return cls(
            message_id=message_id,
            correlation_id=payload.get("correlation_id", ""),
            source_agent=source_agent,
            destination_agent=dest_list,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            retry_count=0,
            status=MessageStatus.PENDING,
        )
    
    @classmethod
    def create_error(
        cls,
        source_agent: str,
        destination_agent: Union[str, List[str]],
        correlation_id: str,
        error_type: str,
        error_message: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """Create an error message for notification."""
        
        payload = payload or {
            "error_type": error_type,
            "error_message": error_message,
        }
        
        dest_list = _ensure_destination_list(destination_agent)
        
        return cls(
            message_id=f"{source_agent.upper()}-ERROR-{correlation_id[-6:]}",
            correlation_id=correlation_id,
            source_agent=source_agent,
            destination_agent=dest_list,
            message_type=MessageType.ERROR,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            retry_count=0,
            status=MessageStatus.PENDING,
        )
    
    def is_retryable(self) -> bool:
        """Check if this message can be retried."""
        return self.retry_count < 3
    
    def increment_retry(self) -> "Message":
        """Increment retry counter and return new message."""
        return Message(
            message_id=self.message_id,
            correlation_id=self.correlation_id,
            source_agent=self.source_agent,
            destination_agent=list(self.destination_agent),
            message_type=self.message_type,
            payload=dict(self.payload),
            task_id=self.task_id,
            milestone_id=self.milestone_id,
            timestamp=self.timestamp,
            priority=self.priority,
            retry_count=self.retry_count + 1,
            status=MessageStatus.PENDING,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "source_agent": self.source_agent,
            "destination_agent": self.destination_agent,
            "message_type": self.message_type.value,
            "task_id": self.task_id,
            "milestone_id": self.milestone_id,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "payload": self.payload,
            "retry_count": self.retry_count,
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create Message from dictionary."""
        
        # Convert string values back to enums if needed
        message_type = MessageType(data.get("message_type", "REQUEST"))
        priority = MessagePriority(data.get("priority", "MEDIUM"))
        status = MessageStatus(data.get("status", "PENDING"))
        
        return cls(
            message_id=data["message_id"],
            correlation_id=data.get("correlation_id", ""),
            source_agent=data["source_agent"],
            destination_agent=data.get("destination_agent", []),
            message_type=message_type,
            payload=data.get("payload", {}),
            task_id=data.get("task_id", ""),
            milestone_id=data.get("milestone_id", ""),
            timestamp=data.get("timestamp", ""),
            priority=priority,
            retry_count=data.get("retry_count", 0),
            status=status,
        )
    
    def __str__(self) -> str:
        """String representation of the message."""
        return f"Message({self.message_id}, {self.source_agent}→{', '.join(self.destination_agent)}, {self.message_type.value})"
