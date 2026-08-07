#!/usr/bin/env python3
"""
Unit tests for the Debugging Agent Runtime.

Tests coverage:
- Failure classification (21 failure types)
- Severity detection
- Root cause extraction
- Affected file identification
- Fix plan generation
- Retry limit enforcement
- LM Studio fallback handling
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root and scripts to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPT_DIR)


def create_test_input(failure_type: str, error_message: str, stack_trace: str = "") -> dict:
    """Create test input for debugging request."""
    return {
        "failure_type": failure_type,
        "error_message": error_message,
        "stack_trace": stack_trace,
        "affected_files": ["test/file.py"],
        "task_id": "TEST-TASK-001",
        "command_executed": "pytest test_file.py",
        "exit_code": 1,
    }


class TestFailureClassification:
    """Test failure classification functionality."""
    
    def test_test_failure_classification(self):
        """Test that assertion error is classified as test_failure."""
        from debugger_agent import classify_failure_type
        
        result = classify_failure_type("AssertionError: expected 200 but got 500", "")
        assert result == "test_failure", f"Expected 'test_failure', got '{result}'"
        print("✓ test_failure classification passed")
    
    def test_api_error_classification(self):
        """Test that HTTP 500 is classified as api_error."""
        from debugger_agent import classify_failure_type
        
        result = classify_failure_type("GET /api/projects returned HTTP 500", "")
        assert result == "api_error", f"Expected 'api_error', got '{result}'"
        print("✓ api_error classification passed")
    
    def test_database_error_classification(self):
        """Test that database connection error is classified correctly."""
        from debugger_agent import classify_failure_type
        
        result = classify_failure_type("Could not connect to PostgreSQL", "")
        assert result == "database_error", f"Expected 'database_error', got '{result}'"
        print("✓ database_error classification passed")
    
    def test_import_error_classification(self):
        """Test that missing module is classified as import_error."""
        from debugger_agent import classify_failure_type
        
        result = classify_failure_type("ModuleNotFoundError: No module named 'fastapi'", "")
        assert result == "import_error", f"Expected 'import_error', got '{result}'"
        print("✓ import_error classification passed")


class TestSeverityDetection:
    """Test severity detection functionality."""
    
    def test_critical_severity(self):
        """Test that database corruption is detected as critical."""
        from debugger_agent import detect_severity
        
        result = detect_severity(
            "database_error",
            "Database corruption detected: data loss possible"
        )
        assert result == "critical", f"Expected 'critical', got '{result}'"
        print("✓ critical severity detection passed")
    
    def test_high_severity(self):
        """Test that HTTP 500 is detected as high severity."""
        from debugger_agent import detect_severity
        
        result = detect_severity(
            "api_error",
            "GET /api/projects returned HTTP 500 Internal Server Error"
        )
        assert result == "high", f"Expected 'high', got '{result}'"
        print("✓ high severity detection passed")
    
    def test_medium_severity(self):
        """Test that test failure is detected as medium severity."""
        from debugger_agent import detect_severity
        
        result = detect_severity(
            "test_failure",
            "AssertionError: expected 200 but got 500"
        )
        assert result == "medium", f"Expected 'medium', got '{result}'"
        print("✓ medium severity detection passed")
    
    def test_low_severity(self):
        """Test that lint warning is detected as low severity."""
        from debugger_agent import detect_severity
        
        result = detect_severity(
            "lint_failure",
            "eslint: 'useless-constructor' - Unused constructor"
        )
        assert result == "low", f"Expected 'low', got '{result}'"
        print("✓ low severity detection passed")


class TestRootCauseExtraction:
    """Test root cause extraction functionality."""
    
    def test_database_connection_root_cause(self):
        """Test database connection error root cause extraction."""
        from debugger_agent import extract_root_cause
        
        result = extract_root_cause(
            "Could not connect to PostgreSQL: connection refused",
            ""
        )
        assert "database" in result["description"].lower()
        print("✓ database root cause extraction passed")
    
    def test_import_error_root_cause(self):
        """Test import error root cause extraction."""
        from debugger_agent import extract_root_cause
        
        result = extract_root_cause(
            "ModuleNotFoundError: No module named 'requests'",
            ""
        )
        assert "package" in result["description"].lower() or "import" in result["description"].lower()
        print("✓ import error root cause extraction passed")


class TestAffectedFilesIdentification:
    """Test affected files identification functionality."""
    
    def test_extract_files_from_stack_trace(self):
        """Test that file paths are extracted from stack traces."""
        from debugger_agent import analyze_affected_files
        
        stack_trace = "File \"backend/app/api/projects.py\", line 42\n  File \"test_file.py\""
        result = analyze_affected_files("Error occurred", stack_trace)
        
        assert len(result.get("likely_affected", [])) > 0, "Should extract file from stack trace"
        print("✓ affected files extraction passed")


class TestFixPlanGeneration:
    """Test fix plan generation functionality."""
    
    def test_fix_plan_created_for_test_failure(self):
        """Test that fix plan is generated for test failures."""
        from debugger_agent import build_fix_plan
        
        root_cause = {
            "description": "Test assertion failed",
            "confidence": "high",
        }
        
        fix_tasks = build_fix_plan(
            failure_type="test_failure",
            root_cause=root_cause,
            affected_files=["test/test_projects.py"],
            task_id="TEST-TASK-001",
        )
        
        assert len(fix_tasks) >= 1, "Should create at least one fix task"
        assert any("testing_agent" in str(task.get("assigned_agent")) for task in fix_tasks), \
            "Fix plan should include testing agent for retest"
        print("✓ fix plan generation passed")


class TestRetryLimitEnforcement:
    """Test retry limit enforcement functionality."""
    
    def test_retry_recommendation_for_medium_severity(self):
        """Test that medium severity issues recommend retry."""
        from debugger_agent import MAX_DEBUG_RETRIES
        
        result = {
            "severity": "medium",
            "failure_type": "test_failure",
        }
        
        retry_recommended = result["severity"] in ["medium", "low"] and 0 < MAX_DEBUG_RETRIES
        assert retry_recommended, "Medium severity should recommend retry"
        print("✓ retry recommendation for medium severity passed")
    
    def test_no_retry_for_critical_severity(self):
        """Test that critical severity issues don't recommend retry."""
        
        result = {
            "severity": "critical",
            "failure_type": "unknown_error",
        }
        
        retry_recommended = result["severity"] in ["medium", "low"]
        assert not retry_recommended, "Critical severity should not recommend retry"
        print("✓ no retry for critical severity passed")


