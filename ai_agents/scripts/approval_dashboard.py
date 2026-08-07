#!/usr/bin/env python3
"""
Human Approval Dashboard for Sanskriti AI Studio.

This dashboard provides a centralized interface for human reviewers to monitor,
inspect, approve, reject, or re-run AI-generated work before it is finalized.

It aggregates data from existing agent systems:
- Coding Agent (via coding_result.json/actions.jsonl)
- Testing Agent (via test_report.json)
- Reviewer Agent (via review_report.json)
- Validation Engine (via validation_history.json)
- Vision Agent (via vision_report.json if available)

ARCHITECTURE FLOW:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   State     │ →   │  Dashboard  │ →   │   Frontend  │
│  Files      │     │   CLI       │     │   UI        │
└─────────────┘     └─────────────┘     └─────────────┘

Key Principles:
1. Reuses existing agent data - no duplicate reporting systems
2. Reads from shared state files
3. Provides structured aggregation for frontend consumption
4. Supports manual approval workflow
5. Qwen 3.5 TEXT-ONLY compliance
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")


def utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON object from disk, returning None when unavailable/invalid."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {"value": data}
    except json.JSONDecodeError as exc:
        return {"_load_error": f"Invalid JSON in {path}: {exc}"}
    except OSError as exc:
        return {"_load_error": f"Could not read {path}: {exc}"}


def load_jsonl_file(path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file line by line."""
    if not os.path.exists(path):
        return []
    results = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        results.append(event)
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return results


def get_task_context() -> Dict[str, Any]:
    """Read current task context from shared state files."""
    candidates = [
        os.path.join(STATE_DIR, "task_plan.json"),
        os.path.join(STATE_DIR, "current_task.json"),
    ]
    for path in candidates:
        data = load_json_file(path)
        if data and not isinstance(data, dict):
            continue
        if not isinstance(data, dict):
            continue
        task_id = data.get("task_id", "")
        description = data.get("description", "")
        milestone = data.get("milestone", "")
        stage = data.get("stage", "")
        agent = data.get("agent", "")
        
        if task_id:
            return {
                "task_id": task_id,
                "description": description,
                "milestone": milestone,
                "stage": stage,
                "agent": agent,
            }
    
    # Fallback from actions.jsonl
    actions = load_jsonl_file(os.path.join(STATE_DIR, "actions.jsonl"))
    recent = actions[-5:] if len(actions) >= 5 else actions
    
    for action in recent:
        task_id = action.get("task_id", "")
        description = action.get("description", "")
        milestone = action.get("milestone", "")
        stage = action.get("stage", "")
        agent = action.get("agent", "")
        
        if task_id:
            return {
                "task_id": task_id,
                "description": description,
                "milestone": milestone,
                "stage": stage,
                "agent": agent,
            }
    
    return {
        "task_id": "manual-dashboard-view",
        "description": "Dashboard view with no active task",
        "milestone": "",
        "stage": "",
        "agent": "",
    }


def get_current_agent() -> Optional[str]:
    """Get the currently executing agent from actions.jsonl."""
    actions = load_jsonl_file(os.path.join(STATE_DIR, "actions.jsonl"))
    
    # Look for most recent agent action (excluding 'viewer' dashboard actions)
    for action in reversed(actions):
        agent_type = action.get("agent", "")
        if agent_type and agent_type != "viewer":
            return agent_type
    
    return None


def get_execution_time() -> int:
    """Get total execution time from task context or approximate."""
    task_context = get_task_context()
    
    # If we have a task_id, it's actively running
    if task_context.get("task_id", "").startswith("STEP-"):
        return 0  # Still running
    
    return 0


def get_retry_count(task_id: str) -> int:
    """Get retry count for a specific task from validation history."""
    validation_history = load_json_file(
        os.path.join(STATE_DIR, "validation_history.json")
    )
    
    if not validation_history:
        return 0
    
    retry_counts = validation_history.get("retry_counts", {})
    base_key = str(task_id)
    
    # Try exact match first
    if base_key in retry_counts:
        return retry_counts[base_key].get("retry_count", 0)
    
    # Try with different prefixes
    for key_prefix, data in retry_counts.items():
        if key_prefix.startswith(base_key):
            return data.get("retry_count", 0)
    
    return 0


