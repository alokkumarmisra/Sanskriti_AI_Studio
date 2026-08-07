#!/usr/bin/env python3
"""
UI Validation Engine for Sanskriti AI Studio.

This module provides the complete UI Validation Engine that:
- Loads milestone acceptance criteria (Phase 1)
- Loads expected UI definitions (Phase 3)
- Loads Vision Analysis report (reusing existing schema)
- Compares expected vs actual (Phase 4)
- Produces validation results (Phase 5)

Version: 1.0
Last Updated: 2026-08-07
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# VALIDATION REPORT SCHEMA - Phase 5 (Phase 6 in original spec)
# =============================================================================

class ValidationReport:
    """
    Structured validation report.
    
    Generates structured reports including:
    - Validation ID
    - Milestone ID
    - Task ID
    - Page Name
    - Pass / Fail
    - Validation Score
    - Satisfied Rules
    - Failed Rules
    - Warnings
    - Recommendations
    """
    
    def __init__(
        self,
        validation_id: str,
        milestone_id: str,
        task_id: str,
        page_name: str,
        status: str,  # "PASS" or "FAIL"
        score: float,  # 0-100
        satisfied_rules: Optional[List[Dict[str, Any]]] = None,
        failed_rules: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[Dict[str, Any]]] = None,
        recommendations: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
    ):
        """
        Initialize a validation report.
        
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
            timestamp: Report timestamp
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
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    
    @classmethod
    def from_comparison_result(
        cls,
        validation_id: str,
        milestone_id: str,
        task_id: str,
        page_name: str,
        comparison_result: Dict[str, Any],
    ) -> "ValidationReport":
        """
        Create a validation report from comparison result.
        
        Args:
            validation_id: Unique identifier
            milestone_id: Milestone ID
            task_id: Task ID
            page_name: Page name
            comparison_result: Result from ComparisonEngine
        
        Returns:
            ValidationReport
        """
        # Calculate score based on issues found
        error_count = comparison_result.get("failure_count", 0)
        warning_count = comparison_result.get("warning_count", 0)
        
        # Score calculation: start at 100, deduct points for each issue
        base_score = 100.0
        deduction_per_error = 20.0
        deduction_per_warning = 5.0
        
        score = max(0.0, min(100.0, base_score - (error_count * deduction_per_error) - (warning_count * deduction_per_warning)))
        
        # Build satisfied rules list - components that were present
        satisfied_rules = []
        for comp_type in ["heading", "button", "navigation", "form", "input"]:
            found = any(c.get("type") == comp_type for c in comparison_result.get("unexpected_components", []))  # If not missing/unexpected, it's satisfied
            if not found:
                satisfied_rules.append({
                    "id": f"COMP-{comp_type.upper()}",
                    "description": f"Component type '{comp_type}' was correctly present",
                    "severity": "INFO",
                })
        
        # Build failed rules list from comparison result
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
        
        # Generate recommendations
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
        
        # Include accessibility warnings as recommendations
        for warning in comparison_result.get("accessibility_warnings", []):
            recommendations.append(warning.get("message", ""))
        
        report = cls(
            validation_id=validation_id,
            milestone_id=milestone_id,
            task_id=task_id,
            page_name=page_name,
            status="PASS" if comparison_result.get("is_pass", False) else "FAIL",
            score=score,
            satisfied_rules=satisfied_rules,
            failed_rules=failed_rules,
            warnings=comparison_result.get("accessibility_warnings", []),
            recommendations=recommendations,
        )
        
        return report
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "validation_id": self.validation_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "page_name": self.page_name,
            "timestamp": self.timestamp,
            "status": self.status,
            "score": self.score,
            "satisfied_rules": self.satisfied_rules,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }
    
    def to_json(self) -> str:
        """Convert report to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def is_passed(self) -> bool:
        """Check if validation passed (no ERROR-level issues)."""
        return self.status == "PASS"


# =============================================================================
# MAIN VALIDATION ENGINE - Phase 1, 3, 4 (Core of the specification)
# =============================================================================

from ai_agents.scripts.comparison_engine import ComparisonEngine
from ai_agents.scripts.validation_history import ValidationHistoryManager, ValidationHistoryEntry


class UIValidationEngine:
    """
    Main UI Validation Engine.
    
    The Validation Engine must determine whether the user interface satisfies 
    the milestone's acceptance criteria.
    
    Responsibilities:
    - Load milestone acceptance criteria (Phase 1)
    - Load expected UI definitions (Phase 3)
    - Load Vision Analysis report (reuses existing schema)
    - Compare expected vs actual (Phase 4)
    - Produce validation results (Phase 5)
    
    Supports validation for:
    - Required pages
    - Navigation
    - Buttons
    - Forms
    - Tables
    - Inputs
    - Labels
    - Headings
    - Layout
    - Visibility
    - Responsiveness
    - Error messages
    - Loading states
    - Empty states
    """
    
    def __init__(self) -> None:
        """Initialize the validation engine."""
        self.comparison_engine: ComparisonEngine = ComparisonEngine()
        self.history_manager: ValidationHistoryManager = ValidationHistoryManager()
    
    def validate(
        self,
        milestone_id: str,
        task_id: str,
        page_name: str,
        expected_ui_model: Dict[str, Any],
        vision_analysis_report: Dict[str, Any],
        url: Optional[str] = None,
    ) -> Tuple[ValidationReport, ValidationHistoryEntry]:
        """
        Perform validation against milestone acceptance criteria.
        
        This method:
        1. Loads expected UI definitions
        2. Loads Vision Analysis report (already structured)
        3. Compares expected vs actual
        4. Produces validation results
        
        Args:
            milestone_id: Milestone identifier
            task_id: Task identifier within the milestone
            page_name: Page name from expected UI model
            expected_ui_model: Expected UI model (from ExpectedUIModel.to_dict())
            vision_analysis_report: Vision Analysis report (dict from VisionAnalysisReport.to_dict())
            url: Optional URL for context
        
        Returns:
            Tuple of (ValidationReport, ValidationHistoryEntry)
        """
        # Generate validation ID - use parameter milestone_id, not self.milestone_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        validation_id = f"VAL-{milestone_id.replace('.', '_')}_{task_id[:8]}_{timestamp}"
        
        # Ensure URL is provided
        url = url or ""
        
        # Step 1: Load milestone acceptance criteria (Phase 1)
        # The expected_ui_model already contains acceptance criteria
        
        # Step 2: Load Vision Analysis report (already done by pipeline)
        # vision_analysis_report is the structured output from VisionAnalysisReport.to_dict()
        
        # Step 3: Compare expected vs actual (Phase 4)
        comparison_result = self.comparison_engine.compare(
            expected_model=expected_ui_model,
            vision_report=vision_analysis_report,
            url=url,
        )
        
        # Step 4: Generate validation report (Phase 5)
        validation_report = ValidationReport.from_comparison_result(
            validation_id=validation_id,
            milestone_id=milestone_id,
            task_id=task_id,
            page_name=page_name,
            comparison_result=comparison_result.to_dict(),
        )
        
        # Step 5: Store in history (Phase 7)
        history_entry = ValidationHistoryEntry.from_comparison_result(
            validation_id=validation_id,
            milestone_id=milestone_id,
            task_id=task_id,
            page_name=page_name,
            comparison_result=comparison_result.to_dict(),
        )
        
        self.history_manager.append_entry(history_entry)
        
        # Save summary periodically
        if validation_report.is_passed():
            self.history_manager.save_summary()
        
        return validation_report, history_entry
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get validation history summary with pass/fail rates."""
        return {
            "pass_rate": self.history_manager.calculate_pass_rate(),
            "failure_rate": self.history_manager.calculate_failure_rate(),
            "trend_analysis": self.history_manager.get_trend_analysis(window=10),
        }


