#!/usr/bin/env python3
"""
Milestone Definition Parser for Sanskriti AI Studio.

This module parses milestone Markdown files from docs/milestones/ and converts them
into structured runtime objects that all agents can consume instead of reading
raw Markdown directly.

Version: 1.0
Last Updated: 2026-08-06
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)

MILESTONES_DIR = os.path.join(WORKSPACE_ROOT, "docs", "milestones")
PARSER_STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state", "milestone_parser")
CACHE_FILE = os.path.join(PARSER_STATE_DIR, "milestone_cache.json")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# Regex patterns module-level (outside class)
PATTERNS = {
    "title": re.compile(r"^(?:# )?(MILESTONE\s+06\.\d+|STEP-\S+)\s*—?\s*(.+)$", re.MULTILINE),
    "id": re.compile(r"MILESTONE\s+(?:06\.|Milestone\s+\d+\.)?(\d+\.\d+)"),
    "summary": re.compile(r"^##\s*Summary\s*$\n(.*?)\n^##", re.DOTALL | re.MULTILINE),
    "detailed_description": re.compile(r"^##\s*Detailed\s+Description\s*$\n(.*?)\n^##", re.DOTALL | re.MULTILINE),
    "business_objective": re.compile(r"^##\s*Business\s+Objective\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "scope_in": re.compile(r"\*\*In Scope:\*\*\s*\n((?:- .*?\n?)+?)\s*\*\*Out of Scope:\*\*\*", re.DOTALL | re.MULTILINE),
    "scope_out": re.compile(r"\*\*Out of Scope:\*\*\*\s*\n((?:- .*?\n?)+?)", re.DOTALL | re.MULTILINE),
    "prerequisites": re.compile(r"^##\s*Prerequisites\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "dependencies": re.compile(r"^##\s*Dependencies\s*$\n(.*?)(?=\n^---|$)", re.DOTALL | re.MULTILINE),
    "functional_requirements": re.compile(r"^##\s*Functional\s+Requirements\s*$\n((?:\d+\.\s+.+\n?)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "technical_requirements": re.compile(r"^##\s*Technical\s+Requirements\s*$\n((?:\d+\.\s+.+\n?)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "acceptance_criteria": re.compile(r"^##\s*Acceptance\s+Criteria\s*$\n((?:\d+\.\s+.+\n?)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "validation_steps": re.compile(r"^##\s*Validation\s+Steps\s*$\n((?:\d+\.\s+.+\n?)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "documentation_requirements": re.compile(r"^##\s*Documentation\s+Requirements\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "estimated_tasks": re.compile(r"^##\s*Estimated\s+Tasks\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "related_apis": re.compile(r"^##\s*Related\s+APIs\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "database_changes": re.compile(r"^##\s*Database\s+Changes\s*$\n((?:```sql[\s\S]*?```|[^`\n]+)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "frontend_changes": re.compile(r"^##\s*Frontend\s+Changes\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "backend_changes": re.compile(r"^##\s*Backend\s+Changes\s*$\n(.*?)(?=\n^##|$)", re.DOTALL | re.MULTILINE),
    "testing_requirements": re.compile(r"^##\s*Testing\s+Requirements\s*$\n((?:\d+\.\s+.+\n?)+?)\s*^##", re.DOTALL | re.MULTILINE),
    "completion_definition": re.compile(r"^##\s*Completion\s+Definition\s*$\n(.*?)(?=\n^---|$)", re.DOTALL | re.MULTILINE),
    "implementation_notes": re.compile(r"^##\s*Implementation\s+Notes\s*$\n((?:### .*?\n(?:- .*?\n?)*)+)\s*$", re.DOTALL | re.MULTILINE),
}


class MilestoneValidationError(Exception):
    """Exception raised when a milestone fails validation."""
    
    def __init__(self, milestone_id: Optional[str] = None, message: str = ""):
        self.milestone_id = milestone_id
        self.message = message
        super().__init__(f"MilestoneValidationError{milestone_id}: {message}" if milestone_id else f"MilestoneValidationError: {message}")


class CircularDependencyError(Exception):
    """Exception raised when circular dependencies are detected."""
    
    def __init__(self, cycle_path: List[str]):
        self.cycle_path = cycle_path
        message = f"Circular dependency detected: {' -> '.join(cycle_path)} -> {cycle_path[0]}"
        super().__init__(message)


class MilestoneDuplicateError(Exception):
    """Exception raised when duplicate milestone IDs are detected."""
    
    def __init__(self, existing_id: str, new_content: Dict[str, Any]):
        self.existing_id = existing_id
        self.new_content = new_content
        super().__init__(f"MilestoneDuplicate: Existing ID '{existing_id}' conflicts with new content")


class MissingFieldError(Exception):
    """Exception raised when required fields are missing."""
    
    def __init__(self, field_name: str, milestone_id: Optional[str] = None):
        self.field_name = field_name
        self.milestone_id = milestone_id
        message = f"Missing required field: {field_name}"
        if milestone_id:
            message += f" in Milestone {milestone_id}"
        super().__init__(message)


class MalformedMarkdownError(Exception):
    """Exception raised when Markdown is malformed."""
    
    def __init__(self, error_type: str, details: Optional[str] = None):
        self.error_type = error_type
        self.details = details or ""
        message = f"Malformed markdown: {error_type}"
        if details:
            message += f": {details}"
        super().__init__(message)


class MilestoneDependencies:
    """Structured dependencies for a milestone."""
    
    def __init__(self, upstream: Optional[str] = None, 
                 downstream: Optional[str] = None,
                 external: Optional[str] = None):
        self.upstream = upstream
        self.downstream = downstream
        self.external = external
    
    @classmethod
    def empty(cls) -> "MilestoneDependencies":
        return cls()
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "upstream": self.upstream or "",
            "downstream": self.downstream or "",
            "external": self.external or "",
        }


class MilestoneScope:
    """Structured scope for a milestone."""
    
    def __init__(self, in_scope: Optional[List[str]] = None, out_of_scope: Optional[List[str]] = None):
        self.in_scope = in_scope or []
        self.out_of_scope = out_of_scope or []


class MilestoneRuntimeObject:
    """
    Strongly-typed runtime object representing a parsed milestone.
    
    This object is consumed by all agents (Planner, Coding Agent, Testing Agent,
    Reviewer Agent, Documentation Agent, Scheduler, Validation Engine).
    """
    
    def __init__(self, 
                 id: str,
                 title: str,
                 summary: Optional[str] = None,
                 detailed_description: Optional[str] = None,
                 business_objective: Optional[str] = None,
                 scope: Optional[Dict[str, List[str]]] = None,
                 prerequisites: Optional[List[Dict[str, Any]]] = None,
                 dependencies: Optional[Dict[str, str]] = None,
                 functional_requirements: Optional[List[Dict[str, Any]]] = None,
                 technical_requirements: Optional[List[Dict[str, Any]]] = None,
                 acceptance_criteria: Optional[List[Dict[str, Any]]] = None,
                 validation_steps: Optional[List[Dict[str, Any]]] = None,
                 documentation_requirements: Optional[List[Dict[str, Any]]] = None,
                 estimated_tasks: Optional[List[Dict[str, Any]]] = None,
                 related_apis: Optional[List[Dict[str, str]]] = None,
                 database_changes: Optional[str] = None,
                 frontend_changes: Optional[str] = None,
                 backend_changes: Optional[str] = None,
                 testing_requirements: Optional[Union[List[str], List[Dict[str, Any]]]] = None,
                 completion_definition: Optional[str] = None,
                 implementation_notes: Optional[Dict[str, Any]] = None):
        """
        Initialize a MilestoneRuntimeObject.
        
        Args:
            id: Milestone identifier (e.g., "06.01", "06_01")
            title: Milestone title
            summary: Concise one-line description
            detailed_description: Comprehensive explanation
            business_objective: Business value delivered
            scope: Dictionary with "in_scope" and "out_of_scope" lists
            prerequisites: List of prerequisite items with checked status
            dependencies: Dictionary with "upstream", "downstream", "external"
            functional_requirements: List of functional requirement items
            technical_requirements: List of technical requirement items
            acceptance_criteria: List of acceptance criteria items
            validation_steps: List of validation step items
            documentation_requirements: List of documentation requirement items
            estimated_tasks: List of estimated task descriptions
            related_apis: Optional list of API path-description pairs
            database_changes: SQL migration script or description
            frontend_changes: Frontend file changes
            backend_changes: Backend file changes
            testing_requirements: List of testing requirements (strings or dicts)
            completion_definition: Definition of when milestone is complete
            implementation_notes: Additional notes and implementation guidance
        """
        # Core identification
        self.id = id
        self.title = title
        
        # Descriptive fields
        self.summary = summary or ""
        self.detailed_description = detailed_description or ""
        
        # Business value
        self.business_objective = business_objective or ""
        
        # Scope
        self.scope: Dict[str, List[str]] = scope or {
            "in_scope": [],
            "out_of_scope": []
        }
        
        # Dependencies and prerequisites
        self.prerequisites: List[Dict[str, Any]] = prerequisites or []
        self.dependencies: Dict[str, str] = dependencies or {
            "upstream": "",
            "downstream": "",
            "external": ""
        }
        
        # Requirements
        self.functional_requirements: List[Dict[str, Any]] = functional_requirements or []
        self.technical_requirements: List[Dict[str, Any]] = technical_requirements or []
        
        # Criteria and validation
        self.acceptance_criteria: List[Dict[str, Any]] = acceptance_criteria or []
        self.validation_steps: List[Dict[str, Any]] = validation_steps or []
        
        # Documentation
        self.documentation_requirements: List[Dict[str, Any]] = documentation_requirements or []
        
        # Tasks
        self.estimated_tasks: List[Dict[str, Any]] = estimated_tasks or []
        
        # Changes and APIs
        self.related_apis: List[Dict[str, str]] = related_apis or []
        self.database_changes = database_changes or ""
        self.frontend_changes = frontend_changes or ""
        self.backend_changes = backend_changes or ""
        
        # Testing and completion
        if testing_requirements:
            if isinstance(testing_requirements, list) and len(testing_requirements) > 0:
                if isinstance(testing_requirements[0], str):
                    self.testing_requirements = testing_requirements
                else:
                    self.testing_requirements = testing_requirements
            else:
                self.testing_requirements = []
        else:
            self.testing_requirements = []
        
        self.completion_definition = completion_definition or ""
        
        # Additional notes
        self.implementation_notes = implementation_notes or {}
        
        # Metadata
        self.created_at = utc_now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MilestoneRuntimeObject":
        """Create a MilestoneRuntimeObject from a dictionary."""
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            summary=data.get("summary"),
            detailed_description=data.get("detailed_description"),
            business_objective=data.get("business_objective"),
            scope=data.get("scope"),
            prerequisites=data.get("prerequisites") or [],
            dependencies=data.get("dependencies") or {},
            functional_requirements=data.get("functional_requirements") or [],
            technical_requirements=data.get("technical_requirements") or [],
            acceptance_criteria=data.get("acceptance_criteria") or [],
            validation_steps=data.get("validation_steps") or [],
            documentation_requirements=data.get("documentation_requirements") or [],
            estimated_tasks=data.get("estimated_tasks") or [],
            related_apis=data.get("related_apis") or [],
            database_changes=str(data.get("database_changes", "")),
            frontend_changes=str(data.get("frontend_changes", "")),
            backend_changes=str(data.get("backend_changes", "")),
            testing_requirements=data.get("testing_requirements"),
            completion_definition=str(data.get("completion_definition", "")),
            implementation_notes=data.get("implementation_notes") or {},
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "title": str(self.title),
            "summary": self.summary,
            "detailed_description": self.detailed_description,
            "business_objective": self.business_objective,
            "scope": self.scope,
            "prerequisites": self.prerequisites,
            "dependencies": {k: v for k, v in self.dependencies.items() if v},
            "functional_requirements": self.functional_requirements,
            "technical_requirements": self.technical_requirements,
            "acceptance_criteria": self.acceptance_criteria,
            "validation_steps": self.validation_steps,
            "documentation_requirements": self.documentation_requirements,
            "estimated_tasks": self.estimated_tasks,
            "related_apis": self.related_apis,
            "database_changes": self.database_changes,
            "frontend_changes": self.frontend_changes,
            "backend_changes": self.backend_changes,
            "testing_requirements": self.testing_requirements if self.testing_requirements else None,
            "completion_definition": self.completion_definition,
            "implementation_notes": self.implementation_notes,
            "created_at": self.created_at,
        }
    
    def __eq__(self, other) -> bool:
        """Compare two milestones by their IDs."""
        if not isinstance(other, MilestoneRuntimeObject):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on milestone ID."""
        return hash(self.id)
    
    def __repr__(self) -> str:
        return f"MilestoneRuntimeObject(id={self.id!r}, title={self.title!r})"