def get_build_status() -> Dict[str, Any]:
    """Get build status from test report."""
    test_report = load_json_file(
        os.path.join(STATE_DIR, "test_report.json")
    )
    
    if not test_report:
        return {
            "status": "NOT_AVAILABLE",
            "message": "Test report not available",
            "compilation_errors": 0,
            "warnings": [],
            "latest_build_time": "",
        }
    
    # Analyze backend tests for build status
    backend = test_report.get("backend", {})
    lint = test_report.get("lint", {})
    build = test_report.get("build", {})
    
    errors = test_report.get("errors", [])
    
    # Get latest timestamp from all tests
    timestamps = []
    for test in test_report.get("tests", []):
        start = test.get("started_at", "")
        if start:
            timestamps.append(start)
    
    latest_build_time = max(timestamps) if timestamps else ""
    
    # Count compilation errors (exit_code != 0 with "error" in stderr)
    error_count = sum(
        1 for test in test_report.get("tests", [])
        if test.get("status") == "FAIL" and "error" in test.get("stderr", "").lower()
    )
    
    # Collect warnings (non-error failures)
    warning_messages = []
    for error in errors:
        msg = error.get("message", "")
        if "warning" in msg.lower():
            warning_messages.append(msg[:200])
    
    return {
        "status": backend.get("status") or lint.get("status") or build.get("status"),
        "compilation_errors": error_count,
        "warnings": warning_messages,
        "latest_build_time": latest_build_time,
    }


def get_test_results() -> Dict[str, Any]:
    """Get test results summary."""
    test_report = load_json_file(
        os.path.join(STATE_DIR, "test_report.json")
    )
    
    if not test_report:
        return {
            "unit_test_summary": "",
            "integration_tests": "",
            "browser_tests": "",
            "pass_percent": 0,
            "failed_tests": [],
            "message": "Test report not available",
        }
    
    # Analyze test results
    tests = test_report.get("tests", [])
    
    passed = sum(1 for t in tests if t.get("status") == "PASS")
    failed = [t for t in tests if t.get("status") == "FAIL"]
    total = len(tests)
    
    pass_percent = (passed / total * 100) if total > 0 else 0
    
    # Categorize tests
    backend_tests = [t for t in tests if t.get("category") == "backend"]
    lint_tests = [t for t in tests if t.get("category") == "lint"]
    build_tests = [t for t in tests if t.get("category") == "build"]
    
    return {
        "unit_test_summary": f"Unit Tests: {passed}/{total} passed ({pass_percent:.1f}%)",
        "integration_tests": ", ".join(t.get("name", "") for t in backend_tests) or "None",
        "browser_tests": "",  # Browser tests would come from vision/report files
        "pass_percent": pass_percent,
        "failed_tests": [
            {
                "name": e.get("test"),
                "category": e.get("category"),
                "message": e.get("message", ""),
            }
            for e in test_report.get("errors", [])
        ],
    }


def get_vision_results() -> Dict[str, Any]:
    """Get vision analysis results if available."""
    vision_path = os.path.join(STATE_DIR, "vision_report.json")
    
    if not os.path.exists(vision_path):
        return {
            "latest_screenshot": "",
            "vision_summary": "No vision report available",
            "detected_components": [],
            "visual_issues": [],
            "confidence_score": None,
            "message": "Vision Agent has not run yet",
        }
    
    try:
        with open(vision_path, "r", encoding="utf-8") as f:
            vision_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "latest_screenshot": "",
            "vision_summary": "Could not parse vision report",
            "detected_components": [],
            "visual_issues": [],
            "confidence_score": None,
            "message": "Vision Agent has not run yet",
        }
    
    summary = vision_data.get("summary", "")
    components = vision_data.get("components", [])
    issues = vision_data.get("issues", [])
    confidence = vision_data.get("confidence")
    screenshot = vision_data.get("screenshot_path", "")
    
    return {
        "latest_screenshot": screenshot,
        "vision_summary": summary[:500] if summary else "",  # Truncate for display
        "detected_components": components,
        "visual_issues": issues,
        "confidence_score": confidence,
        "message": f"Vision analysis completed at {vision_data.get('timestamp', '')}",
    }


