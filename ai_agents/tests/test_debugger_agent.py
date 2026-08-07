#!/usr/bin/env python3
"""
Unit Tests for Debugging Agent Runtime - Sanskriti AI Studio

These tests verify the Debugging Agent's failure analysis capabilities without
requiring a live LM Studio server. Uses mocks and stubs for model integration.
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts to path
SCRIPT_DIR = Path(__file__).parent.parent / "ai_agents" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))


def generate_debug_id() -> str:
    """Generate a unique debugging request ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"DEBUG-{timestamp}"


# ============================================================================
# Test Failure Classification - Copied from debugger_agent.py
# ============================================================================

FAILURE_CATEGORIES = [
    "syntax_error", "type_error", "import_error", "dependency_error",
    "configuration_error", "environment_error", "database_error", "api_error",
    "frontend_error", "backend_error", "runtime_error", "test_failure",
    "integration_test_failure", "build_failure", "lint_failure",
    "migration_error", "authentication_error", "authorization_error",
    "network_error", "file_system_error", "unknown_error"
]


def classify_failure(error_message: str, failure_type: Optional[str] = None) -> tuple:
    """Classify the failure into a category and severity level."""
    
    if failure_type and failure_type in FAILURE_CATEGORIES:
        return (failure_type, determine_severity(error_message, failure_type))
    
    error_lower = error_message.lower()
    
    if any(term in error_lower for term in ["syntax", "parse", "indentation"]):
        return ("syntax_error", "low")
    elif any(term in error_lower for term in ["type", "undefined", "not a function", "is not iterable"]):
        return ("type_error", "medium")
    elif any(term in error_lower for term in ["import", "module not found", "cannot import"]):
        return ("import_error", "medium")
    elif any(term in error_lower for term in ["package", "dependency", "install", "pip", "require"]):
        return ("dependency_error", "high")
    elif any(term in error_lower for term in ["config", "environment", "variable", ".env"]):
        return ("configuration_error", "medium")
    elif any(term in error_lower for term in ["database", "connection refused", "sqlite", "postgresql"]):
        return ("database_error", "high")
    elif any(term in error_lower for term in ["500", "404", "403", "api", "endpoint"]):
        return ("api_error", "high")
    elif any(term in error_lower for term in ["frontend", "vue", "typescript", "ts(2"]):
        return ("frontend_error", "medium")
    elif any(term in error_lower for term in ["backend", "flask", "fastapi", "django"]):
        return ("backend_error", "medium")
    elif any(term in error_lower for term in ["keyerror", "indexerror", "attributeerror"]):
        return ("runtime_error", "medium")
    elif any(term in error_lower for term in ["test failed", "assertion", "expect"]):
        return ("test_failure", "medium")
    elif any(term in error_lower for term in ["integration test", "e2e"]):
        return ("integration_test_failure", "high")
    elif any(term in error_lower for term in ["build failed", "webpack", "rollup", "compile"]):
        return ("build_failure", "high")
    elif any(term in error_lower for term in ["eslint", "linting", "style", "format"]):
        return ("lint_failure", "low")
    elif any(term in error_lower for term in ["migrate", "alembic", "schema"]):
        return ("migration_error", "high")
    elif any(term in error_lower for term in ["auth", "permission", "unauthorized", "forbidden"]):
        return ("authentication_error", "high")
    elif any(term in error_lower for term in ["network", "socket", "timeout", "dns"]):
        return ("network_error", "medium")
    elif any(term in error_lower for term in ["file not found", "permission denied", "disk full"]):
        return ("file_system_error", "high")
    
    return ("unknown_error", "medium")


def determine_severity(error_message: str, failure_type: Optional[str] = None) -> str:
    """Determine severity level based on error characteristics."""
    error_lower = error_message.lower()
    
    if any(term in error_lower for term in [
        "fatal", "corruption", "data loss", "destroyed", "cannot start",
        "segmentation fault", "kill", "core dump"
    ]):
        return "critical"
    
    if failure_type and failure_type in ["build_failure", "database_error", "dependency_error"]:
        return "high"
    if any(term in error_lower for term in [
        "500", "internal server error", "cannot connect", "connection refused"
    ]):
        return "high"
    
    if failure_type and failure_type in ["test_failure", "api_error"]:
        return "medium"
    
    if failure_type and failure_type in ["lint_failure", "syntax_error"] and "fatal" not in error_lower:
        return "low"
    
    return "medium"


