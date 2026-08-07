#!/usr/bin/env python3
"""
Reviewer Agent Loop Protection for Sanskriti AI Studio.

This module implements review loop protection to prevent infinite review cycles,
tracks repeated findings, and generates escalation reports when maximum
review cycles are reached.

Version: 2.0 - Enhanced Reviewer Agent
Last Updated: 2026-07-30
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
ACTIONS_PATH = os.path.join(STATE_DIR, "actions.jsonl")


# ============================================================================
# Review Cycle Configuration
# ============================================================================

MAX_REVIEW_CYCLES = 3


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append a reviewer action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "reviewer_loop_protection",
        "action_type": action_type,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(ACTIONS_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


# ============================================================================
# Finding Normalization for Repeated Finding Detection
# ============================================================================

def normalize_finding(finding: Dict[str, Any]) -> str:
    """
    Create a normalized signature for a finding to detect repeated findings.
    
    Args:
        finding: A review finding dictionary
    
    Returns:
        Normalized string signature of the finding
    """
    return json.dumps(
        {
            "category": finding.get("category", ""),
            "severity": finding.get("severity", ""),
            "title": finding.get("title", "").lower().strip(),
            "problem": finding.get("description", "").lower().strip()[:200],
            "file": str(finding.get("file")) or "",
        },
        sort_keys=True
    )


def find_repeated_findings(
    current_findings: List[Dict[str, Any]],
    previous_findings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Find findings that repeat from previous review attempts.
    
    Args:
        current_findings: Findings from current review
        previous_findings: Findings from previous reviews
    
    Returns:
        List of findings with their repeat history
    """
    repeated = []
    signatures_seen: Set[str] = set()
    
    # Normalize and track previous finding signatures
    for finding in previous_findings:
        signature = normalize_finding(finding)
        if signature not in signatures_seen:
            signatures_seen.add(signature)
    
    # Check current findings against previous
    for current_finding in current_findings:
        current_signature = normalize_finding(current_finding)
        
        if current_signature in signatures_seen:
            # This finding has appeared before
            repeated.append({
                "finding": current_finding,
                "count": 2 + len([f for f in previous_findings if normalize_finding(f) == current_signature]),
                "first_appearance": True  # Simplified - would need to track timestamps
            })
        else:
            signatures_seen.add(current_signature)
    
    return repeated