def get_ui_validation() -> Dict[str, Any]:
    """Get UI validation results."""
    validation_history = load_json_file(
        os.path.join(STATE_DIR, "validation_history.json")
    )
    
    if not validation_history:
        return {
            "validation_score": None,
            "missing_components": [],
            "layout_issues": [],
            "accessibility_warnings": [],
            "pass_fail": "UNKNOWN",
            "message": "Validation history not available",
        }
    
    # Analyze validation history for UI validation
    successful = validation_history.get("successful_validations", [])
    failed = validation_history.get("failed_validations", [])
    
    # Check for frontend/validation related stages
    ui_stages = [s for s in successful + failed if "frontend" in s.get("stage", "").lower() or 
                  "ui" in s.get("stage", "").lower() or "layout" in s.get("stage", "").lower()]
    
    # Calculate validation score based on UI-related validations
    ui_passed = sum(1 for s in ui_stages if s.get("status") == "PASS")
    ui_failed = sum(1 for s in ui_stages if s.get("status") == "FAIL")
    
    # Get missing components from failed validations
    missing_components = []
    layout_issues = []
    accessibility_warnings = []
    
    for failure in failed:
        logs = failure.get("logs", [])
        error = failure.get("errors", [])
        msg = (error[0] if error else "")[:200] if error else ""
        
        if "component" in msg.lower() or "missing" in msg.lower():
            # Extract component info
            parts = msg.split(",")
            for part in parts:
                if ":" in part:
                    comp_type, desc = part.strip().split(":", 1)
                    missing_components.append({"type": comp_type.strip(), "description": desc.strip()})
        
        if "layout" in msg.lower():
            layout_issues.append(msg[:200])
        
        if "accessibility" in msg.lower():
            accessibility_warnings.append(msg[:200])
    
    total_ui = ui_passed + ui_failed
    validation_score = (ui_passed / total_ui * 100) if total_ui > 0 else None
    
    # Determine pass/fail
    if validation_score is not None and validation_score >= 95:
        pass_fail = "PASS"
    elif validation_score is not None and validation_score >= 70:
        pass_fail = "WARNING"
    else:
        pass_fail = "FAIL"
    
    return {
        "validation_score": validation_score,
        "missing_components": missing_components[:10],  # Limit to top 10
        "layout_issues": layout_issues[:5],  # Limit to top 5
        "accessibility_warnings": accessibility_warnings[:5],  # Limit to top 5
        "pass_fail": pass_fail,
        "message": f"UI Validation: {ui_passed} passed, {ui_failed} failed",
    }


def get_review_report() -> Dict[str, Any]:
    """Get reviewer agent report."""
    review_path = os.path.join(STATE_DIR, "review_report.json")
    
    if not os.path.exists(review_path):
        return {
            "reviewer_decision": "",
            "recommendations": [],
            "critical_issues": [],
            "warnings": [],
            "suggestions": [],
            "message": "No reviewer report available",
        }
    
    with open(review_path, "r", encoding="utf-8") as f:
        review_data = json.load(f)
    
    status = review_data.get("status", "")
    summary = review_data.get("summary", "")[:500]
    
    # Map reviewer statuses to decision
    decision_map = {
        "APPROVED": "approved",
        "APPROVED_WITH_WARNINGS": "approved_with_warnings",
        "REQUIRES_CHANGES": "requires_changes",
        "REJECTED": "rejected",
        "BLOCKED": "blocked",
    }
    
    reviewer_decision = decision_map.get(status, status)
    
    # Extract findings by severity
    critical_issues = []
    warnings = []
    suggestions = []
    
    for finding in review_data.get("findings", []):
        severity = finding.get("severity", "")
        problem = finding.get("problem", "")
        recommendation = finding.get("recommendation", "")
        
        if severity == "HIGH" or severity == "CRITICAL":
            critical_issues.append({
                "severity": severity,
                "category": finding.get("category"),
                "file": finding.get("file"),
                "line": finding.get("line"),
                "problem": problem[:500],
            })
        elif severity == "MEDIUM":
            warnings.append({
                "severity": severity,
                "category": finding.get("category"),
                "problem": problem[:500],
            })
        
        # Collect recommendations and suggestions
        if recommendation:
            if severity in ("HIGH", "CRITICAL"):
                critical_issues[-1]["recommendation"] = recommendation
            else:
                suggestions.append(recommendation)
    
    # Add summary as suggestion if not already populated
    if not suggestions and summary:
        suggestions.append(f"Review Summary: {summary}")
    
    return {
        "reviewer_decision": reviewer_decision,
        "recommendations": review_data.get("recommendations", []),
        "critical_issues": critical_issues[:10],  # Limit to top 10
        "warnings": warnings[:5],  # Limit to top 5
        "suggestions": suggestions[:5],  # Limit to top 5
        "message": f"Reviewer Status: {reviewer_decision} - {summary}",
    }