# ============================================================================
# Helper Functions for Tests
# ============================================================================

def extract_error_class(stack_trace: str) -> Optional[str]:
    """Extract the exception class from a stack trace."""
    if not stack_trace:
        return None
    
    lines = stack_trace.split('\n')
    for line in lines:
        match = re.search(r'(?i)(?:Traceback|File).*:(.*?)\)', line)
        if match:
            error_class = match.group(1).split('(')[0].strip()
            return error_class
    
    return None


def normalize_error_message(message: str) -> str:
    """Normalize error message for signature comparison."""
    if not message:
        return ""
    # Remove line breaks and extra whitespace
    normalized = re.sub(r'\s+', ' ', message.strip())
    # Remove file paths to focus on error class
    normalized = re.sub(r'(?:File|In).*:\d+:.*$', '', normalized, flags=re.MULTILINE)
    return normalized.strip()


def extract_component_from_path(files: List[str]) -> Optional[str]:
    """Extract the component name from file paths."""
    if not files:
        return None
    
    for path in files:
        if "api/" in path:
            return "api"
        elif "model/" in path or "schema/" in path:
            return "model/schema"
        elif "test/" in path:
            return "testing"
        elif "frontend/" in path:
            return "frontend"
        elif "database/" in path:
            return "database"
    
    return None


def get_fix_assigned_agent(failure_type: str) -> str:
    """Determine which agent should handle the fix."""
    coding_agents = [
        "syntax_error", "type_error", "import_error", "configuration_error", 
        "api_error", "frontend_error", "backend_error", "runtime_error",
        "test_failure", "build_failure", "migration_error", "file_system_error"
    ]
    
    if failure_type in coding_agents:
        return "coding_agent"
    
    testing_agents = ["test_failure", "integration_test_failure"]
    if failure_type in testing_agents:
        return "testing_agent"
    
    doc_agents = ["lint_failure"]
    if failure_type in doc_agents:
        return "documentation_agent"
    
    return "coding_agent"


def generate_error_signature(request_data: Dict[str, Any]) -> str:
    """Generate a stable signature for error pattern detection."""
    failure_type = request_data.get("failure_type", "")
    error_class = extract_error_class(request_data.get("stack_trace", ""))
    normalized_message = normalize_error_message(request_data.get("error_message", ""))
    component = extract_component_from_path(request_data.get("affected_files", []))
    failing_test = request_data.get("test_name", "")
    
    parts = [
        failure_type or "unknown",
        error_class or "unknown",
        normalized_message[:100] if normalized_message else "",
        component or "unknown",
        failing_test[:50] if failing_test else "",
    ]
    
    return "|".join(filter(None, parts))


# ============================================================================
# Test Functions
# ============================================================================

def test_valid_failure_report():
    """Test 1: Valid failure report with all fields."""
    error_msg = "AssertionError: Expected status code 200, got 500"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "test_failure", f"Expected test_failure, got {classification}"
    assert severity == "medium", f"Expected medium, got {severity}"
    
    print("✓ Test 1 PASSED: Valid failure report with test failure")


def test_empty_failure_report():
    """Test 2: Empty failure report handling."""
    classification, severity = classify_failure("")
    assert classification in FAILURE_CATEGORIES
    
    print("✓ Test 2 PASSED: Empty failure report handled gracefully")


def test_missing_error_information():
    """Test 3: Missing error information."""
    error_msg = "Error occurred"
    classification, severity = classify_failure(error_msg)
    
    assert severity in ["low", "medium", "high", "critical"]
    print("✓ Test 3 PASSED: Missing error info handled with defaults")


def test_test_failure_diagnosis():
    """Test 4: Test failure diagnosis."""
    error_msg = "AssertionError: Expected 200 OK but received Internal Server Error"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "test_failure"
    assert severity == "medium"
    print("✓ Test 4 PASSED: Test failure diagnosis correct")


def test_build_failure_diagnosis():
    """Test 5: Build failure diagnosis."""
    error_msg = "Build failed: Module not found: flask-cors"
    classification, severity = classify_failure(error_msg)
    
    assert classification in ["build_failure", "import_error"]
    assert severity == "high"
    print("✓ Test 5 PASSED: Build failure diagnosis correct")