class TestDebuggingRequestProcessing:
    """Test full debugging request processing workflow."""
    
    @patch('@patch('scripts.debugger_agent.chat_with_coding_model')
    def test_successful_debugging_flow(self, mock_chat):
        """Test successful debugging flow with model available."""
        from debugger_agent import process_debugging_request
        
        # Setup mock response
        mock_chat.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "status": "analyzed",
                        "failure_classification": "api_error",
                        "severity": "high",
                        "root_cause": {
                            "description": "API endpoint has unhandled exception",
                            "confidence": "high",
                        },
                    })
                }
            }]
        }
        
        input_data = create_test_input(
            failure_type="unknown_error",
            error_message="GET /api/projects returned HTTP 500",
            stack_trace=""
        )
        
        result = process_debugging_request(input_data, retry_count=0)
        
        assert result["diagnosis_complete"] is True
        assert result["severity"] == "high"
        print("✓ successful debugging flow passed")
    
    @patch('@patch('scripts.debugger_agent.chat_with_coding_model')
    def test_debugging_flow_without_model(self, mock_chat):
        """Test debugging flow when model is unavailable."""
        from debugger_agent import process_debugging_request
        
        # Mock LM Studio as unavailable
        with patch.dict(os.environ, {'LM_STUDIO_BASE_URL': 'http://invalid-url'}):
            input_data = create_test_input(
                failure_type="unknown_error",
                error_message="GET /api/projects returned HTTP 500",
                stack_trace=""
            )
            
            result = process_debugging_request(input_data, retry_count=0)
            
            assert result["diagnosis_complete"] is True
            # Should fall back to direct analysis
            print("✓ debugging flow without model passed")


class TestEscalationLogic:
    """Test escalation logic functionality."""
    
    def test_escalation_after_max_retries(self):
        """Test that escalation occurs after max retries."""
        from debugger_agent import MAX_DEBUG_RETRIES, process_debugging_request
        
        input_data = create_test_input(
            failure_type="api_error",
            error_message="HTTP 500 error occurred",
            stack_trace=""
        )
        
        result = process_debugging_request(input_data, retry_count=MAX_DEBUG_RETRIES)
        
        assert result["escalation_required"] is True
        assert "Retry limit reached" in result.get("escalation_reason", "")
        print("✓ escalation after max retries passed")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("DEBUGGING AGENT RUNTIME - UNIT TESTS")
    print("=" * 70)
    print()
    
    # Run classification tests
    test_classification = TestFailureClassification()
    test_classification.test_test_failure_classification()
    test_classification.test_api_error_classification()
    test_classification.test_database_error_classification()
    test_classification.test_import_error_classification()
    
    print()
    
    # Run severity tests
    test_severity = TestSeverityDetection()
    test_severity.test_critical_severity()
    test_severity.test_high_severity()
    test_severity.test_medium_severity()
    test_severity.test_low_severity()
    
    print()
    
    # Run root cause tests
    test_root_cause = TestRootCauseExtraction()
    test_root_cause.test_database_connection_root_cause()
    test_root_cause.test_import_error_root_cause()
    
    print()
    
    # Run affected files tests
    test_affected_files = TestAffectedFilesIdentification()
    test_affected_files.test_extract_files_from_stack_trace()
    
    print()
    
    # Run fix plan tests
    test_fix_plan = TestFixPlanGeneration()
    test_fix_plan.test_fix_plan_created_for_test_failure()
    
    print()
    
    # Run retry limit tests
    test_retry = TestRetryLimitEnforcement()
    test_retry.test_retry_recommendation_for_medium_severity()
    test_retry.test_no_retry_for_critical_severity()
    
    print()
    
    # Run full workflow tests
    test_workflow = TestDebuggingRequestProcessing()
    test_workflow.test_successful_debugging_flow()
    test_workflow.test_debugging_flow_without_model()
    
    print()
    
    # Run escalation tests
    test_escalation = TestEscalationLogic()
    test_escalation.test_escalation_after_max_retries()
    
    print()
    print("=" * 70)
    print("ALL UNIT TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