class MilestoneParser:
    """
    Parser that converts milestone Markdown files into structured runtime objects.
    
    This parser:
    1. Reads milestone Markdown from docs/milestones/
    2. Extracts all fields according to the standard template
    3. Validates the extracted content
    4. Returns MilestoneRuntimeObject instances
    """
    
    @classmethod
    def parse_markdown(cls, content: str, id_hint: Optional[str] = None) -> Tuple[Optional[MilestoneRuntimeObject], List[str]]:
        """
        Parse milestone Markdown content into a runtime object.
        
        Args:
            content: Raw Markdown content from the milestone file
            id_hint: Optional ID hint to extract from filename or request
            
        Returns:
            Tuple of (MilestoneRuntimeObject, list of warnings)
            
        Raises:
            MilestoneValidationError: If validation fails
            MalformedMarkdownError: If Markdown is malformed
        """
        if not content or not isinstance(content, str):
            raise MalformedMarkdownError("empty_or_null_content")
        
        # Extract ID from filename hint if provided
        extracted_id = None
        if id_hint:
            match = PATTERNS["id"].search(id_hint)
            if match:
                extracted_id = match.group(1).strip()
        
        # Try to extract title and ID from content first
        title_match = PATTERNS["title"].search(content)
        if title_match:
            full_title = title_match.group(0)
            id_match = PATTERNS["id"].search(full_title)
            
            if id_match:
                milestone_id = id_match.group(1).strip()
            else:
                # Extract just the number from "MILESTONE 6.01 — Database Foundation"
                milestone_id_match = re.search(r"MILESTONE\s+(\d+\.\d+)", full_title)
                if milestone_id_match:
                    milestone_id = milestone_id_match.group(1).strip()
                else:
                    raise MalformedMarkdownError("missing_milestone_number")
            
            title_groups = title_match.groups()
            title = title_groups[1] if len(title_groups) > 1 else "Untitled"
        elif extracted_id:
            # Use the ID hint as part of the title - handle potential None id_hint safely
            if id_hint:
                title = id_hint.replace("MILESTONE", "").replace(f"{extracted_id} — ", "")[:80] or f"Milestone {extracted_id}"
            else:
                title = f"Milestone {extracted_id}"
            milestone_id = extracted_id
        else:
            raise MalformedMarkdownError("missing_milestone_header")
        
        # Extract all sections using regex patterns
        data = cls._extract_sections(content, id_hint if extracted_id else None)
        
        # Create runtime object with empty defaults to avoid type errors
        scope_dict = cls._parse_scope(data.get("scope_content", ""))
        prereqs = cls._parse_prerequisites(data.get("prerequisites", ""))
        deps = cls._parse_dependencies(data.get("dependencies", ""))
        
        object = MilestoneRuntimeObject(
            id=str(milestone_id),
            title=str(title),
            summary=str(data.get("summary", "")),
            detailed_description=str(data.get("detailed_description", "")),
            business_objective=str(data.get("business_objective", "")),
            scope=scope_dict,
            prerequisites=prereqs,
            dependencies={k: v for k, v in deps.items() if v},
            functional_requirements=cls._parse_list_items(data.get("functional_requirements", "")),
            technical_requirements=cls._parse_list_items(data.get("technical_requirements", "")),
            acceptance_criteria=cls._parse_list_items(data.get("acceptance_criteria", "")),
            validation_steps=cls._parse_list_items(data.get("validation_steps", "")),
            documentation_requirements=cls._parse_prerequisites(data.get("documentation_requirements", "")),
            estimated_tasks=cls._parse_list_items(data.get("estimated_tasks", "")),
            related_apis=cls._parse_related_apis(data.get("related_apis", "")),
            database_changes=str(data.get("database_changes", "")),
            frontend_changes=str(data.get("frontend_changes", "")),
            backend_changes=str(data.get("backend_changes", "")),
            testing_requirements=cls._parse_list_items(data.get("testing_requirements", "")) if data.get("testing_requirements") else [],
            completion_definition=str(data.get("completion_definition", "")),
            implementation_notes=data.get("implementation_notes", {}),
        )
        
        # Validate the object
        warnings = []
        
        # Check for duplicate IDs
        if cls._is_duplicate_id(str(milestone_id)):
            warnings.append(f"Warning: Milestone ID '{milestone_id}' may be a duplicate. Verify uniqueness.")
        
        # Log successful parse
        cls._log_event(f"Parsed milestone: {milestone_id} - {title}")
        
        return (object, warnings)
    
    @staticmethod
    def _extract_sections(content: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Extract all sections from content using regex patterns."""
        extracted: Dict[str, Any] = {}
        
        # Extract each section type
        for pattern_name, pattern in PATTERNS.items():
            match = pattern.search(content)
            if match:
                groups = match.groups()
                value = groups[0] if groups else ""
                extracted[pattern_name] = str(value).strip()
        
        # Try to extract scope without the delimiter first
        scope_content_match = re.search(r"^##\s*Scope\s*$\n((?:\*\*[^**]*\s*:.*?\n(?:- .*?\n?)+?)*)", content, re.DOTALL | re.MULTILINE)
        if scope_content_match:
            extracted["scope_content"] = str(scope_content_match.group(1)).strip()
        
        # Try implementation notes without section markers
        impl_notes_match = re.search(r"^##\s*Implementation\s+Notes\s*$\n((?:### .*?\n(?:- .*?\n?)*)+)\s*(?:$|\*\*|$)", content, re.DOTALL | re.MULTILINE)
        if not impl_notes_match and "implementation" in content.lower():
            # Extract as raw text without markdown structure for notes
            extracted["implementation_notes"] = {"raw": ""}
        
        return extracted
    
    @staticmethod
    def _parse_scope(content: str) -> Dict[str, List[str]]:
        """Parse scope section into structured dict."""
        result: Dict[str, List[str]] = {
            "in_scope": [],
            "out_of_scope": []
        }
        
        if not content:
            return result
        
        # Extract in scope items
        in_match = re.search(r"\*\*In Scope:\*\*\s*\n((?:- .*?\n?)+?)", content, re.DOTALL | re.MULTILINE)
        if in_match:
            lines = [line.strip().replace("* ", "") for line in in_match.group(1).strip().split("\n") if line.strip()]
            result["in_scope"] = lines
        
        # Extract out of scope items
        out_match = re.search(r"\*\*Out of Scope:\*\*\s*\n((?:- .*?\n?)+?)", content, re.DOTALL | re.MULTILINE)
        if out_match:
            lines = [line.strip().replace("* ", "") for line in out_match.group(1).strip().split("\n") if line.strip()]
            result["out_of_scope"] = lines
        
        return result
    
    @staticmethod
    def _parse_prerequisites(content: str) -> List[Dict[str, Any]]:
        """Parse prerequisites section into list of dicts."""
        items: List[Dict[str, Any]] = []
        
        if not content:
            return items
        
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("##"):
                continue
            
            # Handle checkbox format "- [ ] item" or "- ✓ item"
            checkbox_match = re.match(r"^(\s*\[-?\s*[✓xX]?\s*\]\s+)?(.*)$", line)
            if checkbox_match:
                marker = checkbox_match.group(1) or ""
                item_text = checkbox_match.group(2).strip()
                
                # Parse item text into title and description
                colon_match = re.search(r"^([^(]+?)\((.*)$", item_text)
                if colon_match:
                    title = colon_match.group(1).strip().lstrip("-")
                    description = colon_match.group(2).strip()
                else:
                    title = item_text.lstrip("- ").replace("[✓]", "").replace("[ ]", "").replace("x", "")
                    description = ""
                
                items.append({
                    "title": str(title),
                    "description": str(description),
                    "completed": bool(marker) or "[✓]" in line or "[x]" in line or "✓" in line,
                })
        
        return items
    
    @staticmethod
    def _parse_dependencies(content: str) -> Dict[str, Optional[str]]:
        """Parse dependencies section into structured dict."""
        result: Dict[str, Optional[str]] = {
            "upstream": "",
            "downstream": "",
            "external": "",
        }
        
        if not content:
            return result
        
        # Extract upstream dependency
        upstream_match = re.search(r"-?\s*Upstream:\s*(.+)", content)
        if upstream_match:
            upstream = upstream_match.group(1).strip().replace("-", "")
            if upstream.upper() != "NONE" and upstream.lower() not in ("none", "null", ""):
                result["upstream"] = str(upstream.strip(".,;"))
        
        # Extract downstream dependency
        downstream_match = re.search(r"-?\s*Downstream:\s*(.+)", content)
        if downstream_match:
            downstream = downstream_match.group(1).strip().replace("-", "")
            if downstream.upper() != "NONE" and downstream.lower() not in ("none", "null", ""):
                result["downstream"] = str(downstream.strip(".,;"))
        
        # Extract external dependencies
        external_match = re.search(r"-?\s*External:\s*(.+)", content)
        if external_match:
            external = external_match.group(1).strip().replace("-", "")
            if external.upper() != "NONE" and external.lower() not in ("none", "null", ""):
                result["external"] = str(external.strip(".,;"))
        
        return result
    
    @staticmethod
    def _parse_list_items(content: str) -> List[Dict[str, Any]]:
        """Parse numbered list items into list of dicts."""
        items: List[Dict[str, Any]] = []
        
        if not content:
            return items
        
        # Split by line and process each numbered item
        lines = content.split("\n")
        current_item: Optional[Dict[str, Any]] = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("##"):
                continue
            
            # Look for numbered items (1. 2. etc.)
            number_match = re.match(r"^\d+\.\s+(.+)$", line)
            
            if number_match:
                # Save previous item if exists
                if current_item:
                    items.append(current_item)
                
                # Parse the numbered item
                text = number_match.group(1).strip()
                
                # Try to extract title in parentheses
                paren_match = re.search(r"^([^(]+?)\((.*)$", text)
                if paren_match:
                    current_item = {
                        "title": str(paren_match.group(1)).strip(),
                        "description": str(paren_match.group(2)).strip(),
                    }
                else:
                    current_item = {
                        "title": str(text).lstrip("1. ").lstrip("- "),
                        "description": "",
                    }
            elif current_item:
                # Add to description for multi-line items
                if current_item["description"]:
                    current_item["description"] += " " + line.strip()
                else:
                    current_item["description"] = line.strip()
        
        # Don't forget the last item
        if current_item:
            items.append(current_item)
        
        return items
    
    @staticmethod
    def _parse_related_apis(content: str) -> List[Dict[str, str]]:
        """Parse related APIs section into list of dicts."""
        apis: List[Dict[str, str]] = []
        
        if not content:
            return apis
        
        # Split by lines and look for "path - description" format
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("##"):
                continue
            
            # Look for path - description format
            parts = line.split("-", 1)
            if len(parts) == 2:
                path = parts[0].strip()
                desc = parts[1].strip()
                apis.append({
                    "path": str(path),
                    "description": str(desc),
                })
        
        return apis
    
    @classmethod
    def _is_duplicate_id(cls, id: Optional[str]) -> bool:
        """Check if milestone ID is a duplicate (simple cache check)."""
        if not id:
            return False
        
        from ai_agents.context_manager import ContextManager
        cache = ContextManager.get_cache()
        # Check if ID matches current milestone or is completed
        current = cache.metadata.get('current_milestone', '')
        completed = list(cache.metadata.get('milestones_completed', []))
        return str(id) == current or str(id) in [str(m) for m in completed]
    
    @classmethod
    def _log_event(cls, message: str):
        """Log parsing event to state directory."""
        os.makedirs(PARSER_STATE_DIR, exist_ok=True)
        
        event = {
            "type": "PARSE_EVENT",
            "message": message,
            "timestamp": utc_now(),
        }
        
        log_path = os.path.join(PARSER_STATE_DIR, "parse_log.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    
    @classmethod
    def get_cache(cls):
        """Get or create the parser cache instance."""
        from ai_agents.context_manager import ContextManager
        
        # Use existing context manager's cache for file modification tracking
        return ContextManager.get_cache()


def validate_milestone_runtime_object(obj: MilestoneRuntimeObject) -> List[str]:
    """
    Validate a MilestoneRuntimeObject for completeness and correctness.
    
    Returns a list of warnings (empty if no issues found).
    """
    warnings: List[str] = []
    
    # Check ID format
    id_match = re.match(r"^(\d+\.\d+)$", str(obj.id))
    if not id_match:
        warnings.append(f"Invalid milestone ID format: '{obj.id}'. Expected format: 'X.Y'")
    
    # Check title
    if not obj.title or not str(obj.title).strip():
        warnings.append(f"Milestone {obj.id} has empty title")
    
    # Check that scope is valid
    if not isinstance(obj.scope, dict):
        warnings.append(f"Milestone {obj.id} has invalid scope structure")
    elif len(obj.scope.get("in_scope", [])) == 0 and len(obj.scope.get("out_of_scope", [])) == 0:
        warnings.append(f"Milestone {obj.id} scope is empty - consider defining scope boundaries")
    
    # Check prerequisites are parseable
    for prereq in obj.prerequisites:
        if not isinstance(prereq, dict):
            warnings.append(f"Milestone {obj.id} has malformed prerequisite: {prereq}")
    
    # Check acceptance criteria exist
    if len(obj.acceptance_criteria) == 0:
        warnings.append(f"Milestone {obj.id} has no acceptance criteria defined")
    
    return warnings


def load_milestone_from_file(filepath: str) -> Tuple[Optional[MilestoneRuntimeObject], List[str]]:
    """
    Load and parse a milestone from a Markdown file.
    
    Args:
        filepath: Path to the milestone Markdown file
        
    Returns:
        Tuple of (MilestoneRuntimeObject, list of warnings/errors)
        
    Raises:
        MilestoneValidationError: If validation fails
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Milestone file not found: {filepath}")
    
    # Read file content
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise MalformedMarkdownError("read_error", str(e))
    
    # Parse the content
    milestone_obj, parse_warnings = MilestoneParser.parse_markdown(content, os.path.basename(filepath))
    
    # Handle parse result - parse_markdown returns Optional[MilestoneRuntimeObject]
    if milestone_obj is None:
        return (None, parse_warnings)
    
    # Validate only if we have a valid object
    validation_warnings = validate_milestone_runtime_object(milestone_obj)
    all_warnings = parse_warnings + validation_warnings
    
    return (milestone_obj, all_warnings)


def parse_all_milestones() -> Tuple[List[MilestoneRuntimeObject], List[str]]:
    """
    Parse all milestone files from the milestones directory.
    
    Returns:
        Tuple of (list of MilestoneRuntimeObject, list of warnings/errors)
    """
    milestones: List[MilestoneRuntimeObject] = []
    all_warnings: List[str] = []
    
    if not os.path.exists(MILESTONES_DIR):
        raise FileNotFoundError(f"Milestones directory not found: {MILESTONES_DIR}")
    
    # Get all milestone files (sorted by name for consistent ordering)
    milestone_files = sorted([
        f for f in os.listdir(MILESTONES_DIR) 
        if os.path.isfile(os.path.join(MILESTONES_DIR, f)) and f.endswith(".md")
    ])
    
    for filename in milestone_files:
        filepath = os.path.join(MILESTONES_DIR, filename)
        
        try:
            milestone_obj, warnings = load_milestone_from_file(filepath)
            
            if milestone_obj:
                milestones.append(milestone_obj)
            
            all_warnings.extend(warnings)
            
        except Exception as e:
            error_msg = str(e)
            if "Malformed" in error_msg or "ValidationError" in error_msg:
                all_warnings.append(f"Failed to parse {filename}: {error_msg}")
            else:
                all_warnings.append(f"Unexpected error parsing {filename}: {error_msg}")
    
    return (milestones, all_warnings)


def save_milestone_to_cache(obj: MilestoneRuntimeObject) -> None:
    """Save parsed milestone to cache for reuse."""
    os.makedirs(PARSER_STATE_DIR, exist_ok=True)
    
    # Load existing cache
    cache_data: Dict[str, Any] = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except Exception:
            pass
    
    # Add new milestone to cache
    cache_data[str(obj.id)] = obj.to_dict()
    
    # Save updated cache
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, default=str)


