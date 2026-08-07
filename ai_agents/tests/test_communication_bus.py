#!/usr/bin/env python3
"""
Test Suite for Communication Bus - Sanskriti AI Studio

This module validates all Communication Bus components:
- Message schema validation
- Router routing rules
- Execution history tracking
- Error handling and retry logic

CRITICAL: Qwen 3.5 is TEXT-ONLY - Never send images in tests.

Version: 1.0
Last Updated: 2026-08-05
"""

import sys
import os

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from ai_agents.communication_bus import (
    Message, MessageType, MessageStatus, MessagePriority,
    Router, RoutingRule, RouteType,
    ExecutionHistory, HistoryEntry,
    ErrorHandler, RetryPolicy, TimeoutConfig, RetryManager,
)


def print_separator(char="=", length=70):
    """Print a separator line."""
    print(char * length)


def test_message_creation():
    """Test message creation functions."""
    print_separator()
    print("[TEST] Message Creation")
    print_separator()
    
    # Test REQUEST message creation
    request = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="MILESTONE-6.6",
        payload={"action": "generate_code"},
        priority=MessagePriority.HIGH,
    )
    
    assert request.message_type.value == "REQUEST"
    assert request.source_agent == "planner_agent"
    assert request.destination_agent == ["coding_agent"]
    print(f"✓ REQUEST message created: {request}")
    
    # Test RESPONSE message creation  
    response = Message.create_response(
        source_agent="coding_agent",
        destination_agent="planner_agent",
        correlation_id=request.correlation_id,
        payload={"status": "success", "result": "code generated"},
    )
    
    assert response.message_type.value == "RESPONSE"
    print(f"✓ RESPONSE message created: {response}")
    
    # Test EVENT message creation
    event = Message.create_event(
        source_agent="coding_agent",
        destination_agent=["planner_agent", "orchestrator_agent"],
        payload={"task_complete": True},
    )
    
    assert event.message_type.value == "EVENT"
    print(f"✓ EVENT message created: {event}")
    
    # Test ERROR message creation
    error = Message.create_error(
        source_agent="coding_agent",
        destination_agent="planner_agent",
        correlation_id=request.correlation_id,
        error_type="ValidationError",
        error_message="Invalid file path provided",
    )
    
    assert error.message_type.value == "ERROR"
    print(f"✓ ERROR message created: {error}")
    
    # Test retry increment
    retried = request.increment_retry()
    assert retried.retry_count == 1
    print(f"✓ Retry count incremented to {retried.retry_count}")
    
    print("✓ Message creation tests PASSED")
    return True


def test_message_serialization():
    """Test message serialization/deserialization."""
    print_separator()
    print("[TEST] Message Serialization")
    print_separator()
    
    original = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"test": "data"},
    )
    
    # Convert to dict
    data = original.to_dict()
    
    # Reconstruct from dict
    restored = Message.from_dict(data)
    
    assert restored.message_id == original.message_id
    assert restored.correlation_id == original.correlation_id
    assert restored.source_agent == original.source_agent
    assert restored.destination_agent == original.destination_agent
    assert restored.message_type.value == original.message_type.value
    assert restored.task_id == original.task_id
    assert restored.milestone_id == original.milestone_id
    assert restored.payload == original.payload
    print(f"✓ Message serialization test PASSED")
    
    return True


def test_router_basic_routing():
    """Test basic router functionality."""
    print_separator()
    print("[TEST] Router Basic Routing")
    print_separator()
    
    # Create router
    router = Router()
    
    # Register handler for coding_agent
    def handle_coding_request(message):
        if message.message_type.value == "REQUEST":
            return Message.create_response(
                source_agent="coding_agent",
                destination_agent=message.source_agent,
                correlation_id=message.correlation_id,
                payload={"status": "completed"},
            )
        return None
    
    router.register_handler("coding_agent", handle_coding_request)
    
    # Create and route a message
    request = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"action": "test"},
    )
    
    response = router.route(request)
    
    assert response is not None
    assert response.message_type.value == "RESPONSE"
    print(f"✓ One-to-one routing test PASSED")
    
    # Test broadcast routing
    broadcast_request = Message.create_request(
        source_agent="orchestrator_agent",
        destination_agent=["coding_agent", "documentation_agent"],
        task_id="TASK-002",
        milestone_id="",
        payload={"action": "broadcast_test"},
    )
    
    response = router.route(broadcast_request)
    print(f"✓ Broadcast routing test PASSED")
    
    return True


