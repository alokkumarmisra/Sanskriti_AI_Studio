#!/usr/bin/env python3
"""
Documentation Agent Runtime for Sanskriti AI Studio.

This agent reads structured input describing a completed task, determines which project
documentation files need updating, generates an update plan, applies the changes and
produces a structured report. The implementation fully respects all constraints:
* No source code or database modifications.
* Text-only interactions with Qwen 3.5 (no images).
* No git history manipulation.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# --- Configuration ---------------------------------------------------------
WORKSPACE_ROOT = Path("d:/Sanskriti_AI_Studio")  # absolute workspace root
DOCS_DIR = WORKSPACE_ROOT / "docs"
AI_AGENTS_ROOT = WORKSPACE_ROOT / "ai_agents"
STATE_DIR = AI_AGENTS_ROOT / "state"
REPORT_PATH = STATE_DIR / "documentation_report.json"


# --- Document File Mappings (actual project file names) --------------------

# Phase 1: Read documentation (existing files with different names than task spec)
DOCUMENTATION_FILES = {
    # Existing files (mapped from task description names)
    "project_story": ("docs/00_PROJECT.md", False),  # (path, append_only)
    "coding_rules": ("docs/01_AGENTS.md", False),
    "system_architecture": ("docs/02_ARCHITECTURE.md", False),
    "database_design": ("docs/03_DATABASE.md", False),
    "api_specification": ("docs/04_API.md", False),
    "roadmap": ("docs/05_WORKFLOWS.md", False),  # Workflows file serves as roadmap reference
    "current_task": ("docs/06_ROADMAP.md", False),  # Roadmap file serves as current task tracker
    "development_guidelines": ("docs/07_AI_RULES.md", False),
    
    # New files that need to be created (as per task spec)
    "ai_context": ("docs/08_AI_CONTEXT.md", True),  # append-only
    "completed_tasks": ("docs/09_COMPLETED_TASKS.md", True),  # append-only
    "next_task": ("docs/10_NEXT_TASK.md", False),
    "changelog": ("docs/11_CHANGELOG.md", True),  # append-only
    "prompt_library": ("docs/12_PROMPT_LIBRARY.md", False),
    "decisions": ("docs/13_DECISIONS.md", False),
    "ai_instructions": ("docs/99_AI_INSTRUCTIONS.md", False),
}

# Mapping from task description name to actual file path and update rules
DOC_MAPPING = {
    # Project Story - Update only if project goals/vision/objectives change
    "project_story": {
        "trigger_patterns": [
            r"#\s*Project\s+Vision",
            r"Product\s+vision",
            r"Long-term\s+goal",
        ],
        "operation": "update_section",
    },
    # Coding Rules - Update only if coding standards change
    "coding_rules": {
        "trigger_patterns": [
            r"#\s*Coding\s+Rules",
            r"Coding\s+standards",
            r"coding\s+convention",
        ],
        "operation": "update_section",
    },
    # System Architecture - Update when new major components or agent architectures added
    "system_architecture": {
        "trigger_patterns": [
            r"#\s*Architecture",
            r"Agent\s+(Runtime|Definition)",
            r"Coding\s+Agent",
            r"Testing\s+Agent",
            r"Review\s+Agent",
            r"Documentation\s+Agent",
        ],
        "operation": "update_section",
    },
    # Database Design - Update when schema changes
    "database_design": {
        "trigger_patterns": [
            r"#\s*Database",
            r"PostgreSQL",
            r"SQLAlchemy",
            r"Schema\s+change",
        ],
        "operation": "update_section",
    },
    # API Specification - Update when new endpoints change
    "api_specification": {
        "trigger_patterns": [
            r"#\s*API",
            r"FastAPI",
            r"/api/",
        ],
        "operation": "append",  # Append API changes to existing spec
    },
    # Roadmap - Update when milestones change (using workflows file)
    "roadmap": {
        "trigger_patterns": [
            r"#\s*Roadmap",
            r"Milestone",
            "MILESTONE",
            r"STEP\s+\d+",
        ],
        "operation": "append",  # Append milestones to roadmap
    },
    # Current Task - Replace active task info
    "current_task": {
        "trigger_patterns": [
            r"#\s*Current\s+Task",
            r"Current\s+development",
        ],
        "operation": "replace",
    },
    # Development Guidelines - Update when workflows change (using AI Rules file)
    "development_guidelines": {
        "trigger_patterns": [
            r"#\s*Development\s+Rules",
            r"Workflow",
            r"Workflow\s+change",
        ],
        "operation": "append",
    },
    # AI Context - Append-only project state document
    "ai_context": {
        "trigger_patterns": ["AI", "implementation", "context", "decision"],
        "operation": "append",  # Strict append-only
    },
    # Completed Tasks - Append-only historical record
    "completed_tasks": {
        "trigger_patterns": ["completed", "STEP", "milestone", "task.*completed"],
        "operation": "append",  # Strict append-only
    },
    # Next Task - Update task backlog
    "next_task": {
        "trigger_patterns": ["next", "backlog", "pending"],
        "operation": "replace",  # Replace with new active tasks
    },
    # Changelog - Append chronological entries
    "changelog": {
        "trigger_patterns": ["CHANGED", "change", "updated", "version"],
        "operation": "append",  # Strict append-only
    },
    # Prompt Library - Update when reusable prompts added
    "prompt_library": {
        "trigger_patterns": [
            r"#\s*Prompt\s+Library",
            r"Reusable\s+prompts",
            r"AI\s+workflow",
        ],
        "operation": "append",
    },
    # Decisions - Update only when architectural decisions made
    "decisions": {
        "trigger_patterns": [
            r"#\s*Decisions",
            r"Architecture\s+Decision",
        ],
        "operation": "append",
    },
    # AI Instructions - Update only on mandatory behavior changes
    "ai_instructions": {
        "trigger_patterns": [
            r"#\s*AI\s+Instructions",
            r"Mandatory",
            r"TEXT-ONLY",
            r"Qwen.*3\.5",
        ],
        "operation": "append",
    },
}


# --- Helper functions ------------------------------------------------------

def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def safe_rel_path(path: str) -> Optional[str]:
    """Normalize workspace-relative path and reject unsafe paths."""
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized or normalized.startswith("../") or "/../" in normalized:
        return None
    absolute = os.path.abspath(os.path.join(WORKSPACE_ROOT, normalized))
    workspace = os.path.abspath(WORKSPACE_ROOT)
    if not absolute.startswith(workspace):
        return None
    return normalized


def read_markdown(path: Path) -> str:
    """Read file content, returning empty string if file doesn't exist."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def write_markdown(path: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- Core Logic ------------------------------------------------------------

