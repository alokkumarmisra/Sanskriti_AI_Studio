#!/usr/bin/env python3
"""
Enhanced Reviewer Agent Input Schema for Sanskriti AI Studio.

This module provides structured input validation and schema enforcement
for the enhanced Reviewer Agent workflow.

Version: 2.0 - Enhanced Reviewer Agent with advanced workflow support
Last Updated: 2026-07-30
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")


# ============================================================================
# Review Status Values (Enhanced Workflow)
# ============================================================================

REVIEW_STATUSES = {
    "APPROVED": "Implementation approved - all criteria met, no blocking issues",
    "APPROVED_WITH_WARNINGS": "Implementation approved with minor/low-severity warnings",
    "REQUIRES_CHANGES": "Changes required before approval - medium/high findings or incomplete acceptance criteria",
    "REJECTED": "Implementation rejected - critical requirements violated or severe issues",
    "BLOCKED": "Review blocked - evidence unavailable, validation cannot be performed, or human review required"
}

VALID_REVIEW_SCOPES = ["task", "milestone", "feature", "frontend", "backend", "API", "database", "documentation", "agent_runtime", "full_workflow"]


# ============================================================================
# Severity Levels - Converted to dictionary (was set)
# ============================================================================

SEVERITIES = {
    "CRITICAL": "Critical severity issue - immediate attention required",
    "HIGH": "High severity issue - should be addressed before release",
    "MEDIUM": "Medium severity issue - should be fixed in next iteration",
    "LOW": "Low severity issue - minor improvement or documentation update",
    "INFO": "Informational finding - no action required"
}


# ============================================================================
# Review Categories (Expanded)
# ============================================================================

REVIEW_CATEGORIES = {
    "REQUIREMENTS_COMPLIANCE": "Requirement specification compliance",
    "PLAN_COMPLIANCE": "Execution plan adherence",
    "ACCEPTANCE_CRITERIA": "Acceptance criteria satisfaction",
    "ARCHITECTURE": "System architecture and boundaries",
    "CODE_QUALITY": "Code quality, maintainability, conventions",
    "FRONTEND": "Frontend implementation",
    "BACKEND": "Backend implementation",
    "API_CONTRACT": "API contracts and integration",
    "DATABASE": "Database schema and operations",
    "TESTING": "Test coverage and quality",
    "ERROR_HANDLING": "Error handling and edge cases",
    "SECURITY": "Security vulnerabilities and best practices",
    "PERFORMANCE": "Performance concerns",
    "DOCUMENTATION": "Documentation completeness",
    "REGRESSION_RISK": "Regression risk assessment",
    "PROJECT_RULES": "Project rules compliance",
    "BENCHMARK_COMPLIANCE": "Benchmark and quality standards"
}


# ============================================================================
# Review Input Schema Definition
# ============================================================================

def create_review_input_schema() -> Dict[str, Any]:
    """
    Create the enhanced structured review input schema.
    
    This schema supports all advanced reviewer features including:
    - Full review context (task, plan, criteria, results)
    - Independent verification against evidence
    - Comprehensive status determination
    
    Returns:
        Dictionary defining the review input schema
    """
    return {
        "review_request_id": {
            "type": "string",
            "description": "Unique identifier for the review request",
            "example": "REVIEW-001",
            "required": True,
            "pattern": r"^REVIEW-\d{3}$"
        },
        "original_user_request": {
            "type": "string",
            "description": "Original user request or task description",
            "example": "Implement Milestone 6.6 — Project Workspace Dashboard",
            "required": True
        },
        "plan_id": {
            "type": "string",
            "description": "Identifier for the execution plan being reviewed",
            "example": "PLAN-6.6-001",
            "required": False
        },
        "milestone": {
            "type": "string",
            "description": "Milestone number being reviewed (e.g., '6.6')",
            "example": "6.6",
            "required": False
        },
        "task_id": {
            "type": "string",
            "description": "Task identifier for the completed work",
            "example": "TASK-6.6-001",
            "required": False
        },
        "review_scope": {
            "type": "string",
            "enum": VALID_REVIEW_SCOPES,
            "description": "Scope of the review - what aspects to focus on",
            "example": "milestone",
            "required": True
        },
        "completed_tasks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of completed task IDs",
            "example": ["TASK-6.1-001", "TASK-6.2-001"],
            "required": False,
            "default": []
        },
        "changed_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files modified during implementation",
            "example": [
                "frontend/src/pages/Workspace.tsx",
                "frontend/src/routes/index.tsx"
            ],
            "required": False,
            "default": []
        },
        "created_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files created during implementation",
            "example": ["frontend/src/components/WorkspacePanel.tsx"],
            "required": False,
            "default": []
        },
        "deleted_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files deleted during implementation",
            "example": ["frontend/src/pages/DeprecatedPage.tsx"],
            "required": False,
            "default": []
        },
        "git_diff": {
            "type": "string",
            "description": "Git diff showing all changes (optional)",
            "example": "diff --git a/file.py b/file.py\n...",
            "required": False,
            "default": ""
        },
        "project_context": {
            "type": "object",
            "additionalProperties": True,
            "description": "Additional project context information",
            "example": {"environment": "development", "branch": "feature/workspace"},
            "required": False,
            "default": {}
        },
        "relevant_documentation": {
            "type": "object",
            "additionalProperties": True,
            "description": "Relevant documentation for review context",
            "example": {
                "docs/05_ROADMAP.md": "...content...",
                "docs/11_CHANGELOG.md": "...content..."
            },
            "required": False,
            "default": {}
        },
        "project_rules": {
            "type": "string",
            "description": "Project rules and guidelines for compliance checking",
            "example": "# Project Rules\n...content...",
            "required": False,
            "default": ""
        },
        "benchmarks": {
            "type": "object",
            "description": "Quality benchmarks to validate against",
            "example": {
                "response_time_ms": 500,
                "code_quality_score": 0.9,
                "test_coverage_percent": 80
            },
            "required": False,
            "default": {}
        },
        "acceptance_criteria": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of acceptance criteria to verify",
            "example": [
                "Workspace route exists",
                "Workspace is accessible through navigation",
                "Project API is integrated"
            ],
            "required": True,
            "minItems": 1
        },
        "test_results": {
            "type": "object",
            "description": "Testing Agent results for review",
            "example": {
                "status": "passed",
                "tests": [...],
                "errors": [],
                "backend": {"status": "PASS"},
                "frontend": {"status": "PASS"}
            },
            "required": False,
            "default": {}
        },
        "lint_results": {
            "type": "object",
            "description": "Linting results for review",
            "example": {
                "status": "passed",
                "errors": [],
                "warnings": []
            },
            "required": False,
            "default": {}
        },
        "build_results": {
            "type": "object",
            "description": "Build results for review",
            "example": {
                "status": "passed",
                "output": "...",
                "warnings": []
            },
            "required": False,
            "default": {}
        },
        "runtime_results": {
            "type": "object",
            "description": "Runtime validation results if applicable",
            "example": {
                "startup_check": "passed",
                "api_health": "healthy"
            },
            "required": False,
            "default": {}
        },
        "previous_debugging_reports": {
            "type": "array",
            "items": {"type": "object"},
            "description": "Previous debugging reports for context",
            "example": [{"report_id": "DEBUG-001", "status": "resolved"}],
            "required": False,
            "default": []
        },
        "previous_review_attempts": {
            "type": "array",
            "items": {"type": "object"},
            "description": "Previous review results for loop protection",
            "example": [
                {
                    "review_id": "REVIEW-001",
                    "status": "requires_changes",
                    "findings": [{"finding_id": "FINDING-001", "resolved": False}]
                }
            ],
            "required": False,
            "default": []
        }
    }


def validate_review_input(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a review input against the schema.
    
    Args:
        data: Dictionary containing review input data
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required fields
    if "review_request_id" not in data:
        errors.append("Missing required field: review_request_id")
    elif not re.match(r"^REVIEW-\d{3}$", str(data["review_request_id"])):
        errors.append(f"Invalid review_request_id format: {data['review_request_id']} (expected REVIEW-XXX)")
    
    if "original_user_request" not in data:
        errors.append("Missing required field: original_user_request")
    
    if "acceptance_criteria" not in data:
        errors.append("Missing required field: acceptance_criteria")
    elif not isinstance(data["acceptance_criteria"], list) or len(data["acceptance_criteria"]) == 0:
        errors.append("acceptance_criteria must be a non-empty list of strings")
    
    if "review_scope" not in data:
        errors.append("Missing required field: review_scope")
    elif data["review_scope"] not in VALID_REVIEW_SCOPES:
        valid_scopes_str = ", ".join(VALID_REVIEW_SCOPES)
        errors.append(f"Invalid review_scope: {data['review_scope']}. Valid scopes: {valid_scopes_str}")
    
    # Validate severity if findings exist (for output validation)
    if "findings" in data and isinstance(data["findings"], list):
        for finding in data["findings"]:
            if isinstance(finding, dict):
                if "severity" in finding and finding["severity"] not in SEVERITIES:
                    errors.append(f"Invalid severity '{finding.get('severity')}' in finding")
                if "category" in finding and finding["category"] not in REVIEW_CATEGORIES:
                    errors.append(f"Invalid category '{finding.get('category')}' in finding")
    
    # Validate status if provided
    if "status" in data and data["status"] not in REVIEW_STATUSES.keys():
        valid_statuses = ", ".join(REVIEW_STATUSES.keys())
        errors.append(f"Invalid status: {data['status']}. Valid statuses: {valid_statuses}")
    
    return len(errors) == 0, errors


def create_empty_review_input() -> Dict[str, Any]:
    """
    Create an empty review input for testing edge cases.
    
    Returns:
        Minimal review input with only required fields
    """
    return {
        "review_request_id": f"REVIEW-{datetime.now().strftime('%Y%m%d')}-000",
        "original_user_request": "",
        "acceptance_criteria": [],
        "review_scope": "task"
    }


def create_validated_sample_review_input() -> Dict[str, Any]:
    """
    Create a sample validated review input for testing.
    
    Returns:
        Sample review input with all fields populated
    """
    return {
        "review_request_id": "REVIEW-001",
        "original_user_request": "Implement Milestone 6.6 — Project Workspace Dashboard",
        "plan_id": "PLAN-6.6-001",
        "milestone": "6.6",
        "task_id": "TASK-6.6-001",
        "review_scope": "milestone",
        "completed_tasks": ["TASK-6.6-001"],
        "changed_files": [
            "frontend/src/pages/Workspace.tsx",
            "frontend/src/routes/index.tsx"
        ],
        "created_files": [],
        "deleted_files": [],
        "git_diff": "",
        "project_context": {
            "environment": "development",
            "branch": "feature/workspace"
        },
        "relevant_documentation": {},
        "project_rules": "# Project Rules\n- Use TypeScript for frontend\n- Follow existing folder structure\n- Add tests for new components",
        "benchmarks": {
            "response_time_ms": 500,
            "code_quality_score": 0.9
        },
        "acceptance_criteria": [
            "Workspace route exists",
            "Workspace is accessible through navigation",
            "Project API is integrated"
        ],
        "test_results": {
            "status": "passed",
            "tests": [],
            "errors": [],
            "backend": {"status": "PASS"},
            "frontend": {"status": "PASS"}
        },
        "lint_results": {
            "status": "passed",
            "errors": [],
            "warnings": []
        },
        "build_results": {
            "status": "passed",
            "output": "...",
            "warnings": []
        },
        "runtime_results": {
            "startup_check": "passed",
            "api_health": "healthy"
        },
        "previous_debugging_reports": [],
        "previous_review_attempts": []
    }


# ============================================================================
# Finding Schema
# ============================================================================

def create_finding_schema() -> Dict[str, Any]:
    """
    Create schema for individual review findings.
    
    Each finding must contain:
    - finding_id: Unique identifier
    - category: Review category
    - severity: CRITICAL, HIGH, MEDIUM, LOW, INFO
    - title: Brief description
    - description: Detailed explanation with evidence
    - affected_files: Files where issue was found
    - acceptance_criteria_affected: Which criteria this finding impacts (optional)
    - recommendation: Recommended fix
    - required_action: Action needed to resolve
    
    Returns:
        Dictionary defining the finding schema
    """
    return {
        "finding_id": {
            "type": "string",
            "description": "Unique identifier for the finding",
            "example": "FINDING-001",
            "required": True,
            "pattern": r"^FINDING-\d{3}$"
        },
        "category": {
            "type": "string",
            "description": "Review category",
            "enum": list(REVIEW_CATEGORIES.keys()),
            "example": "ACCEPTANCE_CRITERIA",
            "required": True
        },
        "severity": {
            "type": "string",
            "description": "Severity level",
            "enum": list(SEVERITIES),
            "example": "HIGH",
            "required": True
        },
        "title": {
            "type": "string",
            "description": "Brief description of the finding",
            "example": "Project API integration missing",
            "required": True
        },
        "description": {
            "type": "string",
            "description": "Detailed explanation with evidence",
            "example": "Workspace page does not retrieve project data from the Project API. The component renders but never calls the fetchProjects() function.",
            "required": True
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Evidence supporting this finding",
            "example": ["Component HTML shows no API call", "Console logs confirm no data loaded"],
            "required": False,
            "default": []
        },
        "affected_files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Files where the issue was found",
            "example": ["frontend/src/pages/Workspace.tsx"],
            "required": True
        },
        "acceptance_criteria_affected": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Which acceptance criteria are affected (optional)",
            "example": ["Workspace route exists"],
            "required": False,
            "default": []
        },
        "recommendation": {
            "type": "string",
            "description": "Recommended fix or improvement",
            "example": "Integrate the existing Project API client and call it in component initialization.",
            "required": True
        },
        "required_action": {
            "type": "string",
            "description": "Action required to resolve this finding",
            "example": "Update Workspace implementation to include API integration",
            "required": True
        }
    }


def create_finding(
    finding_id: str,
    category: str,
    severity: str,
    title: str,
    description: str,
    affected_files: List[str],
    acceptance_criteria_affected: Optional[List[str]] = None,
    evidence: Optional[List[str]] = None,
    recommendation: str = "Review and fix the issue.",
    required_action: str = "Address this finding before approval."
) -> Dict[str, Any]:
    """
    Create a structured review finding.
    
    Args:
        finding_id: Unique identifier (e.g., "FINDING-001")
        category: Review category from REVIEW_CATEGORIES
        severity: Severity level from SEVERITIES
        title: Brief description
        description: Detailed explanation with evidence
        affected_files: List of files where issue was found
        acceptance_criteria_affected: Affected acceptance criteria (optional)
        evidence: Evidence supporting the finding (optional)
        recommendation: Recommended fix
        required_action: Action needed to resolve
    
    Returns:
        Dictionary representing a structured review finding
    """
    return {
        "finding_id": finding_id,
        "category": category,
        "severity": severity,
        "title": title,
        "description": description,
        "evidence": evidence or [],
        "affected_files": affected_files,
        "acceptance_criteria_affected": acceptance_criteria_affected or [],
        "recommendation": recommendation,
        "required_action": required_action
    }


# ============================================================================
# Review Output Schema
# ============================================================================

def create_review_output_schema() -> Dict[str, Any]:
    """
    Create schema for structured review output.
    
    The reviewer agent returns a structured review result containing:
    - Status determination (APPROVED, APPROVED_WITH_WARNINGS, etc.)
    - Summary of the review
    - Findings with full details
    - Acceptance criteria verification results
    - Evidence validation status
    - Risks and regression assessment
    
    Returns:
        Dictionary defining the review output schema
    """
    return {
        "review_request_id": {
            "type": "string",
            "description": "Original review request ID",
            "required": True,
            "example": "REVIEW-001"
        },
        "status": {
            "type": "string",
            "description": "Final review status",
            "enum": list(REVIEW_STATUSES.keys()),
            "example": "requires_changes",
            "required": True
        },
        "review_scope": {
            "type": "string",
            "description": "Scope of the review performed",
            "enum": VALID_REVIEW_SCOPES,
            "example": "milestone",
            "required": True
        },
        "summary": {
            "type": "string",
            "description": "Concise summary of the review findings",
            "example": "Implementation is mostly complete but one mandatory acceptance criterion is not satisfied.",
            "required": True
        },
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Reviewer confidence level based on available evidence",
            "example": "high",
            "default": "medium"
        },
        "requirements_compliance": {
            "type": "object",
            "description": "Requirements compliance verification",
            "example": {
                "status": "passed",
                "evidence": ["All stated requirements implemented"],
                "missing_requirements": []
            }
        },
        "plan_compliance": {
            "type": "object",
            "description": "Plan compliance verification",
            "example": {
                "planned_tasks_completed": 5,
                "planned_tasks_partially_completed": 0,
                "planned_tasks_skipped": 0,
                "additional_unplanned_changes": [],
                "scope_creep_detected": False
            }
        },
        "acceptance_criteria_results": {
            "type": "array",
            "description": "Acceptance criteria verification results with evidence",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "status": {"type": "string", "enum": ["passed", "failed", "partially_passed", "not_verified"]},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "related_files": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"}
                }
            },
            "example": [
                {
                    "criterion": "Workspace route is accessible",
                    "status": "passed",
                    "evidence": ["Route registered in frontend router", "Navigation link points to /workspace"]
                }
            ],
            "required": True
        },
        "findings": {
            "type": "array",
            "description": "List of all review findings",
            "items": {"$ref": "#/definitions/Finding"},
            "example": [
                {
                    "finding_id": "FINDING-001",
                    "category": "ACCEPTANCE_CRITERIA",
                    "severity": "high",
                    "title": "Project API integration missing",
                    "description": "Workspace page does not retrieve project data from the Project API.",
                    "affected_files": ["frontend/src/pages/Workspace.tsx"],
                    "recommendation": "Integrate the existing Project API client.",
                    "required_action": "Update Workspace implementation."
                }
            ],
            "required": True
        },
        "verified_items": {
            "type": "array",
            "items": {"type": "object"},
            "description": "Items verified during review",
            "example": [
                {"item": "Workspace route exists", "status": "verified", "evidence": ["Route found in router"]},
                {"item": "Navigation integration", "status": "verified", "evidence": ["Navigation link present"]}
            ],
            "required": False,
            "default": []
        },
        "unverified_items": {
            "type": "array",
            "items": {"type": "object"},
            "description": "Items that could not be verified (missing evidence)",
            "example": [
                {"item": "Database migration completed", "status": "not_verified", "reason": "Migration log unavailable"}
            ],
            "required": False,
            "default": []
        },
        "risks": {
            "type": "array",
            "items": {"type": "object"},
            "description": "Identified risks with severity and mitigation",
            "example": [
                {
                    "risk": "API rate limiting possible under high load",
                    "severity": "LOW",
                    "likelihood": "MEDIUM",
                    "impact": "LOW",
                    "mitigation": "Implement request queuing"
                }
            ],
            "required": False,
            "default": []
        },
        "regression_risk": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Overall regression risk assessment",
            "example": "low",
            "default": "low"
        },
        "recommended_actions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of recommended next steps",
            "example": [
                "Fix API integration in Workspace component",
                "Add tests for new API endpoints"
            ],
            "required": True
        },
        "re_review_required": {
            "type": "boolean",
            "description": "Whether another review cycle is recommended",
            "example": True,
            "default": False
        },
        "escalation_required": {
            "type": "boolean",
            "description": "Whether this issue requires human escalation",
            "example": False,
            "default": False
        }
    }


def create_review_result(
    review_request_id: str,
    status: str,
    review_scope: str,
    summary: str,
    findings: List[Dict[str, Any]],
    re_view_required: bool = False,
    escalation_required: bool = False
) -> Dict[str, Any]:
    """
    Create a structured review result.
    
    Args:
        review_request_id: Original review request ID
        status: Final review status from REVIEW_STATUSES
        review_scope: Scope of the review
        summary: Review summary
        findings: List of findings (can use create_finding())
        re_view_required: Whether another review cycle is recommended
        escalation_required: Whether human escalation is needed
    
    Returns:
        Dictionary representing a structured review result
    """
    # Convert status to lowercase for JSON compatibility while keeping enum values
    status_lower = status.lower() if status in REVIEW_STATUSES else "unknown"
    
    return {
        "review_request_id": review_request_id,
        "status": status_lower,
        "review_scope": review_scope,
        "summary": summary,
        "confidence": "high",  # Default high confidence for deterministic findings
        "requirements_compliance": {"status": "unknown"},
        "plan_compliance": {
            "planned_tasks_completed": 0,
            "planned_tasks_partially_completed": 0,
            "planned_tasks_skipped": 0,
            "additional_unplanned_changes": [],
            "scope_creep_detected": False
        },
        "acceptance_criteria_results": [],
        "findings": findings,
        "verified_items": [],
        "unverified_items": [],
        "risks": [],
        "regression_risk": "low",
        "recommended_actions": [f["recommendation"] for f in findings] if findings else ["No issues found"],
        "re_review_required": re_view_required,
        "escalation_required": escalation_required,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def create_empty_findings_list(count: int = 0) -> List[Dict[str, Any]]:
    """
    Create an empty findings list with proper schema.
    
    Args:
        count: Number of placeholder findings (optional)
    
    Returns:
        Empty or populated findings list
    """
    return []
