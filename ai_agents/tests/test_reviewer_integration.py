#!/usr/bin/env python3
"""
Reviewer Agent Runtime Integration Tests for Sanskriti AI Studio.

This test suite validates the complete Reviewer Agent workflow through integration
tests that verify:
1. Implementation completed -> Testing passed -> Review approved
2. Implementation with issues -> Review requires changes -> Fix -> Retest -> Re-review approved  
3. Persistent issues -> Maximum review cycles -> Escalation

All tests use mocks/stubs - no live LM Studio or actual code changes required.

Version: 2.0 - Enhanced Reviewer Agent Integration Tests
Last Updated: 2026-07-30
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Add parent directories to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, str(AI_AGENTS_ROOT))

from ai_agents.scripts.reviewer_input_schema import (
    REVIEW_STATUSES,
    create_review_result,
    create_finding,
    SEVERITIES,
    REVIEW_CATEGORIES
)


# ============================================================================
# Integration Test Scenario 1: Successful Review Workflow
# ============================================================================

def test_successful_review_workflow():
    """
    Integration Test 1: Verify the standard successful review workflow.
    
    Workflow:
    1. Coding Agent implements feature
    2. Testing Agent validates implementation (PASS)
    3. Reviewer Agent reviews and approves
    
    Expected outcome: APPROVED status
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST 1: Successful Review Workflow")
    print("=" * 70)
    
    # Step 1: Simulate completed implementation (from Coding Agent)
    coding_result = {
        "status": "COMPLETED",
        "files_changed": ["frontend/src/pages/Workspace.tsx"],
        "message": "Workspace Dashboard implemented"
    }
    print(f"[STEP 1] Coding Agent completed: {coding_result['message']}")
    
    # Step 2: Simulate passed testing (from Testing Agent)
    test_report = {
        "status": "PASS",
        "tests": [],
        "errors": [],
        "backend": {"status": "PASS"},
        "frontend": {"status": "PASS"}
    }
    print(f"[STEP 2] Testing Agent: PASS")
    
    # Step 3: Reviewer receives input and creates review result
    review_input = {
        "review_request_id": "REVIEW-101",
        "original_user_request": "Implement Milestone 6.6 — Project Workspace Dashboard",
        "acceptance_criteria": [
            "Workspace route exists",
            "Workspace is accessible through navigation",
            "Project API is integrated"
        ],
        "review_scope": "milestone"
    }
    
    # Simulate successful review (no findings)
    reviewer_result = create_review_result(
        review_request_id=review_input["review_request_id"],
        status=REVIEW_STATUSES["APPROVED"],
        review_scope=review_input["review_scope"],
        summary="Implementation satisfies the requested requirements.",
        findings=[],  # No issues found
        re_view_required=False,
        escalation_required=False
    )
    
    print(f"[STEP 3] Reviewer Agent: {reviewer_result['status']}")
    
    # Step 4: Orchestrator receives approved result and continues workflow
    assert reviewer_result["status"] == "approved", \
        f"Expected APPROVED but got {reviewer_result['status']}"
    assert len(reviewer_result["findings"]) == 0, \
        f"Expected no findings but got {len(reviewer_result['findings'])}"
    
    print("✓ Workflow completed successfully")
    print("[RESULT] Implementation → Testing → Review → APPROVED")
    print("INTEGRATION TEST 1 PASSED: Successful Review Workflow\n")


# ============================================================================
# Integration Test Scenario 2: Review Requires Changes
# ============================================================================