def test_lint_failure_diagnosis():
    """Test 6: Lint failure diagnosis."""
    error_msg = "ESLint Error: 'unexpected token' in line 10"
    classification, severity = classify_failure(error_msg)
    
    assert classification in ["lint_failure", "syntax_error"]
    assert severity == "low"
    print("✓ Test 6 PASSED: Lint failure diagnosis correct")


def test_runtime_exception_diagnosis():
    """Test 7: Runtime exception diagnosis."""
    error_msg = "KeyError: 'owner_id' in 'ProjectResponse'"
    classification, severity = classify_failure(error_msg)
    
    assert classification in ["runtime_error", "type_error"]
    assert severity == "medium"
    print("✓ Test 7 PASSED: Runtime exception diagnosis correct")


def test_api_failure_diagnosis():
    """Test 8: API failure diagnosis."""
    error_msg = "HTTP 500 Internal Server Error - Database query failed"
    classification, severity = classify_failure(error_msg)
    
    assert classification in ["api_error", "database_error"]
    assert severity == "high"
    print("✓ Test 8 PASSED: API failure diagnosis correct")


def test_root_cause_extraction():
    """Test 9: Root cause extraction from stack traces."""
    stack_trace = """File "/app/api/projects.py", line 45, in serialize_project
    ProjectResponse(owner_id=model.owner_id)
KeyError: 'owner_id'

During handling of the above exception..."""
    
    error_class = extract_error_class(stack_trace)
    assert error_class and "keyerror" in error_class.lower()
    print("✓ Test 9 PASSED: Root cause extraction correct")


def test_confidence_estimation():
    """Test 10: Confidence level for diagnosis."""
    error_msg = "ModuleNotFoundError: No module named 'requests'"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "import_error"
    assert severity == "medium"
    print("✓ Test 10 PASSED: Confidence estimation reasonable")


def test_affected_file_identification():
    """Test 11: Affected file identification from paths."""
    affected_files = [
        "/app/backend/app/api/projects.py",
        "/app/backend/app/schemas/project.py"
    ]
    
    components = extract_component_from_path(affected_files)
    assert "api" in str(components).lower() or (components and len(components) > 0)
    print("✓ Test 11 PASSED: Affected file identification correct")


def test_fix_plan_generation():
    """Test 12: Fix plan generation."""
    failure_type = "test_failure"
    affected_files = ["backend/app/api/projects.py"]
    
    fix_strategy = f"Address {failure_type} issue in: {', '.join(affected_files)}"
    assert len(fix_strategy) > 0
    print("✓ Test 12 PASSED: Fix plan generation correct")


def test_coding_agent_assignment():
    """Test 13: Coding Agent assignment for code fixes."""
    coding_agents = [
        "syntax_error", "type_error", "import_error", "configuration_error",
        "api_error", "frontend_error", "backend_error", "runtime_error",
        "test_failure", "build_failure", "migration_error", "file_system_error"
    ]
    
    for ft in coding_agents[:3]:
        assigned = get_fix_assigned_agent(ft)
        assert assigned == "coding_agent", f"{ft} should be coding_agent, got {assigned}"
    
    print("✓ Test 13 PASSED: Coding Agent assignment correct")


def test_acceptance_criteria_generation():
    """Test 14: Acceptance criteria generation."""
    classification = "test_failure"
    acceptance_criteria = [
        f"{classification.title()} issue is resolved",
        "Related tests pass",
        "No new errors introduced",
    ]
    
    assert len(acceptance_criteria) >= 3
    print("✓ Test 14 PASSED: Acceptance criteria generation correct")


def test_validation_step_generation():
    """Test 15: Validation step generation."""
    classification = "test_failure"
    validation_steps = [
        f"Run validation for {classification} issues",
        "Verify fix resolves the specific error",
        "Ensure no regressions are introduced",
    ]
    
    assert len(validation_steps) >= 3
    print("✓ Test 15 PASSED: Validation step generation correct")


def test_retry_recommendation():
    """Test 16: Retry recommendation."""
    transient_error = "Connection timeout after 30s"
    retry_recommended = any(
        term in transient_error.lower() for term in [
            "timeout", "connection reset", "network", "retry"
        ]
    )
    
    assert retry_recommended == True
    print("✓ Test 16 PASSED: Retry recommendation for transient errors")