def get_pending_approvals() -> List[Dict[str, Any]]:
    """Get list of pending approvals."""
    pending_path = os.path.join(STATE_DIR, "pending_approvals.json")
    
    if not os.path.exists(pending_path):
        return []
    
    with open(pending_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, dict) and data.get("approvals"):
        return data["approvals"]
    
    if isinstance(data, list):
        return data
    
    return []


def get_execution_history() -> Dict[str, Any]:
    """Get execution history from actions.jsonl."""
    actions_path = os.path.join(STATE_DIR, "actions.jsonl")
    actions = load_jsonl_file(actions_path)
    
    # Group by task_id
    tasks: Dict[str, List[Dict[str, Any]]] = {}
    
    for action in actions[-100:]:  # Last 100 actions
        task_id = action.get("task_id", "unknown")
        if task_id not in tasks:
            tasks[task_id] = []
        tasks[task_id].append(action)
    
    history = []
    for task_id, task_actions in tasks.items():
        latest = task_actions[-1]
        agent = latest.get("agent", "")
        status = latest.get("status", "")
        description = latest.get("description", "")
        timestamp = latest.get("timestamp", "")
        
        history.append({
            "task_id": task_id,
            "agent": agent,
            "status": status,
            "description": description[:200],
            "timestamp": timestamp,
        })
    
    # Sort by timestamp descending
    history.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "history": history[-20:],  # Last 20 entries
        "total_runs": len(tasks),
    }


def build_dashboard_data() -> Dict[str, Any]:
    """Build the complete dashboard data structure for frontend consumption."""
    task_context = get_task_context()
    
    return {
        "dashboard_metadata": {
            "generated_at": utc_now(),
            "version": "1.0",
            "qwen_3_5_compliant": True,
        },
        
        # PHASE 1 — DASHBOARD (Current Execution Status)
        "phase1_dashboard": {
            "current_milestone": task_context.get("milestone", ""),
            "current_task": task_context.get("description", ""),
            "execution_status": "RUNNING" if task_context.get("task_id", "").startswith("STEP-") else "IDLE",
            "current_agent": get_current_agent(),
            "current_stage": task_context.get("stage", ""),
            "execution_time_seconds": get_execution_time(),
            "retry_count": get_retry_count(task_context.get("task_id", "")),
        },
        
        # PHASE 2 — BUILD STATUS
        "phase2_build": get_build_status(),
        
        # PHASE 3 — TEST RESULTS
        "phase3_tests": get_test_results(),
        
        # PHASE 4 — VISION RESULTS
        "phase4_vision": get_vision_results(),
        
        # PHASE 5 — UI VALIDATION
        "phase5_validation": get_ui_validation(),
        
        # PHASE 6 — REVIEW REPORT
        "phase6_review": get_review_report(),
        
        # PHASE 7 — USER ACTIONS (available operations)
        "phase7_actions": {
            "approve_available": True,
            "reject_available": True,
            "rerun_current_step_available": True,
            "restart_self_healing_available": False,
            "continue_to_next_milestone_available": bool(task_context.get("milestone")),
            "export_report_available": True,
            "view_history_available": True,
        },
        
        # PHASE 8 — HISTORY
        "phase8_history": get_execution_history(),
        
        # PHASE 9 — DOCUMENTATION (updated files)
        "phase9_documentation": {
            "last_updated": None,  # Would need to scan docs for timestamp
            "requires_review": task_context.get("description", "") != "",
        },
    }