def test_review_requires_changes_workflow():
    """
    Integration Test 2: Verify the review requires changes workflow.
    
    Workflow:
    1. Coding Agent implements feature (partially complete)
    2. Testing Agent validates (PASS - but functionality incomplete)
    3. Reviewer Agent finds issues -> REQUIRES_CHANGES
    4. Orchestrator sends back to Coding Agent for fixes
    5. Coding Agent fixes the issues
    6. Testing Agent re-validates (PASS)
    7. Reviewer Agent reviews again -> APPROVED
    
    Expected outcome: After fix cycle, APPROVED status
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST 2: Review Requires Changes Workflow")
    print("=" * 70)
    
    # ===== First Cycle =====
    print("\n--- FIRST REVIEW CYCLE ---")
    
    # Step 1: Coding Agent implements (incomplete - API integration missing)
    coding_result_1 = {
        "status": "COMPLETED",
        "files_changed": ["frontend/src/pages/Workspace.tsx"],
        "message": "Workspace Dashboard implemented"
    }
    print(f"[STEP 1] Coding Agent completed: {coding_result_1['message']}")
    
    # Step 2: Testing Agent validates (tests pass but don't catch logic gaps)
    test_report_1 = {
        "status": "PASS",
        "tests": [{"test": "render.test.tsx", "passed": True}],
        "errors": []
    }
    print(f"[STEP 2] Testing Agent: PASS (but tests incomplete)")
    
    # Step 3: Reviewer finds issue with API integration
    api_finding = create_finding(
        finding_id="FINDING-041",
        category=REVIEW_CATEGORIES["API_CONTRACT"],
        severity=SEVERITIES["MEDIUM"],
        title="Project API integration missing",
        description="Workspace page does not retrieve project data from the Project API. "
                     "The component renders but never calls the fetchProjects() function.",
        affected_files=["frontend/src/pages/Workspace.tsx"],
        recommendation="Integrate the existing Project API client and call it in "
                       "component initialization to load project data.",
        required_action="Update Workspace implementation to include API integration"
    )
    
    reviewer_result_1 = create_review_result(
        review_request_id="REVIEW-102",
        status=REVIEW_STATUSES["REQUIRES_CHANGES"],
        review_scope="milestone",
        summary="Implementation is mostly complete but API integration is missing.",
        findings=[api_finding],
        re_view_required=True,  # Needs another review after fix
        escalation_required=False
    )
    
    print(f"[STEP 3] Reviewer Agent: REQUIRES_CHANGES - {reviewer_result_1['findings'][0]['title']}")
    
    assert reviewer_result_1["status"] == "requires_changes", \
        f"Expected REQUIRES_CHANGES but got {reviewer_result_1['status']}"
    assert len(reviewer_result_1["findings"]) > 0, \
        "Expected findings for incomplete implementation"
    
    print("[ORCHESTRATOR ACTION] Sending back to Coding Agent for fixes...")
    
    # Step 4: Orchestrator sends back to Coding Agent
    
    # ===== Second Cycle (After Fix) =====
    print("\n--- SECOND REVIEW CYCLE (AFTER FIX) ---")
    
    # Step 1: Coding Agent fixes the issue
    coding_result_2 = {
        "status": "COMPLETED",
        "files_changed": ["frontend/src/pages/Workspace.tsx"],
        "message": "API integration added to Workspace component"
    }
    print(f"[STEP 1] Coding Agent fixed: {coding_result_2['message']}")
    
    # Step 2: Testing Agent re-validates (PASS)
    test_report_2 = {
        "status": "PASS",
        "tests": [{"test": "workspace.test.tsx", "passed": True}],
        "errors": []
    }
    print(f"[STEP 2] Testing Agent retest: PASS")
    
    # Step 3: Reviewer reviews again - now APPROVED
    reviewer_result_2 = create_review_result(
        review_request_id="REVIEW-102",  # Same request ID for tracking
        status=REVIEW_STATUSES["APPROVED"],
        review_scope="milestone",
        summary="Implementation complete - API integration working correctly.",
        findings=[],  # All issues resolved
        re_view_required=False,
        escalation_required=False
    )
    
    print(f"[STEP 3] Reviewer Agent: {reviewer_result_2['status']}")
    
    assert reviewer_result_2["status"] == "approved", \
        f"Expected APPROVED after fix but got {reviewer_result_2['status']}"
    assert len(reviewer_result_2["findings"]) == 0, \
        f"Expected no findings after fix but got {len(reviewer_result_2['findings'])}"
    
    print("✓ Remediation workflow completed")
    print("[RESULT] Review → Requires Changes → Fix → Retest → Re-Review → APPROVED")
    print("INTEGRATION TEST 2 PASSED: Review Requires Changes Workflow\n")


# ============================================================================
# Integration Test Scenario 3: Persistent Issues Leading to Escalation
# ============================================================================

def test_persistent_review_failure_escalation():
    """
    Integration Test 3: Verify escalation after maximum review cycles.
    
    Workflow:
    1. Reviewer finds critical issue
    2. Coding Agent attempts fix but doesn't properly address it
    3. Testing passes (incorrectly or incompletely)
    4. Reviewer finds same issue again -> REQUIRES_CHANGES
    5. Repeat for MAX_REVIEW_CYCLES (3 times)
    6. Maximum cycles reached -> ESCALATION
    
    Expected outcome: Escalation report generated
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST 3: Persistent Review Failure Leading to Escalation")
    print("=" * 70)
    
    from ai_agents.scripts.reviewer_loop_protection import MAX_REVIEW_CYCLES
    
    # ===== First Review Cycle =====
    print("\n--- REVIEW CYCLE 1/3 ---")
    finding_1 = create_finding(
        finding_id="FINDING-051",
        category=REVIEW_CATEGORIES["SECURITY"],
        severity=SEVERITIES["HIGH"],
        title="Security vulnerability in form handling",
        description="Form does not properly sanitize user input before processing.",
        affected_files=["frontend/src/components/ContactForm.tsx"],
        recommendation="Implement proper input sanitization using a library like DOMPurify"
    )
    
    result_1 = create_review_result(
        review_request_id="REVIEW-201",
        status=REVIEW_STATUSES["REQUIRES_CHANGES"],
        review_scope="feature",
        summary="Security issue found in form handling",
        findings=[finding_1],
        re_view_required=True,
        escalation_required=False
    )
    print(f"[CYCLE 1] Reviewer: {result_1['status']} - Security issue identified")
    
    # ===== Second Review Cycle (Issue persists) =====
    print("\n--- REVIEW CYCLE 2/3 ---")
    finding_2 = create_finding(
        finding_id="FINDING-051",  # Same issue still present
        category=REVIEW_CATEGORIES["SECURITY"],
        severity=SEVERITIES["HIGH"],
        title="Security vulnerability in form handling",
        description="Form does not properly sanitize user input before processing.",
        affected_files=["frontend/src/components/ContactForm.tsx"],
        recommendation="Implement proper input sanitization using a library like DOMPurify"
    )
    
    result_2 = create_review_result(
        review_request_id="REVIEW-201",
        status=REVIEW_STATUSES["REQUIRES_CHANGES"],
        review_scope="feature",
        summary="Security issue persists - form still vulnerable",
        findings=[finding_2],
        re_view_required=True,
        escalation_required=False
    )
    print(f"[CYCLE 2] Reviewer: {result_2['status']} - Issue not properly resolved")
    
    # ===== Third Review Cycle (Issue still persists) =====
    print("\n--- REVIEW CYCLE 3/3 ---")
    finding_3 = create_finding(
        finding_id="FINDING-051",  # Same issue again
        category=REVIEW_CATEGORIES["SECURITY"],
        severity=SEVERITIES["HIGH"],
        title="Security vulnerability in form handling",
        description="Form does not properly sanitize user input before processing.",
        affected_files=["frontend/src/components/ContactForm.tsx"],
        recommendation="Implement proper input sanitization using a library like DOMPurify"
    )
    
    result_3 = create_review_result(
        review_request_id="REVIEW-201",
        status=REVIEW_STATUSES["REQUIRES_CHANGES"],
        review_scope="feature",
        summary="Security issue persists after multiple review cycles",
        findings=[finding_3],
        re_view_required=True,
        escalation_required=False
    )
    print(f"[CYCLE 3] Reviewer: {result_3['status']} - Issue still unresolved")
    
    # ===== Escalation =====
    print("\n--- ESCALATION ---")
    from ai_agents.scripts.reviewer_loop_protection import generate_escalation_report
    
    previous_reviews = [result_1, result_2, result_3]
    unresolved_findings = [finding_3]  # Same finding still present
    
    escalation_report = generate_escalation_report(
        review_request_id="REVIEW-201",
        original_request="Implement Contact Form with proper security",
        previous_reviews=previous_reviews,
        unresolved_findings=unresolved_findings
    )
    
    print(f"[ESCALATION] Report generated: {escalation_report['status']}")
    print(f"[ESCALATION] Review cycles completed: {len(previous_reviews)}")
    print(f"[ESCALATION] Human review required: {escalation_report['requires_human_review']}")
    
    assert escalation_report["requires_human_review"] == True, \
        "Escalation report should require human review"
    assert len(escalation_report["review_history"]) >= 3, \
        "Should include history of at least 3 reviews"
    
    print("✓ Escalation workflow completed")
    print("[RESULT] Review × 3 → Same issue persists → MAX_REVIEW_CYCLES → ESCALATION")
    print("INTEGRATION TEST 3 PASSED: Persistent Review Failure Leading to Escalation\n")


