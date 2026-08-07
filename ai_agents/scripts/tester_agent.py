#!/usr/bin/env python3
"""
Testing Agent Runtime for Sanskriti AI Studio AI Agents.

This runtime verifies work produced by the Coding Agent by reading shared state,
selecting relevant validation commands, running them sequentially, and writing a
structured report to ai_agents/state/test_report.json.

CRITICAL: Qwen 3.5 is TEXT-ONLY. This runtime never sends images, screenshots,
image files, image URLs, or visual data to any text-only model.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
REPORT_PATH = os.path.join(STATE_DIR, "test_report.json")
ACTIONS_PATH = os.path.join(STATE_DIR, "actions.jsonl")

DEFAULT_TIMEOUT_SECONDS = 180
BUILD_TIMEOUT_SECONDS = 300


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


def load_text_file(path: str, limit: int = 20000) -> str:
    """Load text safely for definitions/docs without using visual inputs."""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read(limit)
    except OSError:
        return ""


def load_task_plan() -> Dict[str, Any]:
    """Read the current task plan from known shared-state locations."""
    candidates = [
        os.path.join(STATE_DIR, "task_plan.json"),
        os.path.join(STATE_DIR, "current_task.json"),
    ]
    for path in candidates:
        data = load_json_file(path)
        if data:
            data.setdefault("_source", path)
            return data
    return {
        "task_id": "manual-current-state",
        "description": "No task_plan.json/current_task.json found; testing current workspace state.",
        "requirements": [],
        "files_to_create": [],
        "files_to_modify": [],
        "_source": "fallback",
    }


def load_coding_result() -> Dict[str, Any]:
    """Read Coding Agent output from known state files or recent action logs."""
    for filename in ("coding_result.json", "coder_result.json", "code_report.json"):
        path = os.path.join(STATE_DIR, filename)
        data = load_json_file(path)
        if data:
            data.setdefault("_source", path)
            return data

    recent_coder_actions: List[Dict[str, Any]] = []
    if os.path.exists(ACTIONS_PATH):
        try:
            with open(ACTIONS_PATH, "r", encoding="utf-8") as file:
                for line in file:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event.get("agent") in {"coder", "coding_agent"}:
                        recent_coder_actions.append(event)
        except OSError:
            pass

    return {
        "status": "NOT_FOUND",
        "message": "No Coding Agent result file found; using task plan and workspace state.",
        "recent_actions": recent_coder_actions[-5:],
        "_source": "actions.jsonl/fallback",
    }


def record_action(action_type: str, details: Dict[str, Any]) -> None:
    """Append a Testing Agent action to ai_agents/state/actions.jsonl."""
    os.makedirs(STATE_DIR, exist_ok=True)
    action = {
        "agent": "tester",
        "action_type": action_type,
        "details": details,
        "timestamp": utc_now(),
    }
    with open(ACTIONS_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(action, ensure_ascii=False) + "\n")


def collect_changed_files(task_plan: Dict[str, Any], coding_result: Dict[str, Any]) -> List[str]:
    """Identify files changed or targeted by the Coding Agent/task plan."""
    changed: Set[str] = set()
    keys = (
        "files_changed",
        "changed_files",
        "files_created",
        "files_modified",
        "files_to_create",
        "files_to_modify",
        "files_to_read",
    )
    for source in (task_plan, coding_result):
        for key in keys:
            value = source.get(key, [])
            if isinstance(value, str):
                changed.add(value)
            elif isinstance(value, list):
                changed.update(str(item) for item in value if item)

    for event in coding_result.get("recent_actions", []):
        details = event.get("details", {})
        if isinstance(details, dict):
            for key in keys:
                value = details.get(key, [])
                if isinstance(value, str):
                    changed.add(value)
                elif isinstance(value, list):
                    changed.update(str(item) for item in value if item)

    return sorted(path.replace("\\", "/") for path in changed)


def project_file_exists(relative_path: str) -> bool:
    """Check whether a project file or directory exists."""
    return os.path.exists(os.path.join(WORKSPACE_ROOT, relative_path))


def command_available(executable: str) -> bool:
    """Return True when an executable is available on PATH."""
    return shutil.which(executable) is not None


def run_command(
    name: str,
    command: List[str],
    cwd: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    category: str = "general",
) -> Dict[str, Any]:
    """Run one validation command and capture stdout, stderr, and exit code."""
    started_at = utc_now()
    executable = command[0]
    resolved_executable = shutil.which(executable)
    if not resolved_executable:
        return {
            "name": name,
            "category": category,
            "command": " ".join(command),
            "cwd": cwd,
            "status": "FAIL",
            "exit_code": None,
            "stdout": "",
            "stderr": f"Command not found: {executable}",
            "started_at": started_at,
            "finished_at": utc_now(),
            "timeout_seconds": timeout,
        }

    try:
        resolved_command = [resolved_executable] + command[1:]
        completed = subprocess.run(
            resolved_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        status = "PASS" if completed.returncode == 0 else "FAIL"
        return {
            "name": name,
            "category": category,
            "command": " ".join(command),
            "cwd": cwd,
            "status": status,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
            "started_at": started_at,
            "finished_at": utc_now(),
            "timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "category": category,
            "command": " ".join(command),
            "cwd": cwd,
            "status": "FAIL",
            "exit_code": None,
            "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
            "stderr": f"Process timeout after {timeout} seconds.",
            "started_at": started_at,
            "finished_at": utc_now(),
            "timeout_seconds": timeout,
        }
    except OSError as exc:
        return {
            "name": name,
            "category": category,
            "command": " ".join(command),
            "cwd": cwd,
            "status": "FAIL",
            "exit_code": None,
            "stdout": "",
            "stderr": f"Process execution failed: {exc}",
            "started_at": started_at,
            "finished_at": utc_now(),
            "timeout_seconds": timeout,
        }


def status_for_categories(results: List[Dict[str, Any]], categories: Set[str], applicable: bool) -> Dict[str, str]:
    """Summarize multiple validation categories as one report section."""
    category_results = [item for item in results if item.get("category") in categories]
    if not applicable:
        return {"status": "NOT_APPLICABLE", "details": "Validation not applicable for changed files/task scope."}
    if not category_results:
        return {"status": "NOT_RUN", "details": "No validation command was selected for this category."}
    if all(item["status"] == "PASS" for item in category_results):
        return {"status": "PASS", "details": f"{len(category_results)} command(s) passed."}
    failed = [item for item in category_results if item["status"] != "PASS"]
    return {"status": "FAIL", "details": f"{len(failed)} of {len(category_results)} command(s) failed."}


def infer_scope(changed_files: List[str], task_plan: Dict[str, Any]) -> Dict[str, bool]:
    """Infer frontend/backend/database/API validation relevance."""
    text = " ".join(changed_files + [str(task_plan.get("description", ""))]).lower()
    frontend = any(path.startswith("frontend/") for path in changed_files) or "frontend" in text
    backend = any(path.startswith("backend/") for path in changed_files) or "backend" in text
    database = any(path.startswith("database/") for path in changed_files) or "database" in text or "db" in text
    api = backend or "api" in text or any("/api/" in path for path in changed_files)

    if not changed_files and task_plan.get("_source") == "fallback":
        frontend = project_file_exists("frontend/package.json")
        backend = project_file_exists("backend/pyproject.toml")
        database = False
        api = False

    return {"frontend": frontend, "backend": backend, "database": database, "api": api}


def build_validation_plan(scope: Dict[str, bool]) -> List[Dict[str, Any]]:
    """Create a safe sequential validation plan using existing project commands."""
    commands: List[Dict[str, Any]] = []
    frontend_dir = os.path.join(WORKSPACE_ROOT, "frontend")
    backend_dir = os.path.join(WORKSPACE_ROOT, "backend")

    if scope["backend"] and project_file_exists("backend/app/main.py"):
        commands.append({
            "name": "backend_startup_import",
            "category": "backend",
            "command": [sys.executable, "-c", "from app.main import app; print('Backend app import OK')"],
            "cwd": backend_dir,
        })
        commands.append({
            "name": "backend_pytest",
            "category": "backend",
            "command": [sys.executable, "-m", "pytest"],
            "cwd": backend_dir,
        })

    if scope["database"] and project_file_exists("backend/test_db.py"):
        commands.append({
            "name": "database_connection_script",
            "category": "database",
            "command": [sys.executable, "test_db.py"],
            "cwd": backend_dir,
        })

    if scope["api"] and project_file_exists("backend/app/main.py"):
        commands.append({
            "name": "api_route_import",
            "category": "api",
            "command": [sys.executable, "-c", "from app.main import app; print(len(app.routes)); print('API routes import OK')"],
            "cwd": backend_dir,
        })

    if scope["frontend"] and project_file_exists("frontend/package.json"):
        commands.append({
            "name": "frontend_lint",
            "category": "lint",
            "command": ["npm", "run", "lint"],
            "cwd": frontend_dir,
        })
        commands.append({
            "name": "frontend_build",
            "category": "build",
            "command": ["npm", "run", "build"],
            "cwd": frontend_dir,
            "timeout": BUILD_TIMEOUT_SECONDS,
        })

    return commands


def status_for_category(results: List[Dict[str, Any]], category: str, applicable: bool) -> Dict[str, str]:
    """Summarize a report section without falsely marking unrun checks PASS."""
    category_results = [item for item in results if item.get("category") == category]
    if not applicable:
        return {"status": "NOT_APPLICABLE", "details": "Validation not applicable for changed files/task scope."}
    if not category_results:
        return {"status": "NOT_RUN", "details": "No validation command was selected for this category."}
    if all(item["status"] == "PASS" for item in category_results):
        return {"status": "PASS", "details": f"{len(category_results)} command(s) passed."}
    failed = [item for item in category_results if item["status"] != "PASS"]
    return {"status": "FAIL", "details": f"{len(failed)} of {len(category_results)} command(s) failed."}


def extract_errors(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract concise failure summaries for orchestrator/coding feedback."""
    errors = []
    for item in results:
        if item.get("status") == "PASS":
            continue
        message = item.get("stderr") or item.get("stdout") or "Validation failed without output."
        errors.append({
            "test": item.get("name"),
            "category": item.get("category"),
            "exit_code": item.get("exit_code"),
            "message": message[-3000:],
        })
    return errors