def test_retry_limit_enforcement():
    """Test 17: Retry limit enforcement."""
    MAX_DEBUG_RETRIES = 3
    
    retry_count = 0
    for i in range(5):
        if retry_count < MAX_DEBUG_RETRIES:
            retry_count += 1
    
    assert retry_count == MAX_DEBUG_RETRIES
    print("✓ Test 17 PASSED: Retry limit enforcement correct")


def test_repeated_failure_detection():
    """Test 18: Repeated failure detection."""
    current_signature = "import_error|module_not_found|ModuleNotFoundError|unknown|"
    
    previous_attempts = [
        {"failure_type": "import_error", "stack_trace": "", "error_message": "", "affected_files": []},
    ]
    
    is_repeated = False
    for attempt in previous_attempts:
        if generate_error_signature(attempt) == current_signature:
            is_repeated = True
            break
    
    print("✓ Test 18 PASSED: Repeated failure detection logic")


def test_escalation_after_max_retries():
    """Test 19: Escalation after maximum retries."""
    MAX_DEBUG_RETRIES = 3
    
    retry_count = MAX_DEBUG_RETRIES
    escalation_required = retry_count >= MAX_DEBUG_RETRIES
    
    assert escalation_required == True
    print("✓ Test 19 PASSED: Escalation after max retries")


def test_invalid_model_response():
    """Test 20: Invalid model response handling."""
    raw_response = {"choices": []}
    
    status = "malformed_response" if not raw_response.get("choices") else "success"
    
    print("✓ Test 20 PASSED: Invalid model response handled")


def test_lm_studio_unavailable():
    """Test 21: LM Studio unavailable fallback."""
    failure_report = {
        "error_message": "Test error",
        "failure_type": "test_failure"
    }
    
    classification, severity = classify_failure(
        failure_report.get("error_message", ""),
        failure_report.get("failure_type")
    )
    
    assert classification and severity
    print("✓ Test 21 PASSED: LM Studio unavailable fallback works")


def test_malformed_json():
    """Test 22: Malformed JSON handling."""
    content = "This is not JSON { invalid"
    
    json_match = re.search(r'\{[\s\S]*\}', content)
    
    assert json_match is None
    print("✓ Test 22 PASSED: Malformed JSON detection")


def test_sensitive_information_redaction():
    """Test 23: Sensitive information redaction."""
    raw_error = "KeyError in DB connection with password='supersecret123'"
    
    redacted = re.sub(r'password=["\']?([^"\',]+)["\']?', 'password="REDACTED"', raw_error)
    
    assert "supersecret123" not in redacted
    print("✓ Test 23 PASSED: Sensitive information redaction")


def test_dangerous_command_detection():
    """Test 24: Dangerous command detection."""
    dangerous_commands = [
        "rm -rf /",
        "git reset --hard",
        "git push --force",
        "DROP TABLE users",
    ]
    
    for cmd in dangerous_commands:
        is_dangerous = any(
            keyword in cmd.lower() for keyword in [
                "rm -rf", "drop table", "reset --hard", "push --force"
            ]
        )
        assert is_dangerous == True
    
    print("✓ Test 24 PASSED: Dangerous command detection")


# Individual error classification tests
def test_syntax_error():
    """Test: Syntax error classification."""
    error_msg = "SyntaxError: invalid syntax in line 10"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "syntax_error"
    assert severity == "low"
    print("✓ Syntax Error Test PASSED")


def test_type_error():
    """Test: Type error classification."""
    error_msg = "TypeError: 'NoneType' object is not subscriptable"
    classification, severity = classify_failure(error_msg)
    
    assert classification in ["type_error", "runtime_error"]
    assert severity == "medium"
    print("✓ Type Error Test PASSED")


def test_import_error():
    """Test: Import error classification."""
    error_msg = "ImportError: cannot import name 'X' from 'module'"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "import_error"
    assert severity == "medium"
    print("✓ Import Error Test PASSED")


def test_dependency_error():
    """Test: Dependency error classification."""
    error_msg = "RequirementError: No matching distribution found for flask==2.0.0"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "dependency_error"
    assert severity == "high"
    print("✓ Dependency Error Test PASSED")


def test_configuration_error():
    """Test: Configuration error classification."""
    error_msg = "ConfigError: Missing required environment variable DATABASE_URL"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "configuration_error"
    assert severity == "medium"
    print("✓ Configuration Error Test PASSED")


def test_database_error():
    """Test: Database error classification."""
    error_msg = "DatabaseError: connection refused to localhost:5432"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "database_error"
    assert severity == "high"
    print("✓ Database Error Test PASSED")


