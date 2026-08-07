#!/usr/bin/env python3
"""
UI Validation History Manager for Sanskriti AI Studio.

This module provides execution history storage and trend analysis
capabilities for UI validation results.

Version: 1.0
Last Updated: 2026-08-07
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# =============================================================================
# VALIDATION HISTORY STORAGE (Phase 7)
# =============================================================================

HISTORY_DIR = "ai_agents/state/validation_history"
HISTORY_FILE = os.path.join(HISTORY_DIR, "validation_history.jsonl")
SUMMARY_FILE = os.path.join(HISTORY_DIR, "validation_summary.json")


def ensure_history_dir() -> None:
    """Ensure history directory exists."""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR, exist_ok=True)


# =============================================================================
# HISTORY ENTRY SCHEMA (Phase 7)
# =============================================================================

class ValidationHistoryEntry:
    """
    Represents a single validation execution.
    
    Supports:
    - Pass Rate calculation
    - Failure Rate calculation
    - Historical Reports retrieval
    - Trend Analysis
    """
    
    def __init__(
        self,
        validation_id: str,
        milestone_id: str,
        task_id: str,
        page_name: str,
        status: str,  # "PASS", "FAIL"
        score: float,  # 0-100
        satisfied_rules: Optional[List[Dict[str, Any]]] = None,
        failed_rules: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
    ):
        """
        Initialize a validation history entry.
        
        Args:
            validation_id: Unique identifier for this validation run
            milestone_id: Milestone being validated
            task_id: Task identifier within the milestone
            page_name: Page name from expected UI model
            status: PASS or FAIL
            score: Validation score (0-100)
            satisfied_rules: Rules that passed
            failed_rules: Rules that failed
            warnings: Warnings detected
            recommendations: Actionable recommendations
        """
        self.validation_id = validation_id
        self.milestone_id = milestone_id
        self.task_id = task_id
        self.page_name = page_name
        self.status = status
        self.score = score
        self.satisfied_rules = satisfied_rules or []
        self.failed_rules = failed_rules or []
        self.warnings = warnings or []
        self.recommendations = recommendations or []
    
    @classmethod
    def from_comparison_result(
        cls,
        validation_id: str,
        milestone_id: str,
        task_id: str,
        page_name: str,
        comparison_result: Dict[str, Any],
    ) -> "ValidationHistoryEntry":
        """
        Create a history entry from a comparison result.
        
        Args:
            validation_id: Unique identifier
            milestone_id: Milestone ID
            task_id: Task ID
            page_name: Page name
            comparison_result: Result from ComparisonEngine
        
        Returns:
            ValidationHistoryEntry
        """
        # Calculate score based on issues found
        error_count = comparison_result.get("failure_count", 0)
        warning_count = comparison_result.get("warning_count", 0)
        
        # Score calculation: start at 100, deduct points for each issue
        base_score = 100.0
        deduction_per_error = 20.0
        deduction_per_warning = 5.0
        
        score = max(0.0, min(100.0, base_score - (error_count * deduction_per_error) - (warning_count * deduction_per_warning)))
        
        # Build satisfied rules list
        satisfied_rules = [
            {"id": "PASS", "description": "Component present"}
            for comp in comparison_result.get("missing_components", [])
            if False  # Filtered by comparison logic
        ]
        
        # Build failed rules list
        failed_rules = []
        for finding in comparison_result.get("missing_components", []):
            if finding.get("severity") == "ERROR":
                failed_rules.append({
                    "id": f"MISSING-{finding.get('expected_type', 'unknown')}",
                    "description": finding.get("description", ""),
                    "severity": finding.get("severity"),
                })
        
        for finding in comparison_result.get("label_mismatches", []):
            if finding.get("severity") == "ERROR":
                failed_rules.append({
                    "id": f"LABEL-{finding.get('component_type', 'unknown')}",
                    "description": finding.get("message", ""),
                    "severity": finding.get("severity"),
                })
        
        for finding in comparison_result.get("navigation_problems", []):
            if finding.get("severity") == "ERROR":
                failed_rules.append({
                    "id": f"NAV-{finding.get('problem_type', 'unknown')}",
                    "description": finding.get("expected", ""),
                    "severity": finding.get("severity"),
                })
        
        entry = cls(
            validation_id=validation_id,
            milestone_id=milestone_id,
            task_id=task_id,
            page_name=page_name,
            status="PASS" if comparison_result.get("is_pass", False) else "FAIL",
            score=score,
            satisfied_rules=satisfied_rules,
            failed_rules=failed_rules,
            warnings=comparison_result.get("accessibility_warnings", []),
            recommendations=_generate_recommendations(comparison_result),
        )
        
        return entry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "validation_id": self.validation_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "page_name": self.page_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": self.status,
            "score": self.score,
            "satisfied_rules": self.satisfied_rules,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }
    
    def to_json(self) -> str:
        """Convert entry to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