def load_milestone_from_cache(milestone_id: str) -> Optional[MilestoneRuntimeObject]:
    """Load a parsed milestone from cache."""
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        if str(milestone_id) in cache_data:
            obj_dict = cache_data[str(milestone_id)]
            return MilestoneRuntimeObject.from_dict(obj_dict)
    except Exception:
        pass
    
    return None


def invalidate_milestone_cache(milestone_id: Optional[str] = None) -> None:
    """Invalidate cache for a specific milestone or all milestones."""
    if not os.path.exists(CACHE_FILE):
        return
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        # Remove specified milestone or clear all
        if milestone_id:
            cache_data.pop(str(milestone_id), None)
        else:
            cache_data.clear()
        
        # Also remove milestone_ids key if it exists
        if "milestone_ids" in cache_data:
            del cache_data["milestone_ids"]
        
        # Save updated cache
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, default=str)
    except Exception as e:
        print(f"[Milestone Parser] Cache invalidation error: {e}")


def check_milestones_changed() -> bool:
    """Check if any milestone files have changed since last cache update."""
    if not os.path.exists(CACHE_FILE):
        return True  # No cache exists, need to rebuild
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        cache_mtime = os.path.getmtime(CACHE_FILE)
        
        # Get all milestone file mtimes
        if not os.path.exists(MILESTONES_DIR):
            return True
        
        latest_milestone_mtime = 0.0
        for filename in os.listdir(MILESTONES_DIR):
            if filename.endswith(".md"):
                filepath = os.path.join(MILESTONES_DIR, filename)
                mtime = os.path.getmtime(filepath)
                if mtime > latest_milestone_mtime:
                    latest_milestone_mtime = float(mtime)
        
        return latest_milestone_mtime > cache_mtime
        
    except Exception:
        return True  # On error, assume changes


# Export main classes and functions
__all__ = [
    "MilestoneValidationError",
    "CircularDependencyError", 
    "MilestoneDuplicateError",
    "MissingFieldError",
    "MalformedMarkdownError",
    "MilestoneDependencies",
    "MilestoneScope",
    "MilestoneRuntimeObject",
    "MilestoneParser",
    "validate_milestone_runtime_object",
    "load_milestone_from_file",
    "parse_all_milestones",
    "save_milestone_to_cache",
    "load_milestone_from_cache",
    "invalidate_milestone_cache",
    "check_milestones_changed",
]