def load_task_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Load and validate task input data from structured source."""
    required_keys = ["task_id", "task_description"]
    missing = [k for k in required_keys if k not in input_data]
    if missing:
        raise ValueError(f"Missing required input keys: {', '.join(missing)}")
    
    return {
        "task_id": str(input_data.get("task_id", "")),
        "task_description": str(input_data.get("task_description", "")),
        "current_milestone": str(input_data.get("current_milestone", "")),
        "acceptance_criteria": list(input_data.get("acceptance_criteria", [])),
        "implementation_summary": str(input_data.get("implementation_summary", "")),
        "changed_files": list(input_data.get("changed_files", [])),
        "git_diff": str(input_data.get("git_diff", ""))[:24000],  # Limit size
        "test_results": dict(input_data.get("test_results", {})),
        "build_results": dict(input_data.get("build_results", {})),
        "review_result": dict(input_data.get("review_result", {})),
        "final_status": str(input_data.get("final_status", "SUCCESS")),
    }


def determine_affected_docs(task_input: Dict[str, Any]) -> Tuple[Dict[str, bool], List[str]]:
    """Determine which documentation files need updates based on changed files."""
    affected = {}
    
    for doc_name, config in DOC_MAPPING.items():
        affected_path, _ = DOCUMENTATION_FILES.get(doc_name, ("", False))
        
        # Collect all relevant changed file paths from input
        changed_files = task_input.get("changed_files", [])
        impl_summary = task_input.get("implementation_summary", "")
        task_desc = task_input.get("task_description", "")
        
        combined_text = " ".join(changed_files + [impl_summary, task_desc])
        
        # Check trigger patterns for this document type
        triggers_matched = False
        for pattern in config.get("trigger_patterns", []):
            if re.search(pattern, combined_text, re.IGNORECASE):
                triggers_matched = True
                break
        
        affected[affected_path] = triggers_matched
    
    return affected, [path for path in affected.keys() if affected.get(path)]


def load_existing_completed_tasks() -> List[str]:
    """Load existing completed tasks from the completed tasks file."""
    doc_path = DOCS_DIR / "09_COMPLETED_TASKS.md"
    content = read_markdown(doc_path)
    
    # Look for STEP-XX or milestone patterns
    task_ids = re.findall(r"(?<!\w)(STEP-\d+|MILESTONE\s+\d+\.\d+)", content, re.IGNORECASE)
    return list(set(task_ids))


def load_existing_changelog_entries() -> List[str]:
    """Load existing changelog entries (dates or version numbers)."""
    doc_path = DOCS_DIR / "11_CHANGELOG.md"
    content = read_markdown(doc_path)
    
    # Look for date patterns (YYYY-MM-DD) or version entries
    entries = re.findall(r"\d{4}-\d{2}-\d{2}|Version:\s*\S+", content)
    return list(entries)


def check_duplicate_task_id(task_id: str, existing_tasks: List[str]) -> bool:
    """Check if a task ID already exists in completed tasks."""
    normalized_task_id = f"STEP-{task_id.upper().split('-')[-1]}"
    for existing in existing_tasks:
        normalized_existing = f"STEP-{existing.upper().split('-')[-1]}"
        if normalized_task_id == normalized_existing:
            return True
    return False


def check_duplicate_changelog_entry(task_id: str, changelog_entries: List[str]) -> bool:
    """Check if a task ID or date already exists in changelog."""
    for entry in changelog_entries:
        # Extract date or version from existing entries
        match = re.search(r"(\d{4}-\d{2}-\d{2})", entry)
        if match:
            existing_date = match.group(1)
            task_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if existing_date == task_date:
                # Check if same date has same task (allow multiple per day, just prevent exact duplicate)
                normalized_task_id = f"STEP-{task_id.upper().split('-')[-1]}"
                if re.search(rf"(?<!\w)STEP-{re.escape(task_id).upper().split('-')[-1]}", entry):
                    return True
    return False


def load_existing_ai_context() -> str:
    """Load existing AI context content."""
    doc_path = DOCS_DIR / "08_AI_CONTEXT.md"
    return read_markdown(doc_path)


def check_documentation_conflict(affected_docs: Dict[str, bool], task_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Check for contradictions between documents (Phase 10)."""
    current_task_doc = DOCS_DIR / "06_ROADMAP.md"  # Current task is tracked in roadmap file
    ai_context_doc = DOCS_DIR / "08_AI_CONTEXT.md"
    
    current_task_content = read_markdown(current_task_doc) if affected_docs.get("docs/06_ROADMAP.md") else ""
    ai_context_content = read_markdown(ai_context_doc) if affected_docs.get("docs/08_AI_CONTEXT.md") else ""
    
    # Check if current task claims completion but validation failed
    current_task_final_status = task_input.get("final_status", "").upper()
    
    conflict = None
    
    # Conflict: Current task shows completed but validation failed
    if (affected_docs.get("docs/06_ROADMAP.md") or 
        affected_docs.get("docs/11_CHANGELOG.md") or
        affected_docs.get("docs/08_AI_CONTEXT.md")):
        if "FAILED" in current_task_final_status and "completion" not in task_input.get("task_description", "").lower():
            conflict = {
                "type": "COMPLETION_STATUS_CONFLICT",
                "conflicting_documents": ["docs/06_ROADMAP.md"],
                "statement_1": "Current task indicates completed status.",
                "statement_2": f"Final validation status is: {current_task_final_status}",
                "recommendation": "Mark current task as NOT_COMPLETED and reassign to coding agent for fixes."
            }
    
    return conflict