# =============================================================================
# UTILITY FUNCTIONS - Recommendation Generation (Phase 5)
# =============================================================================

def _generate_recommendations(comparison_result: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations from comparison result."""
    recommendations = []
    
    for finding in comparison_result.get("missing_components", []):
        comp_type = finding.get("expected_type", "unknown")
        if "button" in comp_type.lower():
            recommendations.append(f"Add the missing button component: {comp_type}")
        elif "navigation" in comp_type.lower():
            recommendations.append(f"Implement navigation structure: {comp_type}")
    
    for finding in comparison_result.get("label_mismatches", []):
        recommendations.append(f"Correct label mismatch on {finding.get('component_type')}: expected '{finding.get('expected')}', found '{finding.get('actual')}'")
    
    for finding in comparison_result.get("navigation_problems", []):
        if finding.get("problem_type") == "missing_navigation":
            recommendations.append(f"Add navigation with items: {finding.get('expected')}")
        elif finding.get("problem_type") == "missing_breadcrumb":
            recommendations.append("Add breadcrumb navigation for better user orientation")
    
    for warning in comparison_result.get("accessibility_warnings", []):
        recommendations.append(warning.get("message", ""))
    
    return recommendations


# =============================================================================
# HISTORY MANAGER (Phase 7)
# =============================================================================

class ValidationHistoryManager:
    """
    Manages UI validation history with pass/fail tracking and trend analysis.
    
    Supports:
    - Pass Rate calculation
    - Failure Rate calculation  
    - Historical Reports retrieval
    - Trend Analysis
    """
    
    def __init__(self):
        """Initialize the history manager."""
        ensure_history_dir()
    
    def append_entry(self, entry: ValidationHistoryEntry) -> Optional[ValidationHistoryEntry]:
        """Append a validation entry to the history file."""
        json_str = entry.to_json()
        
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json_str + "\n")
    
    def append_entry_dict(self, data: Dict[str, Any]) -> None:
        """Append a validation entry from dictionary to the history file."""
        json_str = json.dumps(data, indent=2, default=str)
        
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json_str + "\n")
    
    def get_entries(self, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all history entries, optionally filtered by milestone."""
        entries = []
        
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry_dict = json.loads(line)
                        
                        if milestone_id is None or entry_dict.get("milestone_id") == milestone_id:
                            entries.append(entry_dict)
                    except json.JSONDecodeError:
                        continue
        
        return entries
    
    def get_entries_by_page(self, page_name: str) -> List[Dict[str, Any]]:
        """Get all history entries for a specific page."""
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry_dict = json.loads(line)
                        if entry_dict.get("page_name") == page_name:
                            return [entry_dict]
                    except json.JSONDecodeError:
                        continue
        
        return []
    
    def get_latest_entry(self) -> Optional[Dict[str, Any]]:
        """Get the most recent validation entry."""
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        # Get the last non-empty line
        for line in reversed(lines):
            if line.strip():
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def calculate_pass_rate(self) -> Dict[str, Any]:
        """Calculate overall pass rate across all validations."""
        entries = self.get_entries()
        
        if not entries:
            return {
                "total_validations": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
            }
        
        passed = sum(1 for e in entries if e.get("status") == "PASS")
        failed = sum(1 for e in entries if e.get("status") == "FAIL")
        total = len(entries)
        
        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
        }
    
    def calculate_failure_rate(self) -> Dict[str, Any]:
        """Calculate overall failure rate across all validations."""
        stats = self.calculate_pass_rate()
        
        return {
            "total_validations": stats["total_validations"],
            "failed": stats["failed"],
            "failure_rate": (stats["failed"] / stats["total_validations"] * 100) if stats["total_validations"] > 0 else 0.0,
        }
    
    def get_trend_analysis(self, window: int = 10) -> Dict[str, Any]:
        """
        Analyze trends over a specified window of recent validations.
        
        Args:
            window: Number of recent entries to analyze
        
        Returns:
            Trend analysis data including pass rate trajectory
        """
        entries = self.get_entries()
        
        if len(entries) < window:
            return {
                "window_size": len(entries),
                "message": "Insufficient history for trend analysis",
                "trend": "unknown",
                "direction": None,
            }
        
        # Get last N entries
        recent_entries = entries[-window:]
        
        # Calculate rolling pass rates
        rolling_rates = []
        window_pass_count = 0
        window_total = 0
        
        for entry in reversed(recent_entries):
            status = entry.get("status", "")
            score = entry.get("score", 0)
            
            if status == "PASS":
                window_pass_count += 1
            elif status == "FAIL":
                pass_count = len(entry.get("satisfied_rules", []))
                total_count = len(entry.get("failed_rules", [])) + len(entry.get("satisfied_rules", []))
                score_percent = (pass_count / total_count * 100) if total_count > 0 else 0
                window_pass_count += (score_percent / 100)
            
            window_total += 1
            
            current_rate = (window_pass_count / window_total * 100) if window_total > 0 else 0
            rolling_rates.insert(0, current_rate)
        
        # Calculate trend direction
        if len(rolling_rates) >= 3:
            first_third_avg = sum(rolling_rates[:len(rolling_rates)//3]) / (len(rolling_rates)//3) if len(rolling_rates)//3 > 0 else 0
            last_third_avg = sum(rolling_rates[-len(rolling_rates)//3:]) / (len(rolling_rates)//3) if len(rolling_rates)//3 > 0 else 0
            
            if last_third_avg > first_third_avg + 5:
                direction = "improving"
            elif last_third_avg < first_third_avg - 5:
                direction = "degrading"
            else:
                direction = "stable"
        else:
            direction = "insufficient_data"
        
        return {
            "window_size": window,
            "current_pass_rate": sum(rolling_rates) / len(rolling_rates) if rolling_rates else 0,
            "trend": direction,
            "direction": direction,
            "recent_rates": rolling_rates[-5:],
        }
    
    def save_summary(self) -> None:
        """Save current statistics to summary file."""
        stats = {
            "pass_rate_stats": self.calculate_pass_rate(),
            "failure_rate_stats": self.calculate_failure_rate(),
            "trend_analysis": self.get_trend_analysis(window=10),
            "total_entries": len(self.get_entries()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, default=str)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def append_validation_entry(
    validation_id: str,
    milestone_id: str,
    task_id: str,
    page_name: str,
    comparison_result: Dict[str, Any],
) -> Optional[ValidationHistoryEntry]:
    """
    Factory function to append a validation entry.
    
    Args:
        validation_id: Unique identifier
        milestone_id: Milestone ID
        task_id: Task ID
        page_name: Page name
        comparison_result: Result from ComparisonEngine
    
    Returns:
        The created ValidationHistoryEntry
    """
    history_manager = ValidationHistoryManager()
    
    entry = ValidationHistoryEntry.from_comparison_result(
        validation_id=validation_id,
        milestone_id=milestone_id,
        task_id=task_id,
        page_name=page_name,
        comparison_result=comparison_result,
    )
    
    history_manager.append_entry(entry)
    
    return entry


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ValidationHistoryEntry",
    "ValidationHistoryManager",
    "append_validation_entry",
    "HISTORY_DIR",
    "HISTORY_FILE",
    "SUMMARY_FILE",
]
