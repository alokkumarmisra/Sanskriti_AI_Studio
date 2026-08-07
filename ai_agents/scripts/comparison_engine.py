#!/usr/bin/env python3
"""
UI Comparison Engine for Sanskriti AI Studio.

This module compares expected UI models against actual Vision Analysis results,
identifying discrepancies and producing structured validation findings.

Version: 1.0
Last Updated: 2026-08-07
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# COMPARISON ENGINE - Phase 4 (Phase 3 in original spec)
# =============================================================================

class ComparisonEngine:
    """
    Compares expected UI models against actual Vision Analysis results.
    
    This engine identifies:
    - Missing Components (expected but not found)
    - Unexpected Components (found but not expected)
    - Incorrect Labels (text mismatches)
    - Layout Problems (structural issues)
    - Accessibility Warnings (missing ARIA, etc.)
    - Navigation Problems (broken links, missing nav elements)
    """
    
    def __init__(self):
        """Initialize the comparison engine."""
        self.missing_components: List[Dict[str, Any]] = []
        self.unexpected_components: List[Dict[str, Any]] = []
        self.label_mismatches: List[Dict[str, Any]] = []
        self.layout_problems: List[Dict[str, Any]] = []
        self.accessibility_warnings: List[Dict[str, Any]] = []
        self.navigation_problems: List[Dict[str, Any]] = []
    
    def compare(
        self,
        expected_model: Dict[str, Any],
        vision_report: Dict[str, Any],
        url: str,
    ) -> "ComparisonResult":
        """
        Compare expected UI model against Vision Analysis result.
        
        Args:
            expected_model: Expected UI model (from ExpectedUIModel or dict)
            vision_report: Vision Analysis report (dict from VisionAnalysisReport.to_dict())
            url: Page URL for context
        
        Returns:
            ComparisonResult with all findings
        """
        # Reset findings for new comparison
        self.missing_components = []
        self.unexpected_components = []
        self.label_mismatches = []
        self.layout_problems = []
        self.accessibility_warnings = []
        self.navigation_problems = []
        
        # Extract detected components from vision report
        detected = vision_report.get("detected_components", [])
        ocr_text = vision_report.get("ocr_text", "")
        visual_issues = vision_report.get("visual_issues", [])
        warnings = vision_report.get("warnings", [])
        
        # Build a map of expected required components for quick lookup
        expected_required = {
            comp["type"]: comp for comp in expected_model.get("required_components", [])
        }
        expected_optional = {
            comp["type"]: comp for comp in expected_model.get("optional_components", [])
        }
        
        # Check for missing required components
        self._check_missing_required(detected, expected_required, ocr_text)
        
        # Check for unexpected components
        self._check_unexpected_components(detected, expected_required, expected_optional)
        
        # Check labels on detected components
        self._check_labels(detected, expected_model)
        
        # Check layout against rules
        self._check_layout_rules(expected_model, visual_issues)
        
        # Check accessibility
        self._check_accessibility(detected, ocr_text)
        
        # Check navigation
        self._check_navigation(expected_model, detected)
        
        return ComparisonResult(
            url=url,
            missing=self.missing_components,
            unexpected=self.unexpected_components,
            label_mismatches=self.label_mismatches,
            layout_problems=self.layout_problems,
            accessibility_warnings=self.accessibility_warnings,
            navigation_problems=self.navigation_problems,
        )
    
    def _check_missing_required(
        self,
        detected: List[Dict[str, Any]],
        expected_required: Dict[str, Dict[str, Any]],
        ocr_text: str,
    ):
        """Check for missing required components."""
        found_types = {comp.get("type") for comp in detected}
        
        for comp_type, expected_comp in expected_required.items():
            if comp_type not in found_types:
                self.missing_components.append({
                    "type": "missing_component",
                    "expected_type": comp_type,
                    "description": f"Required component of type '{comp_type}' was not detected.",
                    "severity": "ERROR",
                })
            else:
                # Component exists, check for specific text/label mismatches
                actual_comp = next((c for c in detected if c.get("type") == comp_type), None)
                expected_text = expected_comp.get("text", "") or expected_comp.get("title", "")
                
                if expected_text and actual_comp:
                    # Extract text from detected component (simplified heuristic)
                    actual_text = self._extract_component_text(actual_comp, detected, ocr_text)
                    
                    if expected_text.lower() != actual_text.lower():
                        self.label_mismatches.append({
                            "type": "label_mismatch",
                            "component_type": comp_type,
                            "expected": expected_text,
                            "actual": actual_text,
                            "severity": "WARNING",
                        })
    
    def _check_unexpected_components(
        self,
        detected: List[Dict[str, Any]],
        required: Dict[str, Dict[str, Any]],
        optional: Dict[str, Dict[str, Any]],
    ):
        """Check for components that exist but weren't expected."""
        expected_types = set(required.keys()) | set(optional.keys())
        found_types = {comp.get("type") for comp in detected}
        
        unexpected = found_types - expected_types
        
        for comp_type in unexpected:
            self.unexpected_components.append({
                "type": "unexpected_component",
                "component_type": comp_type,
                "severity": "INFO",
                "message": f"Component of type '{comp_type}' was detected but not defined in expected UI model.",
            })
    
    def _check_labels(
        self,
        detected: List[Dict[str, Any]],
        expected_model: Dict[str, Any],
    ):
        """Check that labels are present on interactive elements."""
        for comp in detected:
            comp_type = comp.get("type", "")
            
            # Check buttons have text
            if comp_type == "button" and not comp.get("text", "") and not comp.get("label", ""):
                self.label_mismatches.append({
                    "type": "missing_button_text",
                    "component_type": comp_type,
                    "severity": "ERROR",
                    "message": "Button element detected but has no text or label.",
                })
            
            # Check inputs have associated labels
            if comp_type in ["input", "text-input"]:
                if not self._has_label_for_input(comp, detected):
                    self.label_mismatches.append({
                        "type": "missing_input_label",
                        "component_type": comp_type,
                        "severity": "ERROR",
                        "message": "Input field detected without associated label.",
                    })
    
    def _check_layout_rules(self, expected_model: Dict[str, Any], visual_issues: List[Dict]):
        """Check layout rules compliance."""
        rules = expected_model.get("layout_rules", {})
        
        # Check for alignment issues
        if "alignment" in rules and "misaligned" in str(visual_issues).lower():
            self.layout_problems.append({
                "type": "layout_problem",
                "rule_id": "LAYOUT-001",
                "rule_name": "Alignment",
                "expected": rules["alignment"],
                "actual": "misaligned elements detected",
                "severity": "WARNING",
            })
        
        # Check for overflow issues
        if any("overflow" in str(issue).lower() for issue in visual_issues):
            self.layout_problems.append({
                "type": "layout_problem",
                "rule_id": "LAYOUT-002",
                "rule_name": "Overflow Prevention",
                "expected": "no overflow",
                "actual": "overflow detected in layout",
                "severity": "ERROR",
            })
    
    def _check_accessibility(self, detected: List[Dict[str, Any]], ocr_text: str):
        """Check basic accessibility compliance."""
        # Check for missing ARIA labels on interactive elements
        button_count = sum(1 for c in detected if c.get("type") == "button")
        link_count = sum(1 for c in detected if c.get("type") == "link")
        
        # Assume all buttons/links need ARIA labels (simplified check)
        interactive_elements = button_count + link_count
        
        if interactive_elements > 0:
            # If ocr_text doesn't contain common accessibility text patterns
            if not any(pattern in ocr_text.lower() for pattern in ["aria", "label", "accessible"]):
                self.accessibility_warnings.append({
                    "type": "accessibility_warning",
                    "category": "ARIA labels missing",
                    "severity": "INFO",
                    "message": f"Found {interactive_elements} interactive elements. Verify ARIA labels are present.",
                })
    
    def _check_navigation(self, expected_model: Dict[str, Any], detected: List[Dict[str, Any]]):
        """Check navigation requirements."""
        nav_rules = expected_model.get("navigation_rules", {})
        
        # Check for required navigation elements
        if nav_rules.get("menu_items"):
            menu_items = nav_rules["menu_items"]
            nav_elements = [c for c in detected if c.get("type") in ["navigation", "nav-item", "menu"]]
            
            if not nav_elements:
                self.navigation_problems.append({
                    "type": "navigation_problem",
                    "problem_type": "missing_navigation",
                    "severity": "ERROR",
                    "expected": f"Navigation with items: {', '.join(menu_items)}",
                })
        
        # Check for breadcrumb if required
        if nav_rules.get("breadcrumb") and not any(c.get("type") == "breadcrumb" for c in detected):
            self.navigation_problems.append({
                "type": "navigation_problem",
                "problem_type": "missing_breadcrumb",
                "severity": "WARNING",
                "message": "Breadcrumb navigation expected but not found.",
            })
        
        # Check for back link if required
        if nav_rules.get("back_link") and not any(c.get("type") == "link" and c.get("text", "").lower() in ["back", "<-"] for c in detected):
            self.navigation_problems.append({
                "type": "navigation_problem",
                "problem_type": "missing_back_link",
                "severity": "INFO",
                "message": "Back navigation link expected but not found.",
            })
    
    def _extract_component_text(
        self, 
        comp: Dict[str, Any], 
        detected: List[Dict[str, Any]], 
        ocr_text: str
    ) -> str:
        """Extract text content from a detected component."""
        # Simple heuristic: look for text property or infer from position
        if "text" in comp:
            return comp["text"]
        if "title" in comp:
            return comp["title"]
        if "label" in comp:
            return comp["label"]
        
        # Look at OCR text for component context
        if comp.get("location"):
            loc = comp["location"].lower()
            if "top-center" in loc or "center" in loc:
                # Try to extract from first line of OCR
                lines = [l for l in ocr_text.split("\n") if len(l.strip()) > 0]
                return lines[0][:50] if lines else ""
        
        return ""
    
    def _has_label_for_input(self, input_comp: Dict[str, Any], detected: List[Dict[str, Any]]) -> bool:
        """Check if an input has an associated label element."""
        # Simple heuristic: look for nearby "label" or "@label" components
        input_id = input_comp.get("field", input_comp.get("id", ""))
        
        for comp in detected:
            if "label" in comp and str(comp["label"]).lower() not in ["required", "optional"]:
                if input_id.lower() in str(comp.get("for", "")).lower():
                    return True
        
        return False


# =============================================================================
# COMPARISON RESULT (Phase 4 output)
# =============================================================================

class ComparisonResult:
    """Structured result from a comparison operation."""
    
    def __init__(
        self,
        url: str,
        missing: Optional[List[Dict[str, Any]]] = None,
        unexpected: Optional[List[Dict[str, Any]]] = None,
        label_mismatches: Optional[List[Dict[str, Any]]] = None,
        layout_problems: Optional[List[Dict[str, Any]]] = None,
        accessibility_warnings: Optional[List[Dict[str, Any]]] = None,
        navigation_problems: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize comparison result."""
        self.url = url
        self.missing = missing or []
        self.unexpected = unexpected or []
        self.label_mismatches = label_mismatches or []
        self.layout_problems = layout_problems or []
        self.accessibility_warnings = accessibility_warnings or []
        self.navigation_problems = navigation_problems or []
    
    @property
    def is_pass(self) -> bool:
        """Check if comparison passed (no ERROR-level issues)."""
        return not any(
            finding.get("severity") == "ERROR"
            for finding in (
                self.missing + self.unexpected + self.label_mismatches +
                self.layout_problems + self.accessibility_warnings + self.navigation_problems
            )
        )
    
    @property
    def failure_count(self) -> int:
        """Count of ERROR-level issues."""
        return sum(
            1 for finding in (
                self.missing + self.unexpected + self.label_mismatches +
                self.layout_problems + self.accessibility_warnings + self.navigation_problems
            ) if finding.get("severity") == "ERROR"
        )
    
    @property
    def warning_count(self) -> int:
        """Count of WARNING-level issues."""
        return sum(
            1 for finding in (
                self.missing + self.unexpected + self.label_mismatches +
                self.layout_problems + self.accessibility_warnings + self.navigation_problems
            ) if finding.get("severity") == "WARNING"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "url": self.url,
            "missing_components": self.missing,
            "unexpected_components": self.unexpected,
            "label_mismatches": self.label_mismatches,
            "layout_problems": self.layout_problems,
            "accessibility_warnings": self.accessibility_warnings,
            "navigation_problems": self.navigation_problems,
            "is_pass": self.is_pass,
            "failure_count": self.failure_count,
            "warning_count": self.warning_count,
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_comparison_result(
    url: str,
    missing: Optional[List[Dict[str, Any]]] = None,
    unexpected: Optional[List[Dict[str, Any]]] = None,
    label_mismatches: Optional[List[Dict[str, Any]]] = None,
    layout_problems: Optional[List[Dict[str, Any]]] = None,
    accessibility_warnings: Optional[List[Dict[str, Any]]] = None,
    navigation_problems: Optional[List[Dict[str, Any]]] = None,
) -> ComparisonResult:
    """Factory function to create a comparison result."""
    return ComparisonResult(
        url=url,
        missing=missing or [],
        unexpected=unexpected or [],
        label_mismatches=label_mismatches or [],
        layout_problems=layout_problems or [],
        accessibility_warnings=accessibility_warnings or [],
        navigation_problems=navigation_problems or [],
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ComparisonEngine",
    "ComparisonResult",
    "create_comparison_result",
]
