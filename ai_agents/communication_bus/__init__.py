"""
Communication Bus for Sanskriti AI Studio AI Agents.

This module provides a centralized communication layer that coordinates all agent interactions.
It routes requests between agents, standardizes message formats, tracks execution history,
handles retries and timeouts, and prevents duplicate requests.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    COMMUNICATION BUS                         │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │                    Message Router                        │ │
    │  │  - Routes messages between agents                        │ │
    │  │  - Supports one-to-one, broadcast, request/response     │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │              Message Schema Validator                     │ │
    │  │  - Validates message format and required fields          │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │           Execution History & Tracker                    │ │
    │  │  - Logs all messages sent/received                        │ │
    │  │  - Tracks correlation IDs                                 │ │
    │  │  - Maintains retry counters                               │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │          Duplicate Detection & Prevention                │ │
    │  │  - Checks message ID for duplicates                       │ │
    │  │  - Correlates related operations                          │ │
    │  └─────────────────────────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────────────────────────┐ │
    │  │           Error Handling & Retry Logic                    │ │
    │  │  - Implements retry policies                               │ │
    │  │  - Handles timeouts                                        │ │
    │  │  - Manages dead-letter queue                              │ │
    │  └─────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images to the Communication Bus.

Version: 1.0
Last Updated: 2026-08-05
"""

from .message import (
    Message,
    MessageType,
    MessageStatus,
    MessagePriority,
)
from .router import (
    Router,
    RoutingRule,
    RouteType,
)
from .history import (
    ExecutionHistory,
    HistoryEntry,
)
from .error_handler import (
    ErrorHandler,
    RetryPolicy,
    TimeoutConfig,
    RetryManager,
)

__all__ = [
    # Message types and constants
    "Message",
    "MessageType",
    "MessageStatus",
    "MessagePriority",
    # Router and routing rules
    "Router",
    "RoutingRule",
    "RouteType",
    # History tracking
    "ExecutionHistory",
    "HistoryEntry",
    # Error handling
    "ErrorHandler",
    "RetryPolicy",
    "TimeoutConfig",
    "RetryManager",
]