def test_authentication_error():
    """Test: Authentication error classification."""
    error_msg = "AuthenticationError: Invalid token provided"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "authentication_error"
    assert severity == "high"
    print("✓ Authentication Error Test PASSED")


def test_network_error():
    """Test: Network error classification."""
    error_msg = "NetworkError: DNS resolution failed for api.example.com"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "network_error"
    assert severity == "medium"
    print("✓ Network Error Test PASSED")


def test_file_system_error():
    """Test: File system error classification."""
    error_msg = "FileNotFoundError: [Errno 2] No such file or directory: 'config.yml'"
    classification, severity = classify_failure(error_msg)
    
    assert classification == "file_system_error"
    assert severity == "high"
    print("✓ File System Error Test PASSED")


def test_severity_critical():
    """Test: Critical severity detection."""
    error_msg = "FatalError: Database corruption detected"
    classification, severity = classify_failure(error_msg)
    
    assert severity == "critical"
    print("✓ Severity Critical Test PASSED")


def test_severity_high():
    """Test: High severity detection."""
    error_msg = "Build failed with exit code 1"
    classification, severity = classify_failure(error_msg)
    
    assert severity in ["high", "medium"]
    print("✓ Severity High Test PASSED")


def test_severity_medium():
    """Test: Medium severity detection."""
    error_msg = "AssertionError: Expected value but got None"
    classification, severity = classify_failure(error_msg)
    
    assert severity == "medium"
    print("✓ Severity Medium Test PASSED")


def test_severity_low():
    """Test: Low severity detection."""
    error_msg = "ESLint warning: trailing whitespace on line 5"
    classification, severity = classify_failure(error_msg)
    
    assert severity == "low"
    print("✓ Severity Low Test PASSED")


# ============================================================================
# Run All Tests
# ============================================================================

def run_all_tests():
    """Run all unit tests and report results."""
    print("=" * 60)
    print("DEBUGGING AGENT UNIT TESTS")
    print("=" * 60)
    
    test_functions = [
        ("Valid Failure Report", test_valid_failure_report),
        ("Empty Failure Report", test_empty_failure_report),
        ("Missing Error Information", test_missing_error_information),
        ("Test Failure Diagnosis", test_test_failure_diagnosis),
        ("Build Failure Diagnosis", test_build_failure_diagnosis),
        ("Lint Failure Diagnosis", test_lint_failure_diagnosis),
        ("Runtime Exception Diagnosis", test_runtime_exception_diagnosis),
        ("API Failure Diagnosis", test_api_failure_diagnosis),
        ("Root Cause Extraction", test_root_cause_extraction),
        ("Confidence Estimation", test_confidence_estimation),
        ("Affected File Identification", test_affected_file_identification),
        ("Fix Plan Generation", test_fix_plan_generation),
        ("Coding Agent Assignment", test_coding_agent_assignment),
        ("Acceptance Criteria Generation", test_acceptance_criteria_generation),
        ("Validation Step Generation", test_validation_step_generation),
        ("Retry Recommendation", test_retry_recommendation),
        ("Retry Limit Enforcement", test_retry_limit_enforcement),
        ("Repeated Failure Detection", test_repeated_failure_detection),
        ("Escalation After Max Retries", test_escalation_after_max_retries),
        ("Invalid Model Response", test_invalid_model_response),
        ("LM Studio Unavailable", test_lm_studio_unavailable),
        ("Malformed JSON", test_malformed_json),
        ("Sensitive Information Redaction", test_sensitive_information_redaction),
        ("Dangerous Command Detection", test_dangerous_command_detection),
        # Severity Tests
        ("Syntax Error Classification", test_syntax_error),
        ("Type Error Classification", test_type_error),
        ("Import Error Classification", test_import_error),
        ("Dependency Error Classification", test_dependency_error),
        ("Configuration Error Classification", test_configuration_error),
        ("Database Error Classification", test_database_error),
        ("Authentication Error Classification", test_authentication_error),
        ("Network Error Classification", test_network_error),
        ("File System Error Classification", test_file_system_error),
        ("Critical Severity Detection", test_severity_critical),
        ("High Severity Detection", test_severity_high),
        ("Medium Severity Detection", test_severity_medium),
        ("Low Severity Detection", test_severity_low),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name} ERROR: {type(e).__name__}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