def display_dashboard_summary(data: Dict[str, Any]) -> str:
    """Display a human-readable summary of the dashboard data."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("HUMAN APPROVAL DASHBOARD - Sanskriti AI Studio")
    lines.append("=" * 80)
    lines.append("")
    
    # Metadata
    meta = data.get("dashboard_metadata", {})
    lines.append(f"Generated: {meta.get('generated_at', 'N/A')}")
    lines.append(f"Qwen 3.5 Compliant: {'Yes' if meta.get('qwen_3_5_compliant') else 'No'}")
    lines.append("")
    
    # PHASE 1 — DASHBOARD
    p1 = data.get("phase1_dashboard", {})
    lines.append("-" * 40)
    lines.append("PHASE 1: Current Execution Status")
    lines.append("-" * 40)
    lines.append(f"Milestone:      {p1.get('current_milestone', 'N/A') or 'None'}")
    lines.append(f"Task:           {p1.get('current_task', 'N/A') or 'No active task'}")
    lines.append(f"Status:         {p1.get('execution_status')}")
    lines.append(f"Agent:          {p1.get('current_agent') or 'None'}")
    lines.append(f"Stage:          {p1.get('current_stage', 'N/A') or 'N/A'}")
    lines.append(f"Execution Time: {p1.get('execution_time_seconds')}s")
    lines.append(f"Retry Count:    {p1.get('retry_count', 0)}")
    lines.append("")
    
    # PHASE 2 — BUILD STATUS
    p2 = data.get("phase2_build", {})
    lines.append("-" * 40)
    lines.append("PHASE 2: Build Status")
    lines.append("-" * 40)
    build_status = p2.get("status", "N/A")
    if build_status == "PASS":
        status_symbol = "✓"
    elif build_status == "FAIL":
        status_symbol = "✗"
    else:
        status_symbol = "?"
    
    lines.append(f"Build Status:   {status_symbol} {build_status}")
    lines.append(f"Errors:         {p2.get('compilation_errors', 0)}")
    lines.append(f"Warnings:       {len(p2.get('warnings', []))}")
    if p2.get("latest_build_time"):
        lines.append(f"Latest Build:   {p2['latest_build_time'][:30]}...")
    lines.append("")
    
    # PHASE 3 — TEST RESULTS
    p3 = data.get("phase3_tests", {})
    lines.append("-" * 40)
    lines.append("PHASE 3: Test Results")
    lines.append("-" * 40)
    lines.append(f"Unit Tests:     {p3.get('unit_test_summary', 'N/A')}")
    lines.append(f"Integration:    {p3.get('integration_tests', 'N/A')}")
    lines.append(f"Browser Tests:  {p3.get('browser_tests', 'N/A')}")
    pass_pct = p3.get("pass_percent", 0)
    failed_count = len(p3.get("failed_tests", []))
    if pass_pct is not None:
        status_symbol = "✓" if pass_pct >= 95 else "⚠" if pass_pct >= 70 else "✗"
    else:
        status_symbol = "?"
    lines.append(f"Pass %:         {status_symbol} {pass_pct:.1f}%" if pass_pct is not None else f"Pass %:         N/A")
    lines.append(f"Failed Tests:   {failed_count}")
    for error in p3.get("failed_tests", [])[:3]:
        lines.append(f"  - {error.get('name')}: {error.get('message', '')[:80]}")
    lines.append("")
    
    # PHASE 4 — VISION RESULTS
    p4 = data.get("phase4_vision", {})
    lines.append("-" * 40)
    lines.append("PHASE 4: Vision Results")
    lines.append("-" * 40)
    vision_msg = p4.get("message", "N/A")
    if vision_msg == "No vision report available":
        status_symbol = "?"
        lines.append(f"Status:         {status_symbol} {vision_msg}")
    elif vision_msg.startswith("Vision analysis"):
        status_symbol = "✓"
        lines.append(f"Status:         {status_symbol} Analysis completed")
    else:
        status_symbol = "?"
        lines.append(f"Status:         {status_symbol} {vision_msg[:100]}")
    
    components = p4.get("detected_components", [])
    if components:
        lines.append(f"Components:     {len(components)} detected")
    
    issues = p4.get("visual_issues", [])
    if issues:
        lines.append(f"Issues:         {len(issues)} visual issues found")
    
    confidence = p4.get("confidence_score")
    if confidence:
        lines.append(f"Confidence:     {confidence}")
    
    screenshot = p4.get("latest_screenshot", "")
    if screenshot:
        lines.append(f"Screenshot:     Available: {screenshot}")
    lines.append("")
    
    # PHASE 5 — UI VALIDATION
    p5 = data.get("phase5_validation", {})
    lines.append("-" * 40)
    lines.append("PHASE 5: UI Validation")
    lines.append("-" * 40)
    validation_score = p5.get("validation_score")
    if validation_score is not None:
        status_symbol = "✓" if validation_score >= 95 else "⚠" if validation_score >= 70 else "✗"
        lines.append(f"Validation:     {status_symbol} {validation_score:.1f}%")
    else:
        status_symbol = "?"
        lines.append(f"Validation:     {status_symbol} N/A")
    
    pass_fail = p5.get("pass_fail", "")
    if pass_fail != "UNKNOWN":
        lines.append(f"Result:         {pass_fail}")
    
    missing = len(p5.get("missing_components", []))
    layout_issues = len(p5.get("layout_issues", []))
    accessibility_warnings = len(p5.get("accessibility_warnings", []))
    lines.append(f"Missing Components: {missing}")
    lines.append(f"Layout Issues:     {layout_issues}")
    lines.append(f"A11y Warnings:     {accessibility_warnings}")
    lines.append("")
    
    # PHASE 6 — REVIEW REPORT
    p6 = data.get("phase6_review", {})
    lines.append("-" * 40)
    lines.append("PHASE 6: Review Report")
    lines.append("-" * 40)
    review_decision = p6.get("reviewer_decision", "")
    if review_decision:
        status_symbol = "✓" if review_decision == "approved" else "⚠" if review_decision in ("approved_with_warnings", "requires_changes") else "✗" if review_decision == "rejected" else "?"
        lines.append(f"Decision:       {status_symbol} {review_decision.upper()}")
    else:
        status_symbol = "?"
        lines.append(f"Decision:       {status_symbol} N/A")
    
    critical_issues = p6.get("critical_issues", [])
    warnings = p6.get("warnings", [])
    if critical_issues:
        lines.append(f"Critical Issues:{len(critical_issues)}")
    if warnings:
        lines.append(f"Warnings:       {len(warnings)}")
    
    suggestions = p6.get("suggestions", [])
    if suggestions:
        lines.append(f"Suggestions:    {len(suggestions)} items")
        for i, sug in enumerate(suggestions[:3], 1):
            lines.append(f"  {i}. {sug[:80]}")
    lines.append("")
    
    # PHASE 7 — USER ACTIONS
    p7 = data.get("phase7_actions", {})
    lines.append("-" * 40)
    lines.append("PHASE 7: User Actions")
    lines.append("-" * 40)
    actions = []
    if p7.get("approve_available"):
        actions.append("✓ Approve")
    if p7.get("reject_available"):
        actions.append("✗ Reject")
    if p7.get("rerun_current_step_available"):
        actions.append("↺ Re-run Current Step")
    if p7.get("restart_self_healing_available"):
        actions.append("🔄 Restart Self-Healing")
    if p7.get("continue_to_next_milestone_available"):
        actions.append("→ Continue to Next Milestone")
    if p7.get("export_report_available"):
        actions.append("📄 Export Report")
    if p7.get("view_history_available"):
        actions.append("📜 View History")
    
    lines.append(", ".join(actions) if actions else "No actions available")
    lines.append("")
    
    # PHASE 8 — HISTORY
    p8 = data.get("phase8_history", {})
    lines.append("-" * 40)
    lines.append("PHASE 8: Execution History (Recent)")
    lines.append("-" * 40)
    total_runs = p8.get("total_runs", 0)
    lines.append(f"Total Runs:     {total_runs}")
    for entry in p8.get("history", [])[-5:]:
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("+00:00", "+00:00"))
                lines.append(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} - {entry.get('agent')}: {entry.get('status')}")
            except:
                pass
    
    lines.append("")
    
    # PHASE 9 — DOCUMENTATION
    p9 = data.get("phase9_documentation", {})
    lines.append("-" * 40)
    lines.append("PHASE 9: Documentation")
    lines.append("-" * 40)
    lines.append(f"Requires Review:{p9.get('requires_review', False)}")
    if p9.get("last_updated"):
        lines.append(f"Last Updated:   {p9['last_updated']}")
    lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def main() -> None:
    """CLI entry point for the Approval Dashboard."""
    print("=" * 60)
    print("HUMAN APPROVAL DASHBOARD - Sanskriti AI Studio")
    print("=" * 60)
    print("[INFO] This dashboard aggregates data from all existing agents.")
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - no images sent to any models.")
    print("")
    
    data = build_dashboard_data()
    summary = display_dashboard_summary(data)
    
    print(summary)
    print("")
    print("=" * 60)
    print("USER ACTIONS")
    print("=" * 60)
    print("1. Export this report to JSON: approval_dashboard.py --export")
    print("2. Run as a live dashboard server: approval_dashboard.py --server")
    print("3. Generate report for a specific milestone: approval_dashboard.py --milestone STEP-XXXXXX")
    print("")


if __name__ == "__main__":
    main()
