#!/usr/bin/env python3
"""
Review / Code Quality Agent Runtime - STEP 23.7 AUTONOMOUS VISUAL REVIEWER

Complete implementation consuming all reports:
- Code Review (from Coding Agent)
- Unit Test Results (from Testing Agent)  
- Vision Analysis Report (from Vision Pipeline)
- UI Validation Report (from UI Validation Engine)

Produces unified PASS/NEEDS_CHANGES/FAIL decision with comprehensive findings.

CRITICAL: Qwen 3.5 is TEXT-ONLY. This runtime never sends images or visual data
to the text-only model. All visual analysis is done by separate Vision Pipeline.

STEP 23.7 IMPLEMENTATION SUMMARY:
=================================
Phase 1 - Review Inputs: Load all reports (coding, test, vision, UI validation)
Phase 2 - Review Logic: Synthesize findings into unified decision  
Phase 3 - Issue Classification: Categorize issues by severity and category
Phase 4 - Final Report: Generate comprehensive report with all sections
Phase 5 - Debugging Integration: Send FAIL results to Debugging Agent
Phase 6 - History: Store review in ai_agents/state/review_history.jsonl
Phase 7 - Documentation: Update docs/02_SYSTEM_ARCHITECTURE.md, docs/08_AI_CONTEXT.md, docs/11_CHANGELOG.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
ACTIONS_PATH = os.path.join(STATE_DIR, "actions.jsonl")
REPORT_PATH = os.path.join(STATE_DIR, "review_report.json")
REVIEW_HISTORY_PATH = os.path.join(STATE_DIR, "review_history.jsonl")

MAX_FILE_CHARS = 12000
MAX_DIFF_CHARS = 24000
MAX_DOC_CHARS = 8000
MAX_MODEL_RESPONSE_CHARS = 8000

REVIEW_STATUSES = {"PASS", "NEEDS_CHANGES", "FAIL"}
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
CATEGORIES = {
    "CORRECTNESS", "ARCHITECTURE", "CODE_QUALITY", "BACKEND", "FRONTEND",
    "DATABASE", "API", "SECURITY", "TESTING", "DOCUMENTATION", "VISION", "UI_VALIDATION",
}

TEXT_ONLY_IMAGE_MARKERS = ("data:image/", "<image", "![](", "image_url")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_rel_path(path: str) -> Optional[str]:
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return None
    absolute = os.path.abspath(os.path.join(WORKSPACE_ROOT, normalized))
    workspace = os.path.abspath(WORKSPACE_ROOT)
    if not absolute.startswith(workspace):
        return None
    return normalized


def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            data.setdefault("_source", path)
            return data
        return {"value": data, "_source": path}
    except (json.JSONDecodeError, OSError) as exc:
        return {"_load_error": f"Could not read {path}: {exc}", "_source": path}


def load_text_file(path: str, limit: int = MAX_DOC_CHARS) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read(limit)
    except (UnicodeDecodeError, OSError):
        return ""


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {"agent": "reviewer", "action_type": action_type, "details": details, "timestamp": utc_now()}
    with open(ACTIONS_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def load_task_plan() -> Dict[str, Any]:
    for filename in ("task_plan.json", "current_task.json"):
        data = load_json_file(os.path.join(STATE_DIR, filename))
        if data:
            return data
    return {"task_id": "manual-current-state", "description": "", "requirements": [],
            "acceptance_criteria": [], "files_to_create": [], "files_to_modify": [], "_source": "fallback"}


def load_coding_result() -> Dict[str, Any]:
    for filename in ("coding_result.json", "coder_result.json", "code_report.json"):
        data = load_json_file(os.path.join(STATE_DIR, filename))
        if data:
            return data
    return {"status": "NOT_FOUND", "message": "", "_source": "fallback"}


def load_test_report() -> Dict[str, Any]:
    """Testing Agent results (unit tests, browser tests, lint, build)."""
    data = load_json_file(os.path.join(STATE_DIR, "test_report.json"))
    if data:
        return data
    return {"status": "NOT_RUN", "message": "", "tests": [], "errors": [], "_source": "fallback"}


def load_vision_report() -> Dict[str, Any]:
    """Vision Pipeline results (visual analysis of screenshots) - STEP 23.7 Input."""
    data = load_json_file(os.path.join(STATE_DIR, "vision_report.json"))
    if data:
        return data
    return {"status": "NOT_AVAILABLE", "message": "",
            "session_id": "", "screenshot_id": "", "url": "", "summary": "",
            "detected_components": [], "missing_components": [], "ocr_text": "",
            "visual_issues": [], "warnings": [], "suggested_improvements": [], "_source": "fallback"}


def load_ui_validation_report() -> Dict[str, Any]:
    """UI Validation Engine results (expected vs actual UI comparison) - STEP 23.7 Input."""
    data = load_json_file(os.path.join(STATE_DIR, "ui_validation_report.json"))
    if data:
        return data
    return {"status": "NOT_AVAILABLE", "message": "",
            "validation_id": "", "milestone_id": "", "task_id": "", "page_name": "",
            "status": "", "score": 0.0, "satisfied_rules": [], "failed_rules": [],
            "warnings": [], "recommendations": [], "_source": "fallback"}


def load_review_input(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    absolute = path if os.path.isabs(path) else os.path.join(WORKSPACE_ROOT, path)
    return load_json_file(absolute) or {"_load_error": f"Review input not found: {path}"}


def collect_paths_from_value(value: Any) -> Set[str]:
    paths: Set[str] = set()
    if isinstance(value, str):
        normalized = safe_rel_path(value)
        if normalized:
            paths.add(normalized)
    elif isinstance(value, list):
        for item in value:
            paths.update(collect_paths_from_value(item))
    elif isinstance(value, dict):
        for key in ("file", "path", "filename", "relative_path"):
            paths.update(collect_paths_from_value(value.get(key)))
    return paths


def collect_changed_files(*sources: Dict[str, Any]) -> List[str]:
    keys = ("changed_files", "files_changed", "files_created", "files_modified",
            "files_reviewed", "files_to_create", "files_to_modify", "files_to_read",
            "documentation_changes")
    changed: Set[str] = set()
    for source in sources:
        for key in keys:
            changed.update(collect_paths_from_value(source.get(key)))
    return sorted(path for path in changed if os.path.isfile(os.path.join(WORKSPACE_ROOT, path)))


def load_relevant_source(files: Iterable[str]) -> Dict[str, str]:
    source: Dict[str, str] = {}
    ignored_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".avi", ".wav", ".mp3"}
    for rel_path in files:
        _, extension = os.path.splitext(rel_path.lower())
        if extension in ignored_extensions:
            source[rel_path] = "[Skipped media/binary file. Qwen 3.5 is TEXT-ONLY]"
            continue
        content = load_text_file(os.path.join(WORKSPACE_ROOT, rel_path), limit=MAX_FILE_CHARS)
        if content:
            source[rel_path] = content
    return source


def collect_git_diff(include_git_diff: bool) -> str:
    if not include_git_diff:
        return ""
    try:
        completed = subprocess.run(["git", "diff", "--", "ai_agents"], cwd=WORKSPACE_ROOT,
                                   capture_output=True, text=True, timeout=30, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"[Git diff unavailable: {exc}]"
    if completed.returncode != 0:
        return f"[Git diff failed: {completed.stderr[-2000:]}]"
    return completed.stdout[:MAX_DIFF_CHARS]


def load_project_documentation() -> Dict[str, str]:
    docs = {
        "docs/01_AGENTS.md": os.path.join(WORKSPACE_ROOT, "docs", "01_AGENTS.md"),
        "docs/02_ARCHITECTURE.md": os.path.join(WORKSPACE_ROOT, "docs", "02_ARCHITECTURE.md"),
        "docs/03_DATABASE.md": os.path.join(WORKSPACE_ROOT, "docs", "03_DATABASE.md"),
        "docs/04_API.md": os.path.join(WORKSPACE_ROOT, "docs", "04_API.md"),
        "docs/07_AI_RULES.md": os.path.join(WORKSPACE_ROOT, "docs", "07_AI_RULES.md"),
    }
    return {name: load_text_file(path, limit=MAX_DOC_CHARS) for name, path in docs.items() if os.path.exists(path)}


def infer_scope(changed_files: List[str], task_plan: Dict[str, Any], review_input: Dict[str, Any]) -> Dict[str, bool]:
    text = " ".join(changed_files + [str(task_plan.get("description", "")), str(review_input.get("task_description", ""))]).lower()
    return {
        "backend": any(path.startswith("backend/") for path in changed_files) or "backend" in text or "fastapi" in text,
        "frontend": any(path.startswith("frontend/") for path in changed_files) or "frontend" in text or "react" in text,
        "database": any(path.startswith(("database/", "backend/app/models", "backend/app/repositories")) for path in changed_files) or "database" in text or "migration" in text,
        "api": any("/api/" in path or path.startswith("backend/app/api") for path in changed_files) or "api" in text,
        "documentation": any(path.startswith(("docs/", "ai_agents/README")) or path.endswith(".md") for path in changed_files) or "documentation" in text,
        "agent_runtime": any(path.startswith("ai_agents/") for path in changed_files) or "agent" in text,
    }


def validate_text_only_payload(payload: Any) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for marker in TEXT_ONLY_IMAGE_MARKERS:
        if marker in serialized:
            raise ValueError(f"TEXT-ONLY VIOLATION: image marker detected: {marker}")


def redact_sensitive_text(text: str) -> str:
    return re.sub(r"(?i)(api[_-]?key|secret|token|password|bearer)[\s:\-=]*[^\s'\"]{8,}",
                   lambda m: f"{m.group(1).lower().replace(' ', '_')}***REDACTED***", text)


def first_matching_line(content: str, pattern: re.Pattern[str]) -> Optional[int]:
    for index, line in enumerate(content.splitlines(), start=1):
        if pattern.search(line):
            return index
    return None


def first_text_line(content: str, needle: str) -> Optional[int]:
    for index, line in enumerate(content.splitlines(), start=1):
        if needle in line:
            return index
    return None