def check_loop_protection(
    review_request_id: str,
    previous_review_attempts: Optional[List[Dict[str, Any]]] = None,
    current_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Check for loop protection violations.
    
    Args:
        review_request_id: Current review request ID
        previous_review_attempts: Previous review results with findings
        current_findings: Findings from current review attempt
    
    Returns:
        Loop protection status and recommendations
    """
    if previous_review_attempts is None:
        previous_review_attempts = []
    
    if current_findings is None:
        current_findings = []
    
    # Flatten all previous findings
    all_previous_findings: List[Dict[str, Any]] = []
    for attempt in previous_review_attempts:
        findings = attempt.get("findings", [])
        if findings and isinstance(findings, list):
            all_previous_findings.extend(findings)
    
    # Find repeated findings
    repeated = find_repeated_findings(current_findings, all_previous_findings)
    
    # Determine review cycle number
    review_cycle_count = len(previous_review_attempts) + 1
    
    is_at_max = review_cycle_count >= MAX_REVIEW_CYCLES
    has_repeated_findings = len(repeated) > 0
    
    if is_at_max:
        status = "MAX_REVIEW_CYCLES_REACHED"
    elif has_repeated_findings:
        status = "REPEATED_FINDINGS_DETECTED"
    else:
        status = "OK"
    
    return {
        "review_request_id": review_request_id,
        "review_cycle_count": review_cycle_count,
        "max_review_cycles": MAX_REVIEW_CYCLES,
        "is_at_max": is_at_max,
        "has_repeated_findings": has_repeated_findings,
        "repeated_findings": repeated,
        "status": status,
        "recommendation": _get_recommendation(status, review_cycle_count)
    }


def _get_recommendation(status: str, cycle_count: int) -> str:
    """Get recommendation based on loop protection status."""
    if status == "MAX_REVIEW_CYCLES_REACHED":
        return (
            f"Maximum review cycles ({MAX_REVIEW_CYCLES}) reached. "
            "Escalation required - manual intervention needed."
        )
    elif status == "REPEATED_FINDINGS_DETECTED":
        return (
            f"Repeated findings detected across {cycle_count} review cycle(s). "
            "Verify that fixes are actually being applied, not just claimed."
        )
    else:
        return "Review loop protection check passed."


# ============================================================================
# Escalation Report Generation
# ============================================================================

def generate_escalation_report(
    review_request_id: str,
    original_request: str,
    previous_reviews: List[Dict[str, Any]],
    unresolved_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a human-readable escalation report.
    
    Args:
        review_request_id: The review request ID
        original_request: Original user request
        previous_reviews: Previous review results
        unresolved_findings: Findings that could not be resolved
    
    Returns:
        Escalation report dictionary
    """
    # Group unresolved findings by category and severity
    findings_by_category: Dict[str, List[Dict[str, Any]]] = {}
    for finding in unresolved_findings:
        category = finding.get("category", "UNKNOWN")
        if category not in findings_by_category:
            findings_by_category[category] = []
        findings_by_category[category].append(finding)
    
    # Build escalation report
    report = {
        "escalation_request_id": f"ESCALATION-{review_request_id}",
        "original_user_request": original_request,
        "review_request_id": review_request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "MAX_REVIEW_CYCLES_REACHED",
        "summary": _build_escalation_summary(review_request_id, previous_reviews),
        "unresolved_findings_by_category": {cat: findings for cat, findings in findings_by_category.items()},
        "review_history": [
            {
                "review_id": r.get("review_request_id", "unknown"),
                "status": r.get("status", "unknown"),
                "findings_count": len(r.get("findings", [])),
                "findings": r.get("findings", [])[:3]  # Limit to first 3 findings for brevity
            }
            for r in previous_reviews[-3:]  # Show last 3 reviews
        ],
        "recommendations": _build_escalation_recommendations(unresolved_findings),
        "requires_human_review": True
    }
    
    return report


def _build_escalation_summary(
    review_request_id: str,
    previous_reviews: List[Dict[str, Any]]
) -> str:
    """Build human-readable escalation summary."""
    cycle_count = len(previous_reviews) + 1
    
    # Count findings per severity across all reviews
    total_critical = sum(
        len([f for f in r.get("findings", []) if f.get("severity") == "CRITICAL"])
        for r in previous_reviews
    )
    total_high = sum(
        len([f for f in r.get("findings", []) if f.get("severity") == "HIGH"])
        for r in previous_reviews
    )
    total_medium = sum(
        len([f for f in r.get("findings", []) if f.get("severity") == "MEDIUM"])
        for r in previous_reviews
    )
    
    return (
        f"Escalation Report for {review_request_id}\n\n"
        f"This task has exceeded the maximum review cycle limit ({cycle_count} cycles).\n"
        f"The same issues have persisted across multiple review attempts.\n\n"
        f"Summary of findings by severity:\n"
        f"- Critical: {total_critical}\n"
        f"- High: {total_high}\n"
        f"- Medium: {total_medium}\n\n"
        f"A human reviewer should assess whether:\n"
        f"1. The implementation requirements are clear and achievable\n"
        f"2. Automated testing is providing accurate feedback\n"
        f"3. Additional context or clarification is needed\n"
        f"4. Manual intervention is required"
    )


def _build_escalation_recommendations(
    unresolved_findings: List[Dict[str, Any]]
) -> List[str]:
    """Build recommendations for human reviewer."""
    recommendations = []
    
    # Analyze finding patterns
    critical_high_count = len([f for f in unresolved_findings if f.get("severity") in ["CRITICAL", "HIGH"]])
    acceptance_criteria_failures = [
        f for f in unresolved_findings 
        if f.get("category") == "ACCEPTANCE_CRITERIA"
    ]
    security_issues = [
        f for f in unresolved_findings 
        if f.get("category") == "SECURITY"
    ]
    
    if critical_high_count > 0:
        recommendations.append(
            "Critical and high-severity issues require immediate attention. "
            "Verify these are being properly fixed, not just acknowledged."
        )
    
    if acceptance_criteria_failures:
        recommendations.append(
            f"Acceptance criteria failures detected ({len(acceptance_criteria_failures)}). "
            "Review each criterion and ensure implementation matches requirements."
        )
    
    if security_issues:
        recommendations.append(
            "Security issues require immediate escalation. "
            "Do not proceed with implementation until resolved."
        )
    
    # Check for repeated same-issue
    signatures = {normalize_finding(f) for f in unresolved_findings}
    if len(signatures) < len(unresolved_findings):
        recommendations.append(
            "Some issues are repeated across reviews. Verify fixes are actually applied, "
            "not just claimed as resolved."
        )
    
    if not recommendations:
        recommendations.append(
            "Review all findings and determine appropriate action. "
            "Consider whether additional implementation or clarification is needed."
        )
    
    return recommendations


def track_review_attempt(
    review_request_id: str,
    status: str,
    findings: List[Dict[str, Any]]
) -> None:
    """
    Track a review attempt in the actions log.
    
    Args:
        review_request_id: The review request ID
        status: Review status (approved, requires_changes, rejected, blocked)
        findings: Findings from this review attempt
    """
    record_action("review_attempt", {
        "review_request_id": review_request_id,
        "status": status,
        "findings_count": len(findings),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


def get_unresolved_findings(
    previous_reviews: List[Dict[str, Any]],
    current_findings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Get list of unresolved findings from previous reviews.
    
    Args:
        previous_reviews: Previous review results
        current_findings: Current review findings (may have resolved some issues)
    
    Returns:
        Findings that still exist in current findings
    """
    # Build signatures of all findings ever seen
    signatures_seen = set()
    for attempt in previous_reviews:
        for finding in attempt.get("findings", []):
            signature = normalize_finding(finding)
            signatures_seen.add(signature)
    
    # Current findings that have NOT been resolved (still in current findings)
    unresolved = []
    for finding in current_findings:
        signature = normalize_finding(finding)
        if signature not in signatures_seen:
            # This is a new finding
            signatures_seen.add(signature)
            unresolved.append(finding)
    
    return unresolved