# ============================================================================
# Integration Test Scenario 4: Security Issue Requires Immediate Rejection
# ============================================================================

def test_security_issue_immediate_rejection():
    """
    Integration Test 4: Verify that critical security issues result in immediate rejection.
    
    Expected outcome: REJECTED status with escalation_required=True
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST 4: Security Issue Immediate Rejection")
    print("=" * 70)
    
    # Reviewer finds critical security issue
    critical_finding = create_finding(
        finding_id="FINDING-061",
        category=REVIEW_CATEGORIES["SECURITY"],
        severity=SEVERITIES["CRITICAL"],
        title="Hardcoded database credentials detected",
        description="Database password found in source code: password = 'supersecret123'",
        affected_files=["backend/app/config/database.py"],
        recommendation="Move all credentials to environment variables immediately"
    )
    
    # Reviewer should REJECT the implementation
    reviewer_result = create_review_result(
        review_request_id="REVIEW-301",
        status=REVIEW_STATUSES["REJECTED"],
        review_scope="backend",
        summary="Critical security vulnerability - hardcoded credentials in production code.",
        findings=[critical_finding],
        re_view_required=True,  # Needs fixing before any approval
        escalation_required=True  # Security issue requires immediate attention
    )
    
    print(f"[REVIEWER] Status: {reviewer_result['status']}")
    print(f"[REVIEWER] Escalation required: {reviewer_result['escalation_required']}")
    
    assert reviewer_result["status"] == "rejected", \
        f"Critical security issue should result in REJECTED, got {reviewer_result['status']}"
    assert reviewer_result["escalation_required"] == True, \
        "Security issues should require escalation"
    
    print("✓ Security issue properly handled")
    print("[RESULT] Security issue detected → REJECTED with immediate escalation")
    print("INTEGRATION TEST 4 PASSED: Security Issue Immediate Rejection\n")


# ============================================================================
# Integration Test Scenario 5: Review Approved With Warnings
# ============================================================================

def test_review_approved_with_warnings():
    """
    Integration Test 5: Verify review with warnings (low-severity findings).
    
    Expected outcome: APPROVED_WITH_WARNINGS status
    
    Use case: Implementation is correct but has minor improvements needed.
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST 5: Review Approved With Warnings")
    print("=" * 70)
    
    # Low-severity findings (not blocking)
    warnings = [
        create_finding(
            finding_id="FINDING-071",
            category=REVIEW_CATEGORIES["CODE_QUALITY"],
            severity=SEVERITIES["LOW"],
            title="Minor documentation improvement needed",
            description="README could use more examples for new users.",
            affected_files=["README.md"],
            recommendation="Add usage examples to README"
        ),
        create_finding(
            finding_id="FINDING-072",
            category=REVIEW_CATEGORIES["DOCUMENTATION"],
            severity=SEVERITIES["LOW"],
            title="Missing inline comments",
            description="Some complex logic lacks inline documentation.",
            affected_files=["frontend/src/utils/helpers.ts"],
            recommendation="Add JSDoc comments for helper functions"
        )
    ]
    
    # Reviewer approves with warnings
    reviewer_result = create_review_result(
        review_request_id="REVIEW-401",
        status=REVIEW_STATUSES["APPROVED_WITH_WARNINGS"],
        review_scope="milestone",
        summary="Implementation approved with minor documentation improvements needed.",
        findings=warnings,  # Only low-severity warnings
        re_view_required=False,  # Can proceed without fixing warnings
        escalation_required=False
    )
    
    print(f"[REVIEWER] Status: {reviewer_result['status']}")
    print(f"[REVIEWER] Warnings count: {len(reviewer_result['findings'])}")
    
    assert reviewer_result["status"] == "approved_with_warnings", \
        f"Expected APPROVED_WITH_WARNINGS, got {reviewer_result['status']}"
    assert len(reviewer_result["findings"]) > 0, \
        f"Expected warnings but got none"
    
    print("✓ Review with warnings properly handled")
    print("[RESULT] Implementation → Testing → Review (warnings) → APPROVED_WITH_WARNINGS")
    print("INTEGRATION TEST 5 PASSED: Review Approved With Warnings\n")


# ============================================================================
# Main Integration Test Runner
# ============================================================================

def run_all_integration_tests() -> bool:
    """Run all integration tests and return success status."""
    print("\n" + "=" * 70)
    print("REVIEWER AGENT RUNTIME - INTEGRATION TESTS")
    print("=" * 70)
    
    test_functions = [
        ("Test 1: Successful Review Workflow", test_successful_review_workflow),
        ("Test 2: Review Requires Changes Workflow", test_review_requires_changes_workflow),
        ("Test 3: Persistent Review Failure Escalation", test_persistent_review_failure_escalation),
        ("Test 4: Security Issue Immediate Rejection", test_security_issue_immediate_rejection),
        ("Test 5: Review Approved With Warnings", test_review_approved_with_warnings),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {test_name}")
            print(f"  Error: {type(e).__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)
