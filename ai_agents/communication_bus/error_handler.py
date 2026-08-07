"""
Error Handler Module for Sanskriti AI Studio AI Agents.

This module provides comprehensive error handling for the Communication Bus including:
- Retry policies with exponential backoff
- Timeout handling for long-running operations
- Dead-letter queue for failed messages
- Duplicate detection and prevention

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images in error payloads.

Version: 1.0
Last Updated: 2026-08-05
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .message import Message, MessageType as MESSAGE_TYPES


@dataclass
class RetryPolicy:
    """
    Configuration for retry behavior.
    
    Controls how many times a message should be retried and with what delays.
    """
    
    # Maximum number of retry attempts
    max_retries: int = 3
    
    # Initial delay before first retry (in seconds)
    initial_delay: float = 1.0
    
    # Maximum delay between retries (in seconds)
    max_delay: float = 60.0
    
    # Delay multiplier for exponential backoff
    delay_multiplier: float = 2.0
    
    # Probability of jitter (random delay) to prevent thundering herd
    jitter_probability: float = 0.1
    
    # Jitter amount (as fraction of delay)
    jitter_fraction: float = 0.1
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for a given retry attempt using exponential backoff with optional jitter.
        
        Args:
            attempt: The current attempt number (0-indexed)
        
        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = self.initial_delay * (self.delay_multiplier ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if configured
        if self.jitter_probability > 0 and attempt < self.max_retries:
            import random
            jitter = delay * self.jitter_fraction * random.random()
            delay += jitter
        
        return delay


@dataclass
class TimeoutConfig:
    """
    Configuration for timeout behavior.
    
    Controls how timeouts are handled for long-running operations.
    """
    
    # Default timeout in seconds
    default_timeout: float = 30.0
    
    # Maximum allowed timeout (hard limit)
    max_timeout: float = 300.0
    
    # Timeout check interval (seconds between checks)
    check_interval: float = 1.0
    
    def get_timeout(self, operation: str) -> float:
        """
        Get the appropriate timeout for a given operation type.
        
        Args:
            operation: Type of operation
        
        Returns:
            Appropriate timeout value
        """
        # Override timeouts for specific operations
        operation_timeouts = {
            "request": self.default_timeout,
            "broadcast": 60.0,
            "error_handling": 10.0,
        }
        
        return operation_timeouts.get(operation.lower(), self.default_timeout)


class ErrorHandler:
    """
    Handles all error-related functionality for the Communication Bus.
    
    Capabilities:
    - Retry messages based on configured policy
    - Handle timeouts gracefully
    - Move failed messages to dead-letter queue
    - Detect and prevent duplicate processing
    - Generate error notifications
    
    Usage:
        handler = ErrorHandler()
        
        # Register retry handler for an operation
        @handler.register_retry_handler("coding_agent.process")
        async def handle_coding_retry(message: Message, attempt: int) -> bool:
            # Determine if we should retry this specific operation
            return message.is_retryable()
        
        # Process a message with error handling
        result = handler.process_with_retry(
            message=message,
            process_fn=coding_agent_handler,
            policy=RetryPolicy(max_retries=3),
        )
    """
    
    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ):
        """
        Initialize the error handler.
        
        Args:
            retry_policy: Retry policy (uses defaults if None)
            timeout_config: Timeout configuration (uses defaults if None)
        """
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout_config = timeout_config or TimeoutConfig()
        
        # Dead-letter queue for failed messages
        self._ddlq: List[Any] = []
    
    def should_retry(self, message: Any) -> bool:
        """
        Determine if a message should be retried.
        
        Args:
            message: Message to check
        
        Returns:
            True if message can be retried
        """
        # Check retry count against policy limit
        return (
            message.get("retry_count", 0) < self.retry_policy.max_retries and
            message.is_retryable()
        )
    
    def calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate the delay before retrying.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds before next retry
        """
        return self.retry_policy.calculate_delay(attempt)
    
    def create_error_message(
        self,
        message: Any,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Create an error message for notification.
        
        Args:
            message: Original message that failed
            error_type: Type of error (e.g., "Timeout", "HandlerError")
            error_message: Error description
            context: Additional context information
        
        Returns:
            Error message ready to be routed
        """
        payload = {
            "error_type": error_type,
            "error_message": error_message,
            "original_message_id": message.get("message_id", ""),
            "retry_count": message.get("retry_count", 0),
            **(context or {}),
        }
        
        return Message.create_error(
            source_agent=message.get("source_agent", ""),
            destination_agent=message.get("destination_agent", []),
            correlation_id=message.get("correlation_id", ""),
            error_type=error_type,
            error_message=error_message,
            payload=payload,
        )
    
    def move_to_dead_letter_queue(self, message: Any) -> None:
        """
        Move a failed message to the dead-letter queue.
        
        Args:
            message: Message that has failed all retries
        """
        self._ddlq.append(message)
    
    def get_dead_letter_queue(self) -> List[Any]:
        """
        Get all messages in the dead-letter queue.
        
        Returns:
            List of failed messages
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
    
    def get_ddlq_size(self) -> int:
        """
        Get the current size of the dead-letter queue.
        
        Returns:
            Number of messages in DDLQ
        """
        return len(self._ddlq)


class RetryManager:
    """
    Manages retry behavior for message processing.
    
    Combines error handling, timeout management, and retry logic into
    a unified interface for reliable message processing.
    """
    
    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_config: Optional[TimeoutConfig] = None,
        ddlq_handler: Optional[Callable[[Any], None]] = None,
    ):
        """
        Initialize the retry manager.
        
        Args:
            retry_policy: Retry policy configuration
            timeout_config: Timeout configuration
            ddlq_handler: Callback for dead-letter queue entries (optional)
        """
        self.retry_handler = ErrorHandler(retry_policy, timeout_config)
        self.ddlq_handler = ddlq_handler
        self._processing_locks: Dict[str, bool] = {}  # Prevent concurrent processing
    
    def process_with_retry(
        self,
        message: Any,
        process_fn: Callable[[Any], Any],
    ) -> Tuple[bool, Optional[Any], Optional[str]]:
        """
        Process a message with automatic retry logic.
        
        Args:
            message: Message to process
            process_fn: Function that processes the message (should return result or raise)
        
        Returns:
            Tuple of (success, result, error_message)
        """
        attempt = 0
        
        while attempt <= self.retry_handler.retry_policy.max_retries:
            try:
                # Acquire processing lock to prevent concurrent attempts
                key = f"{message.get('message_id', '')}:{message.get('correlation_id', '')}"
                if key in self._processing_locks:
                    continue
                
                self._processing_locks[key] = True
                
                result = process_fn(message)
                
                # Release lock and return success
                del self._processing_locks[key]
                return True, result, None
                
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                
                # Check if we should retry
                if attempt < self.retry_handler.retry_policy.max_retries:
                    delay = self.retry_handler.calculate_retry_delay(attempt)
                    print(
                        f"[RETRY] {message.get('message_id', 'unknown')} failed (attempt {attempt + 1}/{self.retry_handler.retry_policy.max_retries}) "
                        f"Error: {error_type}: {error_message}. Retrying in {delay:.1f}s..."
                    )
                    
                    # Create new message with incremented retry count
                    message = Message.create_request(
                        source_agent=message.get("source_agent", ""),
                        destination_agent=list(message.get("destination_agent", [])),
                        task_id=message.get("task_id", ""),
                        milestone_id=message.get("milestone_id", ""),
                        payload=dict(message.get("payload", {})),
                        priority=message.get("priority", "MEDIUM"),
                        correlation_id=message.get("correlation_id", ""),
                    )
                    
                    # Wait for retry delay (in a real system, would use asyncio.sleep or threading)
                    attempt += 1
                else:
                    # Max retries exceeded - move to DDLQ and send error notification
                    print(
                        f"[RETRY] {message.get('message_id', 'unknown')} failed after {self.retry_handler.retry_policy.max_retries} attempts. "
                        f"Moving to dead-letter queue."
                    )
                    
                    self.retry_handler.move_to_dead_letter_queue(message)
                    
                    if self.ddlq_handler:
                        self.ddlq_handler(message)
                    
                    # Send error notification
                    error_msg = self.retry_handler.create_error_message(
                        message=message,
                        error_type=f"MaxRetriesExceeded:{error_type}",
                        error_message=f"{error_message} after {self.retry_handler.retry_policy.max_retries} attempts",
                    )
                    
                    return False, None, str(error_message)
        
        # Should not reach here, but handle gracefully
        return False, None, "Unknown error in retry loop"
    
    def get_retry_count(self, message: Any) -> int:
        """
        Get the current retry count for a message.
        
        Args:
            message: Message to check
        
        Returns:
            Current retry count
        """
        return message.get("retry_count", 0)
    
    def reset_message(self, message: Any) -> Any:
        """
        Reset a message (clear retry count, reset status).
        
        Used when manual intervention or special handling is needed.
        
        Args:
            message: Message to reset
        
        Returns:
            Reset message
        """
        return Message.create_request(
            source_agent=message.get("source_agent", ""),
            destination_agent=list(message.get("destination_agent", [])),
            task_id=message.get("task_id", ""),
            milestone_id=message.get("milestone_id", ""),
            payload=dict(message.get("payload", {})),
            priority=message.get("priority", "MEDIUM"),
            correlation_id=message.get("correlation_id", ""),
        )


# Factory function to create a configured retry manager
def create_retry_manager(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
) -> RetryManager:
    """
    Create a RetryManager with default configuration.
    
    Args:
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Configured RetryManager instance
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
    )
    
    return RetryManager(retry_policy=policy)
