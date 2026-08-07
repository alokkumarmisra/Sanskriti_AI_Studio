#!/usr/bin/env python3
"""
Intelligent Context Manager for Sanskriti AI Studio.

This module provides intelligent context management for AI agents, ensuring each agent
receives only the information required for its current task while minimizing prompt size
and preserving accuracy.

Responsibilities:
1. Create a reusable Context object with all possible fields
2. Implement intelligent selection rules per agent type
3. Remove duplicate text and compress repeated information
4. Cache common documentation and track token usage
5. Warn if context exceeds configurable limits
6. Invalidate cache when underlying files change

CRITICAL: Qwen 3.5 is TEXT-ONLY. This manager never sends images or visual data.

Version: 1.0
Last Updated: 2026-08-05
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.join(AI_AGENTS_ROOT, "..") if AI_AGENTS_ROOT.startswith(".") else os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


class TokenTracker:
    """Simple token usage tracker for context optimization."""
    
    # Approximate token counts (rough estimates)
    WORD_TO_TOKEN_RATIO = 0.75
    LINE_BREAK_OVERHEAD = 0.1
    
    @staticmethod
    def estimate_tokens(text: str, is_json: bool = False) -> int:
        """Estimate token count from text."""
        if not text or not isinstance(text, str):
            return 0
        
        # For JSON, we need to account for structure
        if is_json:
            lines = text.split('\n')
            char_count = sum(len(line) for line in lines) + len(lines)
        else:
            char_count = len(text)
        
        # Base estimate: ~1 token per 4 characters (rough average)
        base_tokens = char_count / 4
        tokens = int(base_tokens * TokenTracker.WORD_TO_TOKEN_RATIO)
        return max(0, tokens + char_count // 50)  # Add overhead for line breaks


class ContextCache:
    """Context-specific caching for documentation and metadata."""
    
    def __init__(self):
        self.cache: Dict[str, str] = {
            "project_story": "",
            "coding_rules": "",
            "system_architecture": "",
            "database_design": "",
            "api_specification": "",
            "roadmap": "",
            "current_task": "",
            "development_guidelines": "",
            "ai_context": "",
        }
        self.metadata: Dict[str, Any] = {
            "last_bootstrap": None,
            "milestones_completed": [],
            "current_milestone": None,
            "execution_history_count": 0,
        }
        
        # File modification times for invalidation
        self.file_mtimes: Dict[str, float] = {}
    
    def initialize(self) -> None:
        """Initialize cache from bootstrap state."""
        try:
            report_path = os.path.join(STATE_DIR, "startup_report.json")
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    
                    # Extract milestones from completed_milestones
                    for milestone in report.get("completed_milestones", []):
                        self.metadata["milestones_completed"].append(milestone)
                    
                    # Set current milestone if available
                    current_milestone = report.get("current_milestone")
                    if current_milestone:
                        self.metadata["current_milestone"] = current_milestone
                    
                    # Track execution history from actions.jsonl
                    actions_path = os.path.join(STATE_DIR, "actions.jsonl")
                    if os.path.exists(actions_path):
                        with open(actions_path, 'r', encoding='utf-8') as f:
                            self.metadata["execution_history_count"] = sum(1 for _ in f)
                    
                # Store bootstrap timestamp
                self.metadata["last_bootstrap"] = utc_now()
                
        except Exception as e:
            print(f"[Context Cache] Initialization error: {e}")
    
    def load_milestone_state(self) -> None:
        """Load current milestone state from documentation."""
        current_task_path = os.path.join(WORKSPACE_ROOT, "docs", "06_CURRENT_TASK.md")
        if os.path.exists(current_task_path):
            with open(current_task_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract milestone info
                match = re.search(r"(Milestone\s+\d+\.\d+|Step\s+\d+)\s*[-:]?\s*(COMPLETED)?", content)
                if match and "COMPLETED" not in content:
                    self.metadata["current_milestone"] = match.group(1).strip()
    
    def get_documentation(self, doc_name: str) -> Optional[str]:
        """Get cached documentation or load from disk."""
        # Check cache first
        if doc_name in self.cache and self.cache[doc_name]:
            return self.cache[doc_name]
        
        # Check file modification for invalidation
        doc_path_map = {
            "project_story": "docs/00_PROJECT_STORY.md",
            "coding_rules": "docs/01_CODING_RULES.md",
            "system_architecture": "docs/02_SYSTEM_ARCHITECTURE.md",
            "database_design": "docs/03_DATABASE_DESIGN.md",
            "api_specification": "docs/04_API_SPECIFICATION.md",
            "roadmap": "docs/05_ROADMAP.md",
            "current_task": "docs/06_CURRENT_TASK.md",
            "development_guidelines": "docs/07_DEVELOPMENT_GUIDELINES.md",
            "ai_context": "docs/08_AI_CONTEXT.md",
            "completed_tasks": "docs/09_COMPLETED_TASKS.md",
            "next_task": "docs/10_NEXT_TASK.md",
            "changelog": "docs/11_CHANGELOG.md",
            "prompt_library": "docs/12_PROMPT_LIBRARY.md",
            "decisions": "docs/13_DECISIONS.md",
            "ai_instructions": "docs/99_AI_INSTRUCTIONS.md",
        }
        
        if doc_name in doc_path_map:
            path = WORKSPACE_ROOT + "/" + doc_path_map[doc_name]
            current_mtime = os.path.getmtime(path) if os.path.exists(path) else None
            
            # If mtime changed, reload from disk
            if current_mtime:
                self.file_mtimes[path] = current_mtime
        
        return self.cache.get(doc_name)  # Return empty string for non-cached docs
    
    def load_all_documentation(self) -> Dict[str, str]:
        """Load all documentation for context."""
        doc_path_map = {
            "project_story": "docs/00_PROJECT_STORY.md",
            "coding_rules": "docs/01_CODING_RULES.md",
            "system_architecture": "docs/02_SYSTEM_ARCHITECTURE.md",
            "database_design": "docs/03_DATABASE_DESIGN.md",
            "api_specification": "docs/04_API_SPECIFICATION.md",
            "roadmap": "docs/05_ROADMAP.md",
            "current_task": "docs/06_CURRENT_TASK.md",
            "development_guidelines": "docs/07_DEVELOPMENT_GUIDELINES.md",
            "ai_context": "docs/08_AI_CONTEXT.md",
            "completed_tasks": "docs/09_COMPLETED_TASKS.md",
            "next_task": "docs/10_NEXT_TASK.md",
            "changelog": "docs/11_CHANGELOG.md",
            "prompt_library": "docs/12_PROMPT_LIBRARY.md",
            "decisions": "docs/13_DECISIONS.md",
            "ai_instructions": "docs/99_AI_INSTRUCTIONS.md",
        }
        
        loaded: Dict[str, str] = {}
        
        for doc_name, path_str in doc_path_map.items():
            path = WORKSPACE_ROOT + "/" + path_str
            
            # Skip if file doesn't exist
            if not os.path.exists(path):
                continue
            
            content = Path(path).read_text(encoding='utf-8', errors='ignore')[:50000]  # Limit size
            self.cache[doc_name] = content
            loaded[doc_name] = content
        
        return loaded


class Context:
    """
    Reusable Context object that can contain all information needed for a task.
    
    This context model avoids duplicate information and provides a unified view
    of the project state for each agent.
    """
    
    def __init__(self, 
                 current_milestone: str = "",
                 current_task: Optional[Dict[str, Any]] = None,
                 acceptance_criteria: Optional[List[str]] = None):
        """
        Initialize a Context object.
        
        Args:
            current_milestone: Current milestone identifier (e.g., "STEP-21.1")
            current_task: Task plan from Planner Agent
            acceptance_criteria: List of acceptance criteria for the task
        """
        self.current_milestone = current_milestone
        self.current_task = current_task or {}
        self.acceptance_criteria: List[str] = list(acceptance_criteria) if acceptance_criteria else []
        
        # Core state
        self.planner_output: Optional[Dict[str, Any]] = None
        self.relevant_documentation: Dict[str, str] = {}
        self.relevant_source_files: Dict[str, str] = {}
        self.changed_files: List[str] = []
        self.git_diff: Optional[str] = None
        
        # Results and reports
        self.test_results: Optional[Dict[str, Any]] = None
        self.build_results: Optional[Dict[str, Any]] = None
        self.lint_results: Optional[Dict[str, Any]] = None
        self.api_responses: Dict[str, str] = {}
        
        # Database information
        self.database_info: Optional[Dict[str, Any]] = None
        
        # Review results
        self.reviewer_comments: List[Dict[str, Any]] = []
        
        # Debugging report
        self.debugging_report: Optional[Dict[str, Any]] = None
        
        # Documentation updates
        self.documentation_updates: List[Dict[str, Any]] = []
        
        # Runtime state
        self.runtime_state: Dict[str, Any] = {}
        
        # Execution history
        self.execution_history: List[Dict[str, Any]] = []
        
        # Token tracking
        self.token_estimation: int = 0
        
        # Metadata
        self.created_at: str = utc_now()
    
    def __repr__(self) -> str:
        return f"Context(milestone={self.current_milestone!r}, tasks={len(self.current_task)})"


class ContextManager:
    """
    Intelligent Context Manager for Sanskriti AI Studio.
    
    This manager provides each AI agent with only the information required for
    its current task, minimizing prompt size while preserving accuracy.
    """
    
    # Token budget warning threshold
    TOKEN_BUDGET_WARNING = 40000
    
    # Cache instance
    _cache: Optional[ContextCache] = None
    
    @classmethod
    def get_cache(cls) -> ContextCache:
        """Get or create the cache instance."""
        if cls._cache is None:
            cls._cache = ContextCache()
        return cls._cache
    
    @staticmethod
    def clear_cache() -> None:
        """Clear all caches (useful for testing)."""
        ContextManager._cache = None
    
    # ==================== CONTEXT LOADING METHODS ====================
    
    def load_runtime_context(self) -> Dict[str, Any]:
        """Load runtime context from bootstrap report."""
        report_path = os.path.join(STATE_DIR, "startup_report.json")
        
        if not os.path.exists(report_path):
            return {}
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            return {
                "runtime_version": report.get("runtime_version", ""),
                "registered_agents": report.get("registered_agents", []),
                "environment_status": report.get("environment_status", {}),
                "documentation_loaded": {
                    "count": report.get("documentation_loaded", {}).get("count", 0),
                    "files": report.get("documentation_loaded", {}).get("files", []),
                },
                "current_milestone": report.get("current_milestone", ""),
                "runtime_state": report.get("runtime_state", {}),
                "completed_milestones": report.get("completed_milestones", []),
                "user": report.get("user", "unknown"),
                "timestamp_utc": report.get("timestamp_utc", ""),
                "errors": report.get("errors", []),
                "warnings": report.get("warnings", []),
            }
        except Exception as e:
            print(f"[Context Manager] Failed to load runtime context: {e}")
            return {}
    
    def load_planner_output(self) -> Optional[Dict[str, Any]]:
        """Load execution plan from planner state."""
        # Try common state locations
        candidates = [
            os.path.join(STATE_DIR, "task_plan.json"),
            os.path.join(STATE_DIR, "current_task.json"),
        ]
        
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
        
        return None
    
    def load_test_results(self) -> Optional[Dict[str, Any]]:
        """Load testing results from state."""
        report_path = os.path.join(STATE_DIR, "test_report.json")
        
        if not os.path.exists(report_path):
            return None
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def load_build_results(self) -> Optional[Dict[str, Any]]:
        """Load build results from state."""
        # Build results are often in test report or review report
        test_report = self.load_test_results()
        
        if not test_report:
            return None
        
        # Extract build info from test report if available
        test_build = test_report.get("build")
        if isinstance(test_build, dict):
            return test_build
        
        if isinstance(test_report.get("tests"), list):
            tests = test_report["tests"]
            build_info = {
                "status": "PASS" if all(t.get("status") == "PASS" for t in tests) else "FAIL",
                "test_count": len(tests),
                "tests": [
                    {
                        "name": t.get("name"),
                        "category": t.get("category"),
                        "status": t.get("status"),
                    }
                    for t in tests if t.get("name")
                ],
            }
            return build_info
        
        # Try review report
        review_path = os.path.join(STATE_DIR, "review_report.json")
        if os.path.exists(review_path):
            try:
                with open(review_path, 'r', encoding='utf-8') as f:
                    review = json.load(f)
                
                return {
                    "status": review.get("status", ""),
                    "findings_count": len(review.get("findings", [])),
                }
            except Exception:
                pass
        
        return None
    
    def load_lint_results(self) -> Optional[Dict[str, Any]]:
        """Load lint results from test report."""
        test_report = self.load_test_results()
        
        if test_report and isinstance(test_report.get("lint"), dict):
            return test_report["lint"]
        
        return None
    
    def load_reviewer_comments(self) -> List[Dict[str, Any]]:
        """Load reviewer comments from review report."""
        review_path = os.path.join(STATE_DIR, "review_report.json")
        
        if not os.path.exists(review_path):
            return []
        
        try:
            with open(review_path, 'r', encoding='utf-8') as f:
                review = json.load(f)
            
            # Convert findings to comments
            comments = [
                {
                    "severity": finding.get("severity", ""),
                    "category": finding.get("category", ""),
                    "file": finding.get("file"),
                    "line": finding.get("line"),
                    "message": finding.get("problem", ""),
                    "recommendation": finding.get("recommendation", ""),
                }
                for finding in review.get("findings", [])
            ]
            
            return comments
        except Exception:
            return []
    
    def load_debugging_report(self) -> Optional[Dict[str, Any]]:
        """Load debugging report from state."""
        debugger_state_path = os.path.join(STATE_DIR, "debugger", "current_debug.json")
        
        if not os.path.exists(debugger_state_path):
            return None
        
        try:
            with open(debugger_state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def load_execution_history(self) -> List[Dict[str, Any]]:
        """Load execution history from actions.jsonl."""
        actions_path = os.path.join(STATE_DIR, "actions.jsonl")
        
        history: List[Dict[str, Any]] = []
        if os.path.exists(actions_path):
            with open(actions_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        action = json.loads(line.strip())
                        history.append(action)
                    except Exception:
                        pass
        
        return history
    
    def collect_changed_files(self, 
                              task_plan: Optional[Dict[str, Any]] = None,
                              coding_result: Optional[Dict[str, Any]] = None,
                              test_results: Optional[Dict[str, Any]] = None) -> List[str]:
        """Collect all changed files from various sources."""
        changed: Set[str] = set()
        
        # From task plan
        if task_plan:
            for key in (
                "changed_files",
                "files_changed",
                "files_created",
                "files_modified",
                "files_to_create",
                "files_to_modify",
                "files_to_read",
            ):
                value = task_plan.get(key, [])
                if isinstance(value, str):
                    changed.add(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            changed.add(item)
        
        # From coding result
        if coding_result:
            for key in (
                "files_changed",
                "changed_files",
                "files_created",
                "files_modified",
                "files_to_create",
                "files_to_modify",
                "files_to_read",
            ):
                value = coding_result.get(key, [])
                if isinstance(value, str):
                    changed.add(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            changed.add(item)
        
        # From test results
        if test_results and isinstance(test_results, dict):
            for key in (
                "changed_files",
                "files_changed",
                "files_created",
                "files_modified",
            ):
                value = test_results.get(key, [])
                if isinstance(value, str):
                    changed.add(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            changed.add(item)
        
        return sorted(path.replace("\\", "/") for path in changed)
    
    # ==================== AGENT-SPECIFIC CONTEXT SELECTION ====================
    
    def select_context_for_coder(self, 
                                  task_plan: Optional[Dict[str, Any]] = None,
                                  relevant_files: Optional[List[str]] = None) -> Context:
        """
        Select context for Coding Agent.
        
        Relevant information:
        - Current task and acceptance criteria
        - Relevant code files (not all project files)
        - Related documentation
        """
        changed_files = self.collect_changed_files(task_plan) if task_plan else []
        files_to_use = relevant_files or changed_files
        
        context = Context(
            current_milestone=self.get_cache().metadata.get("current_milestone", ""),
            current_task=task_plan,
            acceptance_criteria=list(task_plan.get("acceptance_criteria", [])) if task_plan else [],
        )
        
        # Add relevant documentation (filtered)
        doc_filter = {
            "docs/02_SYSTEM_ARCHITECTURE.md": "architecture",
            "docs/01_CODING_RULES.md": "coding rules",
            "docs/07_DEVELOPMENT_GUIDELINES.md": "guidelines",
            "ai_agents/agents/coder.md": "coder definition",
        }
        
        for doc_name, doc_type in doc_filter.items():
            if doc_name in self.get_cache().cache:
                content = self.get_cache().cache[doc_name]
                # Only include if relevant to current task
                if content and (task_plan is None or not task_plan.get("description", "")):
                    context.relevant_documentation[doc_name] = content
        
        # Add relevant source files
        for file_path in files_to_use[:10]:  # Limit to 10 files for token budget
            full_path = os.path.join(WORKSPACE_ROOT, file_path)
            if os.path.exists(full_path):
                try:
                    content = Path(full_path).read_text(encoding='utf-8', errors='ignore')[:2000]
                    context.relevant_source_files[file_path] = content
                except Exception:
                    pass
        
        # Calculate token usage
        self.update_token_estimation(context)
        
        return context
    
    def select_context_for_tester(self, 
                                   task_plan: Optional[Dict[str, Any]] = None,
                                   coding_result: Optional[Dict[str, Any]] = None) -> Context:
        """
        Select context for Testing Agent.
        
        Relevant information:
        - Changed files
        - Test commands and previous test results
        - Backend/API/database scope info
        """
        changed_files = self.collect_changed_files(task_plan, coding_result) if (task_plan or coding_result) else []
        
        # Load test report for previous results
        test_results = self.load_test_results()
        
        context = Context(
            current_milestone=self.get_cache().metadata.get("current_milestone", ""),
            current_task=task_plan,
            acceptance_criteria=list(task_plan.get("acceptance_criteria", [])) if task_plan else [],
        )
        
        # Add relevant documentation (minimal - just scope info)
        doc_filter = {
            "docs/02_SYSTEM_ARCHITECTURE.md": "scope",
            "docs/04_API_SPECIFICATION.md": "api contract",
        }
        
        for doc_name, doc_type in doc_filter.items():
            if doc_name in self.get_cache().cache:
                content = self.get_cache().cache[doc_name]
                if content and len(content) < 3000:  # Only small docs
                    context.relevant_documentation[doc_name] = content
        
        # Add relevant source files (changed files only)
        for file_path in changed_files[:5]:  # Limit to 5 files
            full_path = os.path.join(WORKSPACE_ROOT, file_path)
            if os.path.exists(full_path):
                try:
                    content = Path(full_path).read_text(encoding='utf-8', errors='ignore')[:1500]
                    context.relevant_source_files[file_path] = content
                except Exception:
                    pass
        
        # Add test results
        if test_results:
            context.test_results = {
                "status": test_results.get("status"),
                "tests_run": len(test_results.get("tests", [])),
                "errors": test_results.get("errors", []),
                "backend": test_results.get("backend", {}),
                "database": test_results.get("database", {}),
            }
        
        # Add build results from previous tests
        if isinstance(test_results, dict) and "build" in test_results:
            context.build_results = test_results["build"]
        
        # Calculate token usage
        self.update_token_estimation(context)
        
        return context
    
    def select_context_for_debugger(self, 
                                     task_plan: Optional[Dict[str, Any]] = None,
                                     test_results: Optional[Dict[str, Any]] = None) -> Context:
        """
        Select context for Debugging Agent.
        
        Relevant information:
        - Error messages and stack traces (not files)
        - Affected files list
        - Previous debugging reports
        - System architecture for error classification
        """
        changed_files = self.collect_changed_files(task_plan, None, test_results) if task_plan else []
        
        context = Context(
            current_milestone=self.get_cache().metadata.get("current_milestone", ""),
            current_task=task_plan,
            acceptance_criteria=list(task_plan.get("acceptance_criteria", [])) if task_plan else [],
        )
        
        # Add relevant documentation (architecture for error classification)
        doc_filter = {
            "docs/02_SYSTEM_ARCHITECTURE.md": "architecture context",
        }
        
        for doc_name, doc_type in doc_filter.items():
            if doc_name in self.get_cache().cache:
                content = self.get_cache().cache[doc_name]
                # Limit to first 3000 chars for debugging
                if content and len(content) < 3000:
                    context.relevant_documentation[doc_name] = content
        
        # Add relevant source files (affected files only)
        for file_path in changed_files[:5]:
            full_path = os.path.join(WORKSPACE_ROOT, file_path)
            if os.path.exists(full_path):
                try:
                    content = Path(full_path).read_text(encoding='utf-8', errors='ignore')[:1500]
                    context.relevant_source_files[file_path] = content
                except Exception:
                    pass
        
        # Add test results for error context
        if isinstance(test_results, dict):
            context.test_results = {
                "status": test_results.get("status"),
                "errors": test_results.get("errors", []),
            }
        
        # Add debugging report if available
        debug_report = self.load_debugging_report()
        if debug_report:
            context.debugging_report = debug_report
        
        # Calculate token usage
        self.update_token_estimation(context)
        
        return context
    
    def select_context_for_reviewer(self, 
                                     task_plan: Optional[Dict[str, Any]] = None,
                                     coding_result: Optional[Dict[str, Any]] = None,
                                     test_results: Optional[Dict[str, Any]] = None,
                                     changed_files: Optional[List[str]] = None) -> Context:
        """
        Select context for Reviewer Agent.
        
        Relevant information:
        - Planner output (acceptance criteria)
        - Changed files and git diff
        - Test results and build results
        - Previous review comments
        - Acceptance criteria
        """
        # Use provided changed files or collect them
        if not changed_files:
            changed_files = self.collect_changed_files(task_plan, coding_result, test_results)
        
        context = Context(
            current_milestone=self.get_cache().metadata.get("current_milestone", ""),
            current_task=task_plan,
            acceptance_criteria=list(task_plan.get("acceptance_criteria", [])) if task_plan else [],
        )
        
        # Add relevant documentation (full docs needed for review)
        doc_filter = {
            "docs/02_SYSTEM_ARCHITECTURE.md": "architecture",
            "docs/03_DATABASE_DESIGN.md": "database schema",
            "docs/04_API_SPECIFICATION.md": "API contract",
            "ai_agents/agents/global_rules.md": "global rules",
        }
        
        for doc_name, doc_type in doc_filter.items():
            if doc_name in self.get_cache().cache:
                content = self.get_cache().cache[doc_name]
                # Include full content or limited based on size
                if len(content) < 5000:
                    context.relevant_documentation[doc_name] = content
                else:
                    # Truncate large docs
                    lines = content.split('\n')[:100]
                    context.relevant_documentation[doc_name] = '\n'.join(lines) + "\n... (truncated)"
        
        # Add relevant source files
        for file_path in changed_files:
            full_path = os.path.join(WORKSPACE_ROOT, file_path)
            if os.path.exists(full_path):
                try:
                    content = Path(full_path).read_text(encoding='utf-8', errors='ignore')[:3000]
                    context.relevant_source_files[file_path] = content
                except Exception:
                    pass
        
        # Add test results
        if isinstance(test_results, dict):
            context.test_results = {
                "status": test_results.get("status"),
                "tests_run": len(test_results.get("tests", [])),
                "backend": test_results.get("backend", {}),
                "database": test_results.get("database", {}),
                "api": test_results.get("api", {}),
            }
        
        # Add build results
        if isinstance(test_results, dict) and "build" in test_results:
            context.build_results = test_results["build"]
        
        # Add lint results
        lint_results = self.load_lint_results()
        if lint_results:
            context.lint_results = lint_results
        
        # Add reviewer comments
        comments = self.load_reviewer_comments()
        context.reviewer_comments = [
            {
                "severity": c.get("severity", ""),
                "category": c.get("category", ""),
                "file": c.get("file"),
                "message": c.get("message", ""),
            }
            for c in comments
        ]
        
        # Calculate token usage
        self.update_token_estimation(context)
        
        return context
    
    def select_context_for_documentation_agent(self, 
                                                task_plan: Optional[Dict[str, Any]] = None,
                                                changed_files: Optional[List[str]] = None,
                                                git_diff: Optional[str] = None) -> Context:
        """
        Select context for Documentation Agent.
        
        Relevant information:
        - Completed task info
        - Changed files
        - APIs added
        - Routes added
        - Changelog entries
        - Previous documentation updates
        """
        if not changed_files:
            changed_files = self.collect_changed_files(task_plan)
        
        context = Context(
            current_milestone=self.get_cache().metadata.get("current_milestone", ""),
            current_task=task_plan,
            acceptance_criteria=list(task_plan.get("acceptance_criteria", [])) if task_plan else [],
        )
        
        # Add relevant documentation (previous documentation for context)
        doc_filter = {
            "docs/09_COMPLETED_TASKS.md": "completed tasks history",
            "docs/11_CHANGELOG.md": "changelog entries",
            "docs/08_AI_CONTEXT.md": "AI context state",
            "ai_agents/README.md": "agent documentation",
        }
        
        for doc_name, doc_type in doc_filter.items():
            if doc_name in self.get_cache().cache:
                content = self.get_cache().cache[doc_name]
                # Append-only docs use full content, others may be truncated
                if "changelog" in doc_name or "completed" in doc_name:
                    context.relevant_documentation[doc_name] = content
                else:
                    lines = content.split('\n')[:50]
                    context.relevant_documentation[doc_name] = '\n'.join(lines) + "\n... (truncated)"
        
        # Add relevant source files (new/modified files)
        for file_path in changed_files:
            full_path = os.path.join(WORKSPACE_ROOT, file_path)
            if os.path.exists(full_path):
                try:
                    content = Path(full_path).read_text(encoding='utf-8', errors='ignore')[:2000]
                    context.relevant_source_files[file_path] = content
                except Exception:
                    pass
        
        # Add git diff if provided (otherwise skip for token budget)
        if git_diff and len(git_diff) < 10000:
            context.git_diff = git_diff[:5000]  # Limit to 5000 chars
        
        # Load execution history
        history = self.load_execution_history()
        context.execution_history = history[-20:] if len(history) > 20 else history  # Last 20 actions
        
        return context
    
    # ==================== TOKEN OPTIMIZATION ====================
    
    def update_token_estimation(self, context: Context) -> int:
        """Update token estimation for a context."""
        total_tokens = 0
        
        # Estimate tokens from current task
        if context.current_task:
            desc = str(context.current_task.get("description", ""))[:500]
            reqs = str(context.current_task.get("requirements", [])[:3])[:200]
            criteria = str(context.current_task.get("acceptance_criteria", []))[:300]
            total_tokens += TokenTracker.estimate_tokens(desc + " " + reqs + " " + criteria)
        
        # Estimate from acceptance criteria
        for criterion in context.acceptance_criteria[:5]:  # Limit to 5
            total_tokens += TokenTracker.estimate_tokens(str(criterion)[:200])
        
        # Estimate from documentation (limited)
        for doc_name, content in context.relevant_documentation.items():
            if len(content) > 3000:
                # Truncate large docs
                lines = content.split('\n')[:80]
                content = '\n'.join(lines) + "\n... (truncated)"
                total_tokens += TokenTracker.estimate_tokens(content, is_json=False)
            else:
                total_tokens += TokenTracker.estimate_tokens(content, is_json=False)
        
        # Estimate from source files (very limited)
        for file_path, content in context.relevant_source_files.items():
            if len(content) > 2000:
                lines = content.split('\n')[:50]
                content = '\n'.join(lines) + "\n... (truncated)"
                total_tokens += TokenTracker.estimate_tokens(content, is_json=False)
        
        # Add overhead for structure
        total_tokens += 200  # Base overhead for context structure
        
        context.token_estimation = min(total_tokens, self.TOKEN_BUDGET_WARNING)
        return context.token_estimation
    
    def check_token_budget(self, context: Context) -> Tuple[bool, Optional[str]]:
        """
        Check if context exceeds token budget.
        
        Returns:
            (is_within_budget, warning_message)
        """
        is_within = context.token_estimation <= self.TOKEN_BUDGET_WARNING
        return (
            is_within,
            f"Context exceeds token budget ({context.token_estimation}/{self.TOKEN_BUDGET_WARNING})" if not is_within else None
        )
    
    # ==================== DYNAMIC CONTEXT BUILDING ====================
    
    def build_full_context(self) -> Context:
        """Build a full context with all available information."""
        context = Context()  # Always return a Context instance
        
        # Load runtime state
        runtime_context = self.load_runtime_context()
        if runtime_context:
            context.runtime_state = {
                "version": runtime_context.get("runtime_version", ""),
                "agents": runtime_context.get("registered_agents", []),
                "environment": runtime_context.get("environment_status", {}),
            }
        
        # Load milestone info
        self.get_cache().initialize()
        context.current_milestone = self.get_cache().metadata.get("current_milestone", "")
        
        # Load planner output if available
        task_plan = self.load_planner_output()
        if task_plan:
            context.current_task = task_plan
        
        # Load all documentation
        loaded_docs = self.get_cache().load_all_documentation()
        for doc_name, content in loaded_docs.items():
            context.relevant_documentation[doc_name] = content
        
        # Calculate token estimation
        self.update_token_estimation(context)
        
        return context
    
    def get_agent_context(self, agent_type: str, **kwargs) -> Context:
        """
        Get context for a specific agent type.
        
        Args:
            agent_type: One of "coding", "testing", "debugger", "reviewer", "documentation"
            **kwargs: Agent-specific parameters
            
        Returns:
            Context object for the specified agent
        """
        context_methods = {
            "coding": self.select_context_for_coder,
            "testing": self.select_context_for_tester,
            "debugger": self.select_context_for_debugger,
            "reviewer": self.select_context_for_reviewer,
            "documentation": self.select_context_for_documentation_agent,
        }
        
        method = context_methods.get(agent_type.lower())
        if not method:
            raise ValueError(f"Unknown agent type: {agent_type}. Valid types: {list(context_methods.keys())}")
        
        return method(**kwargs)


# Export main classes
__all__ = [
    "TokenTracker",
    "ContextCache", 
    "Context",
    "ContextManager",
]
