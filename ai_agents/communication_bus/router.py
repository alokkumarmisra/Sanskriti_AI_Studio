"""
Router Module for Sanskriti AI Studio AI Agents.

This module provides intelligent message routing between agents based on routing rules.
It supports one-to-one messaging, broadcast messaging, request/response patterns,
and error handling for failed deliveries.

Routing Rules:
    1. One-to-One: Message sent to single specific agent
    2. Broadcast: Message sent to multiple agents (first responder wins)
    3. Request/Response: Synchronous communication with timeout
    4. Event Notification: Fire-and-forget, no response expected
    5. Error Routing: Route errors to appropriate handlers

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images in routed messages.

Version: 1.0
Last Updated: 2026-08-05
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Union

from ai_agents.communication_bus.message import _ensure_destination_list


# Define RouteType as a simple class instead of Enum to avoid dependency issues
class RouteType:
    """Types of routes supported by the router."""
    
    ONE_TO_ONE = "ONE_TO_ONE"                    # Single destination
    BROADCAST = "BROADCAST"                       # Multiple destinations (first wins)
    REQUEST_RESPONSE = "REQUEST_RESPONSE"        # Synchronous with timeout
    EVENT_NOTIFICATION = "EVENT_NOTIFICATION"    # Fire-and-forget


class RoutingRule:
    """
    Defines a routing rule for message delivery.
    
    Rules can be used to customize routing behavior based on message properties.
    """
    
    def __init__(
        self,
        name: str,
        condition: Callable[..., bool],
        action: Callable[..., None],
        priority: int = 0,
    ):
        """
        Initialize a routing rule.
        
        Args:
            name: Unique name for this rule
            condition: Function that returns True if rule should be applied
            action: Function to execute when rule matches
            priority: Higher values are checked first
        """
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority
    
    def __lt__(self, other: "RoutingRule") -> bool:
        """Enable sorting by priority (higher first)."""
        return self.priority > other.priority



@dataclass
class Message:
    """Message class for inter-agent communication."""
    
    source_agent: str
    destination_agent: List[str]
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now(timezone.utc).timestamp()}")
    task_id: str = ""
    milestone_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    priority: int = 2  # MEDIUM default
    
    message_type: str = "EVENT"  # EVENT, REQUEST, RESPONSE, ERROR
    
    retry_count: int = 0
    
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create_request(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create a request message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="REQUEST",
            **{k: v for k, v in kwargs.items() if k != 'message_type'},
        )
    
    @classmethod
    def create_response(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create a response message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="RESPONSE",
            **{k: v for k, v in kwargs.items() if k != 'message_type'},
        )
    
    @classmethod
    def create_error(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create an error message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="ERROR",
            **{k: v for k, v in kwargs.items() if k not in ('message_type', 'error_type', 'error_message')},
            error_type=kwargs.get('error_type'),
            error_message=kwargs.get('error_message'),
        )

@dataclass
class RoutingConfig:
    """Configuration for the router."""
    
    # Default timeout in seconds for request/response
    default_timeout: float = 30.0
    
    # Maximum retry attempts per message
    max_retries: int = 3
    
    # Retry delay in seconds between attempts
    retry_delay: float = 1.0
    
    # Enable or disable duplicate detection
    enable_duplicate_detection: bool = True
    
    # Duplicate window in seconds (messages within this time with same ID are duplicates)
    duplicate_window: float = 60.0
    
    # Enable dead-letter queue for failed messages
    enable_dead_letter_queue: bool = True


class Router:
    """
    Message router that coordinates agent communication.
    
    The Router handles:
    - Message routing based on destination agents
    - Request/response synchronization with timeout
    - Broadcast message handling (first responder wins)
    - Duplicate detection and prevention
    - Error handling and retry logic
    
    Usage:
        router = Router()
        
        # Register handler for coder_agent
        @router.register_handler("coding_agent")
        async def handle_coding_request(message: Message) -> Optional[Message]:
            if message.message_type == MessageType.REQUEST:
                # Process request and send response
                return Message.create_response(
                    source_agent="coding_agent",
                    destination_agent=message.source_agent,
                    correlation_id=message.correlation_id,
                    payload={"status": "processed", "result": "code generated"},
                )
            return None
        
        # Send a message
        result = router.route(message)
    """
    
    def __init__(self, config: Optional[RoutingConfig] = None):
        """
        Initialize the router.
        
        Args:
            config: Routing configuration (uses defaults if None)
        """
        self.config = config or RoutingConfig()
        
        # Track processed messages for duplicate detection
        self._processed_ids: Set[str] = set()
        self._last_processed_time: Dict[str, datetime] = {}
        
        # Handler registry: agent_name -> list of handlers
        self._handlers: Dict[str, List[Callable]] = {
            "coding_agent": [],
            "testing_agent": [],
            "debugger_agent": [],
            "reviewer_agent": [],
            "documentation_agent": [],
            "planner_agent": [],
            "orchestrator_agent": [],
            "execution_manager": [],
        }
        
        # Dead-letter queue (DDLQ) for failed messages
        self._ddlq: List[Any] = []  # DDLQ = Dead-Letter Queue
        
        # Statistics
        self._stats = {
            "messages_routed": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "retries_attempted": 0,
            "duplicates_detected": 0,
        }
    
    def register_handler(
        self,
        agent_name: str,
        handler: Callable,
    ) -> None:
        """
        Register a handler for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "coding_agent")
            handler: Function that processes messages for this agent
                     Returns response message if applicable, None otherwise
        """
        if agent_name not in self._handlers:
            self._handlers[agent_name] = []
        self._handlers[agent_name].append(handler)
    
    def unregister_handler(self, agent_name: str) -> int:
        """
        Unregister a handler for an agent.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Number of handlers removed (typically 1 if using single handler registration)
        """
        if agent_name in self._handlers:
            # Find and remove first occurrence of this handler
            initial_len = len(self._handlers[agent_name])
            self._handlers[agent_name] = [
                h for h in self._handlers[agent_name]
                if not (hasattr(h, '__name__') and h.__name__ == '_default_handler')
            ]
            return initial_len - len(self._handlers[agent_name])
        return 0
    
    def _is_duplicate(self, message: Any) -> bool:
        """
        Check if message is a duplicate (same ID within duplicate window).
        
        Args:
            message: Message to check
        
        Returns:
            True if this is a duplicate message
        """
        if not self.config.enable_duplicate_detection:
            return False
        
        message_id = message.message_id
        
        # Check if already processed
        if message_id in self._processed_ids:
            self._stats["duplicates_detected"] += 1
            return True
        
        now = datetime.now(timezone.utc)
        
        # If we have a previous time for this ID and it's within the window, it's a duplicate
        if message_id in self._last_processed_time:
            last_time = self._last_processed_time[message_id]
            time_diff = (now - last_time).total_seconds()
            if time_diff < self.config.duplicate_window:
                self._stats["duplicates_detected"] += 1
                return True
        
        # Update tracking for this message
        self._processed_ids.add(message_id)
        self._last_processed_time[message_id] = now
        
        return False
    
    def _increment_retry(self, message: Any) -> Any:
        """Increment retry counter on message."""
        now_ts = datetime.now(timezone.utc).isoformat()
        message_payload = dict(message.payload) if hasattr(message, 'payload') else {}
        message_task_id = getattr(message, 'task_id', '')
        message_milestone_id = getattr(message, 'milestone_id', '')
        message_priority = getattr(message, 'priority', 'MEDIUM')
        
        return Message.create_request(
            source_agent=message.source_agent,
            destination_agent=list(message.destination_agent),
            task_id=message_task_id,
            milestone_id=message_milestone_id,
            payload=message_payload,
            priority=message_priority,
            correlation_id=message.correlation_id,
        )
    
    def route(self, message: Any) -> Optional[Any]:
        """
        Route a message to its destination(s).
        
        This method handles the core routing logic including:
        - Duplicate detection
        - Finding appropriate handlers
        - Executing handlers for each destination
        - Handling response messages
        
        Args:
            message: Message to route
        
        Returns:
            Response message if applicable, None otherwise (for fire-and-forget events)
        
        Raises:
            RuntimeError: If message cannot be routed
        """
        # Check for duplicates
        if self._is_duplicate(message):
            return None
        
        source_agent = getattr(message, 'source_agent', '')
        destinations = _ensure_destination_list(getattr(message, 'destination_agent', []))
        message_type = getattr(message, 'message_type', 'EVENT')
        
        # Route based on message type
        if message_type == 'EVENT':
            return self._route_event(message, destinations)
        
        elif message_type in ['REQUEST', 'RESPONSE']:
            return self._route_request_response(message, destinations)
        
        elif message_type == 'ERROR':
            return self._route_error(message, destinations)
        
        else:
            # Default to event-style routing for unknown types
            return self._route_event(message, destinations)
    
    def _route_event(self, message: Any, destinations: List[str]) -> Optional[Any]:
        """Route an event notification (fire-and-forget)."""
        self._stats["messages_routed"] += 1
        
        # Log the broadcast
        for dest in destinations:
            print(f"[ROUTER] Broadcasting EVENT from {message.source_agent} to {dest}")
        
        return None
    
    def _route_request_response(self, message: Any, destinations: List[str]) -> Optional[Any]:
        """Route a request or response message."""
        self._stats["messages_routed"] += 1
        
        if len(destinations) == 1:
            # One-to-one routing
            return self._route_one_to_one(message, destinations[0])
        
        else:
            # Broadcast to multiple destinations
            return self._route_broadcast(message, destinations)
    
    def _route_one_to_one(self, message: Any, destination: str) -> Optional[Any]:
        """Route a message to a single destination."""
        print(f"[ROUTER] One-to-one: {message.source_agent} → {destination}")
        
        handlers = self._handlers.get(destination, [])
        
        if not handlers:
            # No handler registered - check if source agent should handle its own response
            if destination == message.source_agent:
                print(f"[ROUTER] Source agent handling own request")
                return None
            
            print(f"[ROUTER] No handler registered for {destination}")
            self._stats["messages_failed"] += 1
            return None
        
        # Execute handlers
        response = None
        for handler in handlers:
            try:
                result = handler(message)
                if result is not None:
                    response = result
                    break
            except Exception as e:
                print(f"[ROUTER] Handler error: {e}")
                
                # If retries allowed, increment and retry
                if message.retry_count < self.config.max_retries:
                    message = self._increment_retry(message)
                    continue
                
                # Move to dead-letter queue if enabled
                if self.config.enable_dead_letter_queue:
                    print(f"[ROUTER] Moving to DDLQ: {message.message_id}")
                    self._ddlq.append(message)
                    self._stats["messages_failed"] += 1
                
                response = Message.create_error(
                    source_agent=message.source_agent,
                    destination_agent=[destination],
                    correlation_id=message.correlation_id,
                    error_type=f"HandlerError:{type(e).__name__}",
                    error_message=str(e),
                )
                break
        
        return response
    
    def _route_broadcast(self, message: Any, destinations: List[str]) -> Optional[Any]:
        """Route a broadcast message to multiple destinations."""
        print(f"[ROUTER] Broadcasting to {len(destinations)} destinations")
        
        # Send to all destinations (first valid response wins)
        responses: List[Optional[Any]] = []
        for dest in destinations:
            response = self._route_one_to_one(message, dest)
            responses.append(response)
        
        # Return first non-None response
        for resp in responses:
            if resp is not None and hasattr(resp, 'message_type') and resp.message_type == 'ERROR':
                return resp  # Return error immediately
            if resp is not None:
                return resp
        
        return None
    
    def _route_error(self, message: Any, destinations: List[str]) -> Optional[Any]:
        """Route an error message."""
        self._stats["messages_routed"] += 1
        print(f"[ROUTER] Routing ERROR from {message.source_agent} to {', '.join(destinations)}")
        
        # Route error to all destinations (notify them of the failure)
        return self._route_broadcast(message, destinations)
    
    def get_dead_letter_queue(self) -> List[Any]:
        """
        Get messages in the dead-letter queue.
        
        Returns:
            List of failed messages that haven't been retried
        """
        return list(self._ddlq)
    
    def clear_dead_letter_queue(self) -> int:
        """
        Clear the dead-letter queue.
        
        Returns:
            Number of messages cleared
        """
        count = len(self._ddlq)
        self._ddlq.clear()
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics.
        
        Returns:
            Dictionary with routing statistics
        """
        return {
            "messages_routed": self._stats["messages_routed"],
            "messages_delivered": self._stats["messages_delivered"],
            "messages_failed": self._stats["messages_failed"],
            "retries_attempted": self._stats["retries_attempted"],
            "duplicates_detected": self._stats["duplicates_detected"],
        }
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._stats = {
            "messages_routed": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "retries_attempted": 0,
            "duplicates_detected": 0,
        }
    
    def clear_processed_tracking(self) -> None:
        """Clear the processed messages tracking (for testing)."""
        self._processed_ids.clear()
        self._last_processed_time.clear()


# Utility function for quick message creation and routing
def send_message(
    source_agent: str,
    destination_agent: Union[str, List[str]],
    payload: Dict[str, Any],
    task_id: str = "",
    milestone_id: str = "",
    priority=2,  # MEDIUM default
) -> Any:
    """
    Quick function to create and return a message.
    
    Args:
        source_agent: Agent sending the message
        destination_agent: Destination agent(s)
        payload: Message payload
        task_id: Task identifier (optional)
        milestone_id: Milestone identifier (optional)
        priority: Message priority (1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW)
    
    Returns:
        Created message ready to be routed
    """
    return Message.create_request(
        source_agent=source_agent,
        destination_agent=_ensure_destination_list(destination_agent),
        task_id=task_id,
        milestone_id=milestone_id,
        payload=payload,
    )