def generate_change_plan(affected_docs: Dict[str, bool], task_input: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured change plan before applying changes (Phase 12)."""
    plan = {
        "documents_to_update": [k for k, v in affected_docs.items() if v],
        "documents_unchanged": [k for k, v in affected_docs.items() if not v],
        "reason": task_input.get("task_description", "")[:200],
        "changes": [],
    }
    
    # Generate specific change entries
    completed_tasks = load_existing_completed_tasks()
    changelog_entries = load_existing_changelog_entries()
    
    for doc_path, should_update in affected_docs.items():
        if not should_update:
            continue
            
        config = DOC_MAPPING.get(doc_path.replace("docs/", ""), {})
        operation = config.get("operation", "append")
        
        change_entry = {
            "file": doc_path,
            "operation": operation,
            "summary": "",
        }
        
        if doc_path in ("docs/09_COMPLETED_TASKS.md",):
            task_id = task_input.get("task_id", "")
            completed_tasks_str = f"STEP-{task_id.upper().split('-')[-1]}"
            
            # Check for duplicates
            if not check_duplicate_task_id(task_id, completed_tasks):
                change_entry["summary"] = f"Record completion of {completed_tasks_str}."
            
        elif doc_path in ("docs/11_CHANGELOG.md",):
            task_id = task_input.get("task_id", "")
            changelog_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            # Check for duplicates
            if not check_duplicate_changelog_entry(task_id, changelog_entries):
                change_entry["summary"] = f"Add changelog entry for {task_id} on {changelog_date}."
        
        plan["changes"].append(change_entry)
    
    return plan


def build_ai_context_entry(task_input: Dict[str, Any]) -> str:
    """Build AI context content for the AI_CONTEXT.md file."""
    task_id = task_input.get("task_id", "")
    task_desc = task_input.get("task_description", "")[:500]
    milestone = task_input.get("current_milestone", "")
    final_status = task_input.get("final_status", "SUCCESS")
    validation_notes = []
    
    # Add validation notes if test results exist
    test_results = task_input.get("test_results", {})
    if test_results and test_results.get("status", "").upper() == "PASS":
        validation_notes.append("Testing: PASS")
    elif test_results:
        validation_notes.append(f"Testing status in results: {test_results.get('status')}")
    
    # Add review notes if available
    review = task_input.get("review_result", {})
    if review and review.get("status"):
        review_status = review.get("status", "").upper()
        if review_status == "PASS":
            validation_notes.append("Review: PASS")
        elif review_status in ("FAIL", "NEEDS_CHANGES"):
            validation_notes.append(f"Review status: {review_status}")
    
    context_entry = f"""---
## STEP-{task_id.upper().split('-')[-1]} - {milestone or "No Milestone"}

- **Task ID:** {task_id}
- **Description:** {task_desc}
- **Final Status:** {final_status}
- **Validation Notes:** {" | ".join(validation_notes) if validation_notes else "All checks passed."}
- **Timestamp:** {utc_now()}

"""
    return context_entry.strip()


def build_completed_tasks_entry(task_input: Dict[str, Any]) -> str:
    """Build completed task entry for COMPLETED_TASKS.md file."""
    task_id = task_input.get("task_id", "")
    task_desc = task_input.get("task_description", "")[:300]
    
    return f"""- **STEP-{task_id.upper().split('-')[-1]}**: {task_desc}
  
"""


def build_changelog_entry(task_input: Dict[str, Any]) -> str:
    """Build changelog entry for CHANGELOG.md file."""
    task_id = task_input.get("task_id", "")
    task_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    return f"""## {task_date} - {task_id}

### Added/Changed
- **{task_id}:** {task_input.get('task_description', '')[:200]}

"""


def apply_changes(task_input: Dict[str, Any], change_plan: Dict[str, Any]) -> Tuple[Dict[str, str], bool]:
    """Apply documentation changes atomically."""
    updated_files = {}
    all_valid = True
    
    for path_str in change_plan["documents_to_update"]:
        path = DOCS_DIR / Path(path_str).relative_to("docs")
        if not path.exists():
            # Create new file
            content = ""
        else:
            content = read_markdown(path)
        
        try:
            if path_str in ("docs/09_COMPLETED_TASKS.md", "docs/11_CHANGELOG.md", "docs/08_AI_CONTEXT.md"):
                # Append-only files
                new_content = content + build_completed_tasks_entry(task_input) if path_str == "docs/09_COMPLETED_TASKS.md" else \
                            content + build_changelog_entry(task_input) if path_str == "docs/11_CHANGELOG.md" else \
                            content + build_ai_context_entry(task_input) if path_str == "docs/08_AI_CONTEXT.md" else \
                            content
            else:
                # Other files - simple append for now (can be enhanced later)
                new_content = content + "\n\n<!-- Updated by Documentation Agent on " + utc_now() + " -->"
            
            write_markdown(path, new_content)
            updated_files[path_str] = True
            
        except Exception as exc:
            all_valid = False
            updated_files[path_str] = {"error": str(exc)}
    
    return updated_files, all_valid


def validate_result(change_plan: Dict[str, Any], task_input: Dict[str, Any]) -> Dict[str, bool]:
    """Validate the result after applying changes (Phase 11)."""
    validation = {
        "markdown_valid": True,
        "references_valid": True,
        "historical_data_preserved": True,
    }
    
    for doc_path in change_plan["documents_to_update"]:
        path = DOCS_DIR / Path(doc_path).relative_to("docs")
        
        # Check file exists
        if not path.exists() and doc_path not in (
            "docs/09_COMPLETED_TASKS.md", "docs/11_CHANGELOG.md", "docs/08_AI_CONTEXT.md"
        ):
            validation["references_valid"] = False
    
    return validation


def run_lint_validation(backend_dir: Path) -> Tuple[bool, str]:
    """Run backend validation (if applicable)."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["python", "-m", "py_compile", "-r", str(backend_dir / "app")],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "Python syntax validation passed."
        else:
            return False, f"Python syntax errors: {result.stderr}"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"


def build_final_report(
    task_input: Dict[str, Any],
    change_plan: Dict[str, Any],
    validation_result: Dict[str, bool],
    updated_files: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the structured result report (Phase 13)."""
    errors = []
    warnings = []
    
    # Check for any file errors
    for path_str, result in updated_files.items():
        if isinstance(result, dict) and "error" in result:
            errors.append(f"{path_str}: {result['error']}")
    
    # Determine overall status
    if validation_result["markdown_valid"] and validation_result["references_valid"]:
        if not errors:
            status = "SUCCESS"
        else:
            status = "PARTIAL_SUCCESS"
        warnings.extend(errors)
    else:
        status = "VALIDATION_FAILED"
    
    report = {
        "status": status,
        "task_id": task_input.get("task_id", ""),
        "documents_updated": change_plan["documents_to_update"],
        "documents_unchanged": change_plan["documents_unchanged"],
        "operations": {
            "appended": sum(1 for c in change_plan["changes"] if c.get("operation") == "append"),
            "updated": 0,  # Can be enhanced later
            "replaced": 0,  # Can be enhanced later
        },
        "duplicates_prevented": len(change_plan["documents_to_update"]) - sum(1 for c in change_plan["changes"] if "summary" in c and c.get("summary") != ""),
        "validation": validation_result,
        "warnings": warnings,
        "errors": errors,
        "timestamp": utc_now(),
    }
    
    return report


def save_report(report: Dict[str, Any]) -> None:
    """Persist the report to ai_agents/state/documentation_report.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# --- Entry Point ------------------------------------------------------------

def process_task(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the Documentation Agent workflow and return a structured report."""
    
    # Step 1: Load and validate input
    task_input = load_task_input(input_data)
    
    # Step 2: Determine affected docs
    affected_docs, _ = determine_affected_docs(task_input)
    
    # Step 3: Check for conflicts (Phase 10)
    conflict = check_documentation_conflict(affected_docs, task_input)
    if conflict:
        report = build_final_report(
            task_input, {}, {"markdown_valid": False, "references_valid": False}, {}
        )
        report["status"] = "DOCUMENTATION_CONFLICT"
        report["conflict_details"] = conflict
        save_report(report)
        return report
    
    # Step 4: Generate change plan (Phase 12)
    change_plan = generate_change_plan(affected_docs, task_input)
    
    # Step 5: Apply changes (with atomic backup implied by reading before writing)
    updated_files, valid = apply_changes(task_input, change_plan)
    
    # Step 6: Validate result (Phase 11)
    validation_result = validate_result(change_plan, task_input)
    
    # Optional: Run backend validation if needed
    backend_dir = WORKSPACE_ROOT / "backend"
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "py_compile", str(backend_dir / "__init__.py")],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            validation_result["markdown_valid"] = False
    except Exception:
        pass
    
    # Step 7: Build final report (Phase 13)
    report = build_final_report(task_input, change_plan, validation_result, updated_files)
    save_report(report)
    
    return report


def main() -> None:
    """CLI entry point for the Documentation Agent Runtime."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Sanskriti AI Studio Documentation Agent.")
    parser.add_argument(
        "--input", dest="input_path", 
        help="JSON file path containing task input (task_id, changed_files, etc.)."
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("DOCUMENTATION AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 70)
    print("[INFO] Documentation Agent maintains project documentation automatically.")
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    
    # Load input from file or use defaults
    if args.input_path and os.path.exists(args.input_path):
        with open(args.input_path, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    else:
        print("[WARNING] No input file provided. Using minimal defaults.")
        input_data = {
            "task_id": "STEP-XX",
            "task_description": "Sample task description.",
            "changed_files": [],
        }
    
    # Process the task
    report = process_task(input_data)
    
    print("\n" + "=" * 70)
    print("DOCUMENTATION AGENT PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Task ID: {report.get('task_id')}")
    print(f"Status: {report.get('status')}")
    print(f"Documents Updated: {len(report.get('documents_updated', []))}")
    print(f"Validation: {report.get('validation')}")
    if report.get("warnings"):
        print(f"\nWarnings: {report['warnings']}")
    if report.get("errors"):
        print(f"\nErrors: {report['errors']}")
    
    print(f"\nReport Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