def build_report(task_plan: Dict[str, Any], coding_result: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the final structured test report."""
    changed_files = collect_changed_files(task_plan, coding_result)
    scope = infer_scope(changed_files, task_plan)
    errors = extract_errors(results)
    any_failed = bool(errors)
    any_run = bool(results)
    overall = "FAIL" if any_failed else "PASS" if any_run else "PARTIAL"

    recommendations = []
    if any_failed:
        recommendations.append("Return failures to the Coding Agent/Orchestrator for diagnosis; Testing Agent does not auto-fix code.")
    if not any_run:
        recommendations.append("No validations were run because no applicable commands were selected from the current task scope.")

    return {
        "task_id": str(task_plan.get("task_id", "")),
        "status": overall,
        "timestamp": utc_now(),
        "task_plan_source": task_plan.get("_source", "unknown"),
        "coding_result_source": coding_result.get("_source", "unknown"),
        "changed_files": changed_files,
        "scope": scope,
        "tests": results,
        "backend": status_for_category(results, "backend", scope["backend"]),
        "database": status_for_category(results, "database", scope["database"]),
        "api": status_for_category(results, "api", scope["api"]),
        "frontend": status_for_categories(results, {"lint", "build"}, scope["frontend"]),
        "lint": status_for_category(results, "lint", scope["frontend"]),
        "build": status_for_category(results, "build", scope["frontend"]),
        "errors": errors,
        "recommendations": recommendations,
        "text_only_llm_check": {
            "images_sent_to_qwen_3_5": "NO",
            "image_input_added": "NO",
            "visual_analysis_attempted": "NO",
        },
    }


def save_report(report: Dict[str, Any]) -> None:
    """Persist ai_agents/state/test_report.json."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)


def process_task() -> Dict[str, Any]:
    """Execute the sequential Testing Agent workflow."""
    global_rules = load_text_file(os.path.join(AI_AGENTS_ROOT, "agents", "global_rules.md"))
    tester_definition = load_text_file(os.path.join(AI_AGENTS_ROOT, "agents", "tester.md"))
    task_plan = load_task_plan()
    coding_result = load_coding_result()
    changed_files = collect_changed_files(task_plan, coding_result)
    scope = infer_scope(changed_files, task_plan)
    validation_plan = build_validation_plan(scope)

    record_action("init", {
        "global_rules_loaded": bool(global_rules),
        "tester_definition_loaded": bool(tester_definition),
        "task_plan_source": task_plan.get("_source"),
        "coding_result_source": coding_result.get("_source"),
        "changed_files": changed_files,
        "scope": scope,
    })

    results = []
    for item in validation_plan:
        result = run_command(
            name=item["name"],
            command=item["command"],
            cwd=item["cwd"],
            timeout=item.get("timeout", DEFAULT_TIMEOUT_SECONDS),
            category=item["category"],
        )
        results.append(result)
        record_action("validation_command", {
            "name": result["name"],
            "category": result["category"],
            "status": result["status"],
            "exit_code": result["exit_code"],
        })

    report = build_report(task_plan, coding_result, results)
    save_report(report)
    record_action("report_saved", {"path": REPORT_PATH, "status": report["status"]})
    return report


def main() -> None:
    """CLI entry point for the Testing Agent Runtime."""
    print("=" * 60)
    print("TESTING AGENT RUNTIME - Sanskriti AI Studio")
    print("=" * 60)
    print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
    print("[INFO] Testing Agent observes and reports; it does not modify app code.")

    report = process_task()

    print("\n" + "=" * 60)
    print("TESTING AGENT PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Task ID: {report.get('task_id')}")
    print(f"Overall Status: {report.get('status')}")
    print(f"Commands Run: {len(report.get('tests', []))}")
    print(f"Report Saved: {REPORT_PATH}")
    if report.get("errors"):
        print("\nFailures:")
        for error in report["errors"]:
            print(f"- {error['test']} ({error['category']}), exit={error['exit_code']}")
    print("\nTEXT-ONLY LLM CHECK:")
    print("- Images sent to Qwen 3.5: NO")
    print("- Image input added: NO")
    print("- Visual analysis attempted: NO")


if __name__ == "__main__":
    main()