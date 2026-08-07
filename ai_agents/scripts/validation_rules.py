#!/usr/bin/env python3
"""
UI Validation Rules for Sanskriti AI Studio.

This module defines all validation rules that the UI Validation Engine
can check against Vision Analysis results.

Version: 1.0
Last Updated: 2026-08-07
"""

import re
from typing import Any, Dict, List, Optional


# =============================================================================
# VALIDATION RULE CATEGORIES (Phase 2)
# =============================================================================

VALIDATION_CATEGORIES = {
    "REQUIRED_PAGES": "required_pages",
    "NAVIGATION": "navigation",
    "BUTTONS": "buttons",
    "FORMS": "forms",
    "TABLES": "tables",
    "INPUTS": "inputs",
    "LABELS": "labels",
    "HEADINGS": "headings",
    "LAYOUT": "layout",
    "VISIBILITY": "visibility",
    "RESPONSIVENESS": "responsiveness",
    "ERROR_MESSAGES": "error_messages",
    "LOADING_STATES": "loading_states",
    "EMPTY_STATES": "empty_states",
}

# =============================================================================
# RULE DEFINITIONS (Phase 2)
# =============================================================================

RULE_DEFINITIONS = {
    # Required Pages
    VALIDATION_CATEGORIES["REQUIRED_PAGES"]: {
        "id": "PAGE-001",
        "category": VALIDATION_CATEGORIES["REQUIRED_PAGES"],
        "description": "Verify that required pages exist and are accessible.",
        "check_type": "presence",
        "expected_field": "detected_components",
    },
    
    # Navigation
    VALIDATION_CATEGORIES["NAVIGATION"]: {
        "id": "NAV-001",
        "category": VALIDATION_CATEGORIES["NAVIGATION"],
        "description": "Verify navigation elements are present and functional.",
        "check_type": "presence",
        "expected_field": "detected_components",
    },
    
    # Buttons
    VALIDATION_CATEGORIES["BUTTONS"]: {
        "id": "BTN-001",
        "category": VALIDATION_CATEGORIES["BUTTONS"],
        "description": "Verify required buttons are present with correct labels.",
        "check_type": "presence_and_label",
        "expected_field": "detected_components",
    },
    
    # Forms
    VALIDATION_CATEGORIES["FORMS"]: {
        "id": "FORM-001",
        "category": VALIDATION_CATEGORIES["FORMS"],
        "description": "Verify form elements are present and properly structured.",
        "check_type": "presence_and_structure",
        "expected_field": "detected_components",
    },
    
    # Tables
    VALIDATION_CATEGORIES["TABLES"]: {
        "id": "TAB-001",
        "category": VALIDATION_CATEGORIES["TABLES"],
        "description": "Verify table elements are present with correct headers.",
        "check_type": "presence_and_structure",
        "expected_field": "detected_components",
    },
    
    # Inputs
    VALIDATION_CATEGORIES["INPUTS"]: {
        "id": "INPUT-001",
        "category": VALIDATION_CATEGORIES["INPUTS"],
        "description": "Verify input fields are present with appropriate labels.",
        "check_type": "presence_and_label",
        "expected_field": "detected_components",
    },
    
    # Labels
    VALIDATION_CATEGORIES["LABELS"]: {
        "id": "LBL-001",
        "category": VALIDATION_CATEGORIES["LABELS"],
        "description": "Verify labels are present and correctly associated with fields.",
        "check_type": "presence_and_association",
        "expected_field": "detected_components",
    },
    
    # Headings
    VALIDATION_CATEGORIES["HEADINGS"]: {
        "id": "HDR-001",
        "category": VALIDATION_CATEGORIES["HEADINGS"],
        "description": "Verify heading hierarchy (H1-H6) is correct.",
        "check_type": "presence_and_hierarchy",
        "expected_field": "detected_components",
    },
    
    # Layout
    VALIDATION_CATEGORIES["LAYOUT"]: {
        "id": "LAY-001",
        "category": VALIDATION_CATEGORIES["LAYOUT"],
        "description": "Verify layout structure follows expected patterns.",
        "check_type": "structure",
        "expected_field": "visual_issues",
    },
    
    # Visibility
    VALIDATION_CATEGORIES["VISIBILITY"]: {
        "id": "VSB-001",
        "category": VALIDATION_CATEGORIES["VISIBILITY"],
        "description": "Verify elements are visible when they should be.",
        "check_type": "visibility",
        "expected_field": "visual_issues",
    },
    
    # Responsiveness
    VALIDATION_CATEGORIES["RESPONSIVENESS"]: {
        "id": "RSP-001",
        "category": VALIDATION_CATEGORIES["RESPONSIVENESS"],
        "description": "Verify layout adapts correctly at different viewport sizes.",
        "check_type": "responsive",
        "expected_field": "visual_issues",
    },
    
    # Error Messages
    VALIDATION_CATEGORIES["ERROR_MESSAGES"]: {
        "id": "ERR-001",
        "category": VALIDATION_CATEGORIES["ERROR_MESSAGES"],
        "description": "Verify error messages are displayed when appropriate.",
        "check_type": "presence",
        "expected_field": "ocr_text",
    },
    
    # Loading States
    VALIDATION_CATEGORIES["LOADING_STATES"]: {
        "id": "LDG-001",
        "category": VALIDATION_CATEGORIES["LOADING_STATES"],
        "description": "Verify loading indicators are shown during async operations.",
        "check_type": "presence",
        "expected_field": "detected_components",
    },
    
    # Empty States
    VALIDATION_CATEGORIES["EMPTY_STATES"]: {
        "id": "EMP-001",
        "category": VALIDATION_CATEGORIES["EMPTY_STATES"],
        "description": "Verify empty state messages are shown when data is absent.",
        "check_type": "presence",
        "expected_field": "ocr_text",
    },
}


# =============================================================================
# EXPECTED UI MODEL SCHEMA (Phase 3)
# =============================================================================

class ExpectedUIModel:
    """
    Reusable UI expectation definitions.
    
    Each page may define:
    - Page Name
    - Expected Components
    - Required Components
    - Optional Components
    - Layout Rules
    - Navigation Rules
    - Responsive Rules
    - Acceptance Rules
    """
    
    def __init__(
        self,
        page_name: str,
        expected_components: Optional[List[Dict[str, Any]]] = None,
        required_components: Optional[List[Dict[str, Any]]] = None,
        optional_components: Optional[List[Dict[str, Any]]] = None,
        layout_rules: Optional[Dict[str, Any]] = None,
        navigation_rules: Optional[Dict[str, Any]] = None,
        responsive_rules: Optional[Dict[str, Any]] = None,
        acceptance_rules: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize an Expected UI Model.
        
        Args:
            page_name: Name of the page (e.g., "dashboard", "login")
            expected_components: List of all expected components with types and positions
            required_components: List of components that must be present
            optional_components: List of components that may be absent
            layout_rules: Layout constraints and guidelines
            navigation_rules: Navigation structure requirements
            responsive_rules: Responsive behavior definitions
            acceptance_rules: Acceptance criteria for this page
        """
        self.page_name = page_name
        self.expected_components = expected_components or []
        self.required_components = required_components or []
        self.optional_components = optional_components or []
        self.layout_rules = layout_rules or {}
        self.navigation_rules = navigation_rules or {}
        self.responsive_rules = responsive_rules or {}
        self.acceptance_rules = acceptance_rules or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "page_name": self.page_name,
            "expected_components": self.expected_components,
            "required_components": self.required_components,
            "optional_components": self.optional_components,
            "layout_rules": self.layout_rules,
            "navigation_rules": self.navigation_rules,
            "responsive_rules": self.responsive_rules,
            "acceptance_rules": self.acceptance_rules,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExpectedUIModel":
        """Create model from dictionary."""
        return cls(
            page_name=data.get("page_name", ""),
            expected_components=data.get("expected_components"),
            required_components=data.get("required_components"),
            optional_components=data.get("optional_components"),
            layout_rules=data.get("layout_rules", {}),
            navigation_rules=data.get("navigation_rules", {}),
            responsive_rules=data.get("responsive_rules", {}),
            acceptance_rules=data.get("acceptance_rules", []),
        )


# =============================================================================
# PAGES CATALOG (Phase 3) - Predefined UI Models
# =============================================================================

PAGES_CATALOG = {
    # Login Page
    "login": ExpectedUIModel(
        page_name="login",
        expected_components=[
            {"type": "heading", "text": "Sign In", "location": "top-center"},
            {"type": "form", "id": "login-form", "elements": ["email", "password"]},
            {"type": "button", "text": "Sign In", "location": "form-bottom"},
            {"type": "link", "text": "Forgot Password?", "location": "form-bottom"},
            {"type": "link", "text": "Create Account", "location": "bottom-center"},
        ],
        required_components=[
            {"type": "heading", "text": "Sign In"},
            {"type": "input", "field": "email", "label": "Email"},
            {"type": "input", "field": "password", "label": "Password"},
            {"type": "button", "text": "Sign In"},
        ],
        optional_components=[
            {"type": "link", "text": "Forgot Password?"},
            {"type": "link", "text": "Create Account"},
        ],
        layout_rules={
            "alignment": "centered-column",
            "max-width": "400px",
            "min-height": "100vh",
        },
        navigation_rules={
            "back_link": True,
            "logo": True,
        },
        responsive_rules={
            "mobile": {"width": "< 768px", "behavior": "fullscreen"},
            "tablet": {"width": "768-1024px", "behavior": "centered-column"},
            "desktop": {"width": "> 1024px", "behavior": "centered-column"},
        },
    ),
    
    # Dashboard Page
    "dashboard": ExpectedUIModel(
        page_name="dashboard",
        expected_components=[
            {"type": "heading", "text": "Dashboard", "location": "top-left"},
            {"type": "navigation", "id": "main-nav"},
            {"type": "widget", "id": "stats-card-1", "title": "Total Users"},
            {"type": "widget", "id": "stats-card-2", "title": "Active Sessions"},
            {"type": "widget", "id": "stats-card-3", "title": "Revenue"},
            {"type": "chart", "id": "revenue-chart", "location": "main-content"},
            {"type": "table", "id": "recent-activity", "columns": ["User", "Action", "Time"]},
            {"type": "button", "text": "Refresh Data", "location": "top-right"},
        ],
        required_components=[
            {"type": "heading", "text": "Dashboard"},
            {"type": "navigation", "id": "main-nav"},
            {"type": "widget", "id": "stats-card-1", "title": "Total Users"},
            {"type": "button", "text": "Refresh Data"},
        ],
        optional_components=[
            {"type": "widget", "id": "stats-card-2", "title": "Active Sessions"},
            {"type": "widget", "id": "stats-card-3", "title": "Revenue"},
            {"type": "chart", "id": "revenue-chart"},
            {"type": "table", "id": "recent-activity"},
        ],
        layout_rules={
            "grid-columns": 3,
            "header-height": "60px",
            "sidebar-width": "250px",
        },
        navigation_rules={
            "menu_items": ["Dashboard", "Users", "Settings"],
            "user_profile": True,
        },
        responsive_rules={
            "mobile": {"width": "< 768px", "behavior": "collapsed-sidebar"},
            "tablet": {"width": "768-1024px", "behavior": "full-sidebar"},
            "desktop": {"width": "> 1024px", "behavior": "full-sidebar"},
        },
    ),
    
    # Settings Page
    "settings": ExpectedUIModel(
        page_name="settings",
        expected_components=[
            {"type": "heading", "text": "Settings", "location": "top-left"},
            {"type": "form-section", "id": "profile-section", "title": "Profile"},
            {"type": "input-group", "field": "name", "label": "Full Name"},
            {"type": "input-group", "field": "email", "label": "Email Address"},
            {"type": "button", "text": "Save Changes", "location": "form-bottom"},
        ],
        required_components=[
            {"type": "heading", "text": "Settings"},
            {"type": "input-group", "field": "name", "label": "Full Name"},
            {"type": "button", "text": "Save Changes"},
        ],
        optional_components=[],
        layout_rules={
            "alignment": "left-aligned",
            "max-width": "600px",
        },
        navigation_rules={
            "breadcrumb": True,
            "back_link": True,
        },
    ),
}


# =============================================================================
# PAGES DEFINITION (for dynamic registration)
# =============================================================================

def register_page(
    page_name: str,
    expected_components: Optional[List[Dict[str, Any]]] = None,
    required_components: Optional[List[Dict[str, Any]]] = None,
    optional_components: Optional[List[Dict[str, Any]]] = None,
    layout_rules: Optional[Dict[str, Any]] = None,
    navigation_rules: Optional[Dict[str, Any]] = None,
    responsive_rules: Optional[Dict[str, Any]] = None,
    acceptance_rules: Optional[List[Dict[str, Any]]] = None,
) -> ExpectedUIModel:
    """
    Register a new page in the UI expectations catalog.
    
    Args:
        page_name: Name of the page
        expected_components: All expected components
        required_components: Components that must be present (FAIL if missing)
        optional_components: Components that may be absent (WARN if missing)
        layout_rules: Layout constraints
        navigation_rules: Navigation structure
        responsive_rules: Responsive behavior definitions
        acceptance_rules: Acceptance criteria list
    
    Returns:
        ExpectedUIModel instance registered in catalog
    """
    model = ExpectedUIModel(
        page_name=page_name,
        expected_components=expected_components or [],
        required_components=required_components or [],
        optional_components=optional_components or [],
        layout_rules=layout_rules or {},
        navigation_rules=navigation_rules or {},
        responsive_rules=responsive_rules or {},
        acceptance_rules=acceptance_rules or [],
    )
    
    PAGES_CATALOG[page_name] = model
    return model


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_validation_category(category_id: str) -> Optional[Dict[str, Any]]:
    """Get validation category by ID."""
    if category_id in VALIDATION_CATEGORIES:
        return {
            "id": category_id,
            "category": VALIDATION_CATEGORIES[category_id],
            "rules": [
                rule for rule_name, rule in RULE_DEFINITIONS.items()
                if rule["category"] == VALIDATION_CATEGORIES[category_id]
            ],
        }
    return None


def get_rule_definition(rule_id: str) -> Optional[Dict[str, Any]]:
    """Get rule definition by ID."""
    for rule_name, rule in RULE_DEFINITIONS.items():
        if rule["id"] == rule_id:
            return rule
    return None


def is_page_registered(page_name: str) -> bool:
    """Check if a page is registered in the UI model."""
    return page_name in PAGES_CATALOG


def get_page_model(page_name: str) -> Optional[ExpectedUIModel]:
    """Get the UI model for a registered page."""
    return PAGES_CATALOG.get(page_name)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Categories
    "VALIDATION_CATEGORIES",
    
    # Definitions
    "RULE_DEFINITIONS",
    
    # Models
    "ExpectedUIModel",
    "PAGES_CATALOG",
    "register_page",
    
    # Utilities
    "get_validation_category",
    "get_rule_definition",
    "is_page_registered",
    "get_page_model",
]