# =============================================================================
# FACTORY FUNCTIONS (for Communication Bus integration)
# =============================================================================

def create_validation_engine() -> UIValidationEngine:
    """Factory function to create a configured Validation Engine."""
    return UIValidationEngine()


def close_validation_engine(engine: UIValidationEngine) -> None:
    """Close the validation engine (cleanup if needed)."""
    # No special cleanup needed


# =============================================================================
# STANDALONE VALIDATION FUNCTION
# =============================================================================

def run_ui_validation(
    milestone_id: str,
    task_id: str,
    page_name: str,
    expected_ui_model: Dict[str, Any],
    vision_analysis_report: Dict[str, Any],
    url: Optional[str] = None,
) -> Tuple[ValidationReport, ValidationHistoryEntry]:
    """
    Standalone function to run a UI validation without creating engine instance.
    
    Args:
        milestone_id: Milestone identifier
        task_id: Task identifier
        page_name: Page name
        expected_ui_model: Expected UI model dictionary
        vision_analysis_report: Vision Analysis report dictionary
        url: Optional URL for context
    
    Returns:
        Tuple of (ValidationReport, ValidationHistoryEntry)
    """
    engine = create_validation_engine()
    
    return engine.validate(
        milestone_id=milestone_id,
        task_id=task_id,
        page_name=page_name,
        expected_ui_model=expected_ui_model,
        vision_analysis_report=vision_analysis_report,
        url=url,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ValidationReport",
    "UIValidationEngine",
    "create_validation_engine",
    "close_validation_engine",
    "run_ui_validation",
]