def test_router_duplicate_detection():
    """Test router duplicate detection."""
    print_separator()
    print("[TEST] Router Duplicate Detection")
    print_separator()
    
    router = Router()
    router.config.enable_duplicate_detection = True
    
    # Create a message
    request = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"action": "test"},
    )
    
    # Route first time - should succeed
    response1 = router.route(request)
    assert response1 is not None
    
    # Route same message again - should be rejected as duplicate
    response2 = router.route(request)
    assert response2 is None  # Should return None for duplicates
    
    print(f"✓ Duplicate detection test PASSED")
    
    # Test with disabled duplicate detection
    router.config.enable_duplicate_detection = False
    response3 = router.route(request)
    assert response3 is not None
    
    print(f"✓ Disabled duplicate detection test PASSED")
    
    return True


def test_router_statistics():
    """Test router statistics tracking."""
    print_separator()
    print("[TEST] Router Statistics")
    print_separator()
    
    router = Router()
    
    # Route several messages
    for i in range(5):
        msg = Message.create_request(
            source_agent="planner_agent",
            destination_agent="coding_agent",
            task_id=f"TASK-{i}",
            milestone_id="",
            payload={"action": "test"},
        )
        router.route(msg)
    
    stats = router.get_stats()
    
    assert stats["messages_routed"] == 5
    print(f"✓ Router statistics test PASSED")
    print(f"   - Messages routed: {stats['messages_routed']}")
    
    return True


def test_execution_history():
    """Test execution history tracking."""
    print_separator()
    print("[TEST] Execution History")
    print_separator()
    
    # Create history
    history = ExecutionHistory(max_entries=10)
    
    # Add entries
    entry1 = HistoryEntry(
        message_id="MSG-001",
        source_agent="planner_agent",
        destination_agents=["coding_agent"],
        message_type="REQUEST",
        success=True,
        correlation_id="CORR-001",
    )
    
    entry2 = HistoryEntry(
        message_id="MSG-002",
        source_agent="coding_agent",
        destination_agents=["planner_agent"],
        message_type="RESPONSE",
        success=True,
        correlation_id="CORR-001",
    )
    
    entry3 = HistoryEntry(
        message_id="MSG-003",
        source_agent="coding_agent",
        destination_agents=["planner_agent"],
        message_type="ERROR",
        success=False,
        error_type="ValidationError",
        correlation_id="CORR-002",
    )
    
    history.add(entry1)
    history.add(entry2)
    history.add(entry3)
    
    # Test get by source agent
    planner_entries = history.get_by_source_agent("planner_agent")
    assert len(planner_entries) == 2
    
    # Test get by destination agent
    coding_entries = history.get_by_destination_agent("coding_agent")
    assert len(coding_entries) == 2
    
    # Test get by type
    error_entries = history.get_by_type("ERROR")
    assert len(error_entries) == 1
    
    # Test get by correlation ID
    corr_group = history.get_correlation_group("CORR-001")
    assert corr_group["correlation_id"] == "CORR-001"
    assert corr_group["message_count"] == 2
    
    # Test statistics
    stats = history.get_statistics()
    assert stats["total_messages"] == 3
    assert stats["successful"] == 2
    assert stats["failed"] == 1
    
    print(f"✓ Execution history test PASSED")
    print(f"   - Total messages: {stats['total_messages']}")
    print(f"   - Successful: {stats['successful']}")
    print(f"   - Failed: {stats['failed']}")
    
    return True


def test_error_handler_retry_policy():
    """Test error handler retry policy."""
    print_separator()
    print("[TEST] Error Handler Retry Policy")
    print_separator()
    
    policy = RetryPolicy(
        max_retries=3,
        initial_delay=1.0,
        delay_multiplier=2.0,
    )
    
    # Test delay calculation
    assert policy.calculate_delay(0) == 1.0
    assert policy.calculate_delay(1) == 2.0
    assert policy.calculate_delay(2) == 4.0
    
    print(f"✓ Retry delay calculation test PASSED")
    
    return True


def test_error_handler_dead_letter_queue():
    """Test error handler dead-letter queue."""
    print_separator()
    print("[TEST] Error Handler Dead Letter Queue")
    print_separator()
    
    handler = ErrorHandler()
    
    # Create a message and simulate failure
    request = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"action": "test"},
    )
    
    # Move to DDLQ
    handler.move_to_dead_letter_queue(request)
    
    # Get DDLQ contents
    ddlq = handler.get_dead_letter_queue()
    assert len(ddlq) == 1
    
    # Clear DDLQ
    count = handler.clear_dead_letter_queue()
    assert count == 1
    
    print(f"✓ Dead letter queue test PASSED")
    
    return True


def test_error_handler_retry_manager():
    """Test error handler retry manager."""
    print_separator()
    print("[TEST] Error Handler Retry Manager")
    print_separator()
    
    manager = RetryManager(
        retry_policy=RetryPolicy(max_retries=3),
    )
    
    # Test processing with success
    def successful_process(message):
        return {"status": "success", "data": "processed"}
    
    # Create request object for testing
    request_obj = Message.create_request(
        source_agent="planner_agent",
        destination_agent="coding_agent",
        task_id="TASK-001",
        milestone_id="",
        payload={"action": "test"},
    )
    
    success, result, error = manager.process_with_retry(
        message=request_obj,
        process_fn=successful_process,
    )
    
    print(f"✓ Retry manager processing test PASSED")
    
    return True


def main():
    """Run all tests."""
    print_separator()
    print("COMMUNICATION BUS - TEST SUITE")
    print_separator()
    print("Sanskriti AI Studio")
    from datetime import timezone

    results = []
    
    try:
        results.append(("Message Creation", test_message_creation()))
    except Exception as e:
        print(f"✗ Message Creation test FAILED: {e}")
        results.append(("Message Creation", False))
    
    try:
        results.append(("Message Serialization", test_message_serialization()))
    except Exception as e:
        print(f"✗ Message Serialization test FAILED: {e}")
        results.append(("Message Serialization", False))
    
    try:
        results.append(("Router Basic Routing", test_router_basic_routing()))
    except Exception as e:
        print(f"✗ Router Basic Routing test FAILED: {e}")
        results.append(("Router Basic Routing", False))
    
    try:
        results.append(("Router Duplicate Detection", test_router_duplicate_detection()))
    except Exception as e:
        print(f"✗ Router Duplicate Detection test FAILED: {e}")
        results.append(("Router Duplicate Detection", False))
    
    try:
        results.append(("Router Statistics", test_router_statistics()))
    except Exception as e:
        print(f"✗ Router Statistics test FAILED: {e}")
        results.append(("Router Statistics", False))
    
    try:
        results.append(("Execution History", test_execution_history()))
    except Exception as e:
        print(f"✗ Execution History test FAILED: {e}")
        results.append(("Execution History", False))
    
    try:
        results.append(("Error Handler Retry Policy", test_error_handler_retry_policy()))
    except Exception as e:
        print(f"✗ Error Handler Retry Policy test FAILED: {e}")
        results.append(("Error Handler Retry Policy", False))
    
    try:
        results.append(("Error Handler Dead Letter Queue", test_error_handler_dead_letter_queue()))
    except Exception as e:
        print(f"✗ Error Handler Dead Letter Queue test FAILED: {e}")
        results.append(("Error Handler Dead Letter Queue", False))
    
    # Summary
    print_separator()
    print("TEST SUMMARY")
    print_separator()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  [{status}] {name}")
    
    print_separator()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
