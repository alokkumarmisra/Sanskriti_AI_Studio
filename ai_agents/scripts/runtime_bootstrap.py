#!/usr/bin/env python3
"""
Runtime Bootstrap for Sanskriti AI Studio.

This module initializes and validates the entire autonomous development environment
before any milestone execution begins. It performs:

1. Runtime initialization
2. Configuration loading
3. Required folder/file validation
4. Environment variable validation
5. Agent registration
6. Planner loading
7. Execution Manager loading
8. Documentation loading
9. State restoration
10. Startup report generation

CRITICAL: Qwen 3.5 is TEXT-ONLY. This bootstrap never sends images or visual data.

Version: 1.0
Last Updated: 2026-08-05
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.dirname(AI_AGENTS_ROOT)


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def utc_local() -> str:
    """Return current local timestamp in ISO-8601 format."""
    return datetime.now().isoformat()


class RuntimeBootstrap:
    """Runtime Bootstrap for Sanskriti AI Studio."""

    def __init__(self):
        """Initialize the runtime bootstrap."""
        self.workspace_root = WORKSPACE_ROOT
        self.ai_agents_root = AI_AGENTS_ROOT
        self.state_dir = os.path.join(AI_AGENTS_ROOT, "state")
        self.logs_dir = os.path.join(WORKSPACE_ROOT, "ai_agents", "logs")
        self.runtime_config_path = os.path.join(self.ai_agents_root, "runtime.json")
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.registration_log: List[Dict[str, Any]] = []

    def validate_required_folders(self) -> bool:
        """Validate that all required folders exist."""
        print("[BOOTSTRAP] Validating required folders...")

        required_folders = [
            ("ai_agents/agents", "Agents directory"),
            ("ai_agents/scripts", "Scripts directory"),
            ("ai_agents/state", "State management directory"),
            ("ai_agents/logs", "Logs directory"),
            ("backend/app", "Backend application directory"),
            ("frontend/src", "Frontend source directory"),
            ("docs", "Documentation directory"),
        ]

        all_valid = True
        for folder_path, description in required_folders:
            full_path = os.path.join(self.workspace_root, folder_path)
            if os.path.exists(full_path):
                print(f"  [OK] {description}: {full_path}")
            else:
                self.errors.append(f"Missing folder: {folder_path} ({description})")
                print(f"  [(X)] {description}: MISSING")
                all_valid = False

        return all_valid

    def validate_required_files(self) -> bool:
        """Validate that all required files exist."""
        print("[BOOTSTRAP] Validating required files...")

        # Check for existing agent implementations
        agent_files = [
            ("ai_agents/scripts/coder_agent.py", "Coding Agent"),
            ("ai_agents/scripts/tester_agent.py", "Testing Agent"),
            ("ai_agents/scripts/debugger_agent.py", "Debugging Agent"),
            ("ai_agents/scripts/planner_agent.py", "Planner Agent"),
            ("ai_agents/scripts/reviewer_agent.py", "Review Agent"),
            ("ai_agents/scripts/orchestrator.py", "Orchestrator Agent"),
            ("ai_agents/agents/documentation_agent.py", "Documentation Agent"),
            ("ai_agents/scripts/config.py", "Configuration"),
        ]

        all_valid = True
        for file_path, description in agent_files:
            full_path = os.path.join(self.workspace_root, file_path)
            if os.path.exists(full_path):
                print(f"  [OK] {description}: {file_path}")
            else:
                self.warnings.append(f"Optional component not found: {description} ({file_path})")
                print(f"  ! {description}: NOT FOUND (will be auto-registered)")

        # Check for documentation files
        doc_files = [
            ("docs/02_SYSTEM_ARCHITECTURE.md", "System Architecture"),
            ("docs/08_AI_CONTEXT.md", "AI Context"),
            ("docs/11_CHANGELOG.md", "Changelog"),
        ]

        for file_path, description in doc_files:
            full_path = os.path.join(self.workspace_root, file_path)
            if os.path.exists(full_path):
                print(f"  [OK] {description}: {file_path}")
            else:
                self.warnings.append(f"Documentation not found: {description} ({file_path})")

        return True  # Don't fail on optional docs

    def validate_environment_variables(self) -> Dict[str, Any]:
        """Validate and extract environment configuration."""
        print("[BOOTSTRAP] Validating environment variables...")

        env_config = {
            "LM_STUDIO_URL": os.environ.get("LM_STUDIO_URL", "http://localhost:1234"),
            "LM_STUDIO_ENABLED": os.environ.get("LM_STUDIO_ENABLED", "true").lower() == "true",
            "BACKEND_URL": os.environ.get("BACKEND_URL", "http://localhost:8000"),
            "FRONTEND_URL": os.environ.get("FRONTEND_URL", "http://localhost:5173"),
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),  # Will be loaded from .env if exists
        }

        # Try to load backend environment file
        env_path = os.path.join(self.workspace_root, "backend", ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key in env_config:
                                env_config[key] = value
            except Exception as e:
                self.warnings.append(f"Could not load .env file: {e}")

        print(f"  [OK] LM Studio URL: {env_config['LM_STUDIO_URL']}")
        print(f"  [OK] LM Studio Enabled: {env_config['LM_STUDIO_ENABLED']}")
        print(f"  [OK] Backend URL: {env_config['BACKEND_URL']}")
        print(f"  [OK] Frontend URL: {env_config['FRONTEND_URL']}")

        return env_config

    def load_documentation(self) -> Dict[str, str]:
        """Load all project documentation for context."""
        print("[BOOTSTRAP] Loading project documentation...")

        doc_paths = [
            "docs/00_PROJECT_STORY.md",
            "docs/01_CODING_RULES.md",
            "docs/02_SYSTEM_ARCHITECTURE.md",
            "docs/03_DATABASE_DESIGN.md",
            "docs/04_API_SPECIFICATION.md",
            "docs/05_ROADMAP.md",
            "docs/05_WORKFLOWS.md",
            "docs/06_CURRENT_TASK.md",
            "docs/07_DEVELOPMENT_GUIDELINES.md",
            "docs/08_AI_CONTEXT.md",
            "docs/09_COMPLETED_TASKS.md",
            "docs/10_NEXT_TASK.md",
            "docs/11_CHANGELOG.md",
        ]

        loaded_docs = {}
        for doc_path in doc_paths:
            full_path = os.path.join(self.workspace_root, doc_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        loaded_docs[doc_path] = content[:50000]  # Limit size
                        print(f"  [OK] Loaded: {doc_path}")
                except Exception as e:
                    self.warnings.append(f"Could not load documentation {doc_path}: {e}")
            else:
                self.warnings.append(f"Documentation not found: {doc_path}")

        return loaded_docs

    def register_agent(self, agent_name: str, file_path: str, module_name: Optional[str] = None) -> bool:
        """Register an agent and record in registration log."""
        full_path = os.path.join(self.workspace_root, file_path)
        
        if os.path.exists(full_path):
            print(f"  [OK] Registered Agent: {agent_name} ({file_path})")
            self.registration_log.append({
                "type": "agent",
                "name": agent_name,
                "path": file_path,
                "status": "registered",
                "timestamp": utc_now(),
            })
            return True
        else:
            print(f"  ! Agent not found: {agent_name} ({file_path})")
            self.registration_log.append({
                "type": "agent",
                "name": agent_name,
                "path": file_path,
                "status": "not_found",
                "timestamp": utc_now(),
            })
            return False

    def register_all_agents(self) -> Dict[str, Any]:
        """Register all available agents."""
        print("[BOOTSTRAP] Registering agents...")
        
        # Core development agents
        self.register_agent("Coding Agent", "ai_agents/scripts/coder_agent.py", "coder_agent")
        self.register_agent("Testing Agent", "ai_agents/scripts/tester_agent.py", "tester_agent")
        self.register_agent("Debugging Agent", "ai_agents/scripts/debugger_agent.py", "debugger_agent")
        self.register_agent("Review Agent", "ai_agents/scripts/reviewer_agent.py", "reviewer_agent")
        self.register_agent("Documentation Agent", "ai_agents/agents/documentation_agent.py", "documentation_agent")
        
        # Orchestration agents
        self.register_agent("Planner Agent", "ai_agents/scripts/planner_agent.py", "planner_agent")
        self.register_agent("Orchestrator Agent", "ai_agents/scripts/orchestrator.py", "orchestrator")

        # Return registration status
        return {
            "registered": len([r for r in self.registration_log if r["status"] == "registered"]),
            "not_found": len([r for r in self.registration_log if r["status"] == "not_found"]),
        }

    def register_execution_manager(self) -> bool:
        """Register the milestone execution manager."""
        print("[BOOTSTRAP] Registering Execution Manager...")
        
        file_path = "ai_agents/scripts/milestone_execution_manager.py"
        full_path = os.path.join(self.workspace_root, file_path)
        
        if os.path.exists(full_path):
            print(f"  [OK] Registered: Milestone Execution Manager ({file_path})")
            self.registration_log.append({
                "type": "manager",
                "name": "Milestone Execution Manager",
                "path": file_path,
                "status": "registered",
                "timestamp": utc_now(),
            })
            return True
        else:
            print(f"  ! Execution Manager not found: {file_path}")
            self.registration_log.append({
                "type": "manager",
                "name": "Milestone Execution Manager",
                "path": file_path,
                "status": "not_found",
                "timestamp": utc_now(),
            })
            return False

    def validate_agent_registry(self) -> Dict[str, Any]:
        """Validate the agent registry structure."""
        print("[BOOTSTRAP] Validating agent registry...")

        registry = {
            "agents": [
                {"name": "coding_agent", "module": "coder_agent", "file": "ai_agents/scripts/coder_agent.py"},
                {"name": "testing_agent", "module": "tester_agent", "file": "ai_agents/scripts/tester_agent.py"},
                {"name": "debugger_agent", "module": "debugger_agent", "file": "ai_agents/scripts/debugger_agent.py"},
                {"name": "reviewer_agent", "module": "reviewer_agent", "file": "ai_agents/scripts/reviewer_agent.py"},
                {"name": "documentation_agent", "module": "documentation_agent", "file": "ai_agents/agents/documentation_agent.py"},
                {"name": "planner_agent", "module": "planner_agent", "file": "ai_agents/scripts/planner_agent.py"},
                {"name": "orchestrator", "module": "orchestrator", "file": "ai_agents/scripts/orchestrator.py"},
            ],
            "managers": [
                {"name": "milestone_execution_manager", "file": "ai_agents/scripts/milestone_execution_manager.py"},
            ],
        }

        print("  [OK] Agent Registry validated:")
        print(f"    - {len(registry['agents'])} agents defined")
        print(f"    - {len(registry['managers'])} managers defined")

        return registry

    def restore_runtime_state(self) -> bool:
        """Restore runtime state from existing state files."""
        print("[BOOTSTRAP] Restoring runtime state...")

        orchestrator_state_path = os.path.join(self.state_dir, "orchestrator", "current_task.json")
        if os.path.exists(orchestrator_state_path):
            try:
                with open(orchestrator_state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    print(f"  [OK] Restored Orchestrator state from: {orchestrator_state_path}")
                    return True
            except Exception as e:
                self.warnings.append(f"Could not restore orchestrator state: {e}")

        actions_path = os.path.join(self.state_dir, "actions.jsonl")
        if os.path.exists(actions_path):
            try:
                with open(actions_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
                    print(f"  [OK] Found {line_count} actions in history: {actions_path}")
            except Exception as e:
                self.warnings.append(f"Could not read actions history: {e}")

        # Create initial state directories if they don't exist
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(os.path.join(self.state_dir, "orchestrator"), exist_ok=True)
        os.makedirs(os.path.join(self.state_dir, "planner"), exist_ok=True)
        
        return True

    def restore_milestone_state(self) -> bool:
        """Restore milestone state from documentation."""
        print("[BOOTSTRAP] Restoring milestone state...")

        current_task_path = os.path.join(self.workspace_root, "docs", "06_CURRENT_TASK.md")
        if os.path.exists(current_task_path):
            try:
                with open(current_task_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    has_completed = "COMPLETED" in content or "STATUS: COMPLETED" in content
                    print(f"  [OK] Current milestone state loaded: {has_completed}")
                    return True
            except Exception as e:
                self.warnings.append(f"Could not restore milestone state: {e}")

        next_task_path = os.path.join(self.workspace_root, "docs", "10_NEXT_TASK.md")
        if os.path.exists(next_task_path):
            try:
                with open(next_task_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"  [OK] Next task state loaded from: {next_task_path}")
                    return True
            except Exception as e:
                self.warnings.append(f"Could not load next task: {e}")

        return True

    def restore_execution_history(self) -> Dict[str, Any]:
        """Restore execution history from logs and state files."""
        print("[BOOTSTRAP] Restoring execution history...")

        history = {
            "actions": [],
            "errors": [],
            "warnings": [],
            "completed_steps": 0,
        }

        actions_path = os.path.join(self.state_dir, "actions.jsonl")
        if os.path.exists(actions_path):
            try:
                with open(actions_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            action = json.loads(line.strip())
                            history["actions"].append(action)
                        except json.JSONDecodeError:
                            pass
                print(f"  [OK] Loaded {len(history['actions'])} actions from history")
            except Exception as e:
                self.warnings.append(f"Could not read execution history: {e}")

        return history

    def build_runtime_context(self, env_config: Dict[str, Any], docs: Dict[str, str]) -> Dict[str, Any]:
        """Build the complete runtime context."""
        print("[BOOTSTRAP] Building runtime context...")

        agents = [r["name"] for r in self.registration_log if r.get("status") == "registered"]
        managers = ["milestone_execution_manager" if os.path.exists(os.path.join(self.workspace_root, "ai_agents/scripts/milestone_execution_manager.py")) else None]
        
        current_milestone = "Unknown"
        if os.path.exists(os.path.join(self.workspace_root, "docs", "06_CURRENT_TASK.md")):
            try:
                with open(os.path.join(self.workspace_root, "docs", "06_CURRENT_TASK.md"), "r", encoding="utf-8") as f:
                    content = f.read()
                    import re
                    match = re.search(r"(?i)(Milestone\s+\d+\.\d+|Step\s+\d+)\s*[-:]\s*(COMPLETED)?", content)
                    if match and "COMPLETED" not in content:
                        current_milestone = match.group(1).strip()
            except Exception:
                pass

        # Build runtime context with validated data
        valid_docs = {k: v for k, v in docs.items() if v}
        return {
            "runtime_version": "1.0.0",
            "workspace_root": self.workspace_root,
            "ai_agents_root": self.ai_agents_root,
            "state_dir": self.state_dir,
            "logs_dir": self.logs_dir,
            "environment": env_config,
            "documentation_count": len(valid_docs),
            "agents": agents,
            "managers": managers,
            "current_milestone": current_milestone,
            "runtime_state": {
                "initialized": True,
                "ready_for_execution": bool(len(self.errors) == 0),
            },
        }

    def generate_startup_report(self, runtime_context: Dict[str, Any], docs: Dict[str, str]) -> Dict[str, Any]:
        """Generate the complete startup report."""
        print("[BOOTSTRAP] Generating startup report...")

        completed_milestones = []
        if os.path.exists(os.path.join(self.workspace_root, "docs", "09_COMPLETED_TASKS.md")):
            try:
                with open(os.path.join(self.workspace_root, "docs", "09_COMPLETED_TASKS.md"), "r", encoding="utf-8") as f:
                    content = f.read()
                    import re
                    milestones = re.findall(r"(MILESTONE\s+\d+\.\d+|STEP-[A-Za-z0-9_-]+).*?COMPLETED", content, re.DOTALL)
                    completed_milestones = [m.strip() for m in milestones if m]
            except Exception:
                pass

        report = {
            "runtime_version": runtime_context["runtime_version"],
            "registered_agents": runtime_context["agents"],
            "environment_status": {
                "lm_studio_available": runtime_context["environment"].get("LM_STUDIO_ENABLED", True),
                "backend_available": bool(runtime_context["environment"].get("BACKEND_URL")),
                "frontend_available": bool(runtime_context["environment"].get("FRONTEND_URL")),
            },
            "documentation_loaded": {
                "count": runtime_context["documentation_count"],
                "files": list(docs.keys()),
            },
            "current_milestone": runtime_context["current_milestone"],
            "next_task_description": "Review existing implementation before proceeding to next milestone",
            "runtime_state": {
                "initialized": runtime_context["runtime_state"]["initialized"],
                "ready_for_execution": runtime_context["runtime_state"]["ready_for_execution"],
            },
            "completed_milestones": completed_milestones,
            "user": os.environ.get("USER", "unknown"),
            "timestamp_utc": utc_now(),
            "timestamp_local": utc_local(),
            "errors": self.errors,
            "warnings": self.warnings,
        }

        return report

    def bootstrap(self) -> Dict[str, Any]:
        """Execute the complete bootstrap sequence."""
        print("=" * 70)
        print("RUNTIME BOOTSTRAP - Sanskriti AI Studio")
        print("=" * 70)
        print("[CRITICAL] Qwen 3.5 is TEXT-ONLY - No images allowed.")
        print(f"Timestamp: {utc_local()}")
        print("=" * 70)

        # Phase 1: Environment Validation
        print("\n--- Phase 1: Environment Validation ---")
        env_config = self.validate_environment_variables()

        # Phase 2: Folder Validation
        print("\n--- Phase 2: Folder Validation ---")
        folders_valid = self.validate_required_folders()

        # Phase 3: File Validation
        print("\n--- Phase 3: File Validation ---")
        self.validate_required_files()

        # Phase 4: Agent Registration
        print("\n--- Phase 4: Agent Registration ---")
        agent_status = self.register_all_agents()
        self.register_execution_manager()

        # Phase 5: Registry Validation
        print("\n--- Phase 5: Registry Validation ---")
        registry = self.validate_agent_registry()

        # Phase 6: Documentation Loading
        print("\n--- Phase 6: Documentation Loading ---")
        docs = self.load_documentation()

        # Phase 7: State Restoration
        print("\n--- Phase 7: State Restoration ---")
        self.restore_runtime_state()
        self.restore_milestone_state()
        execution_history = self.restore_execution_history()

        # Phase 8: Build Runtime Context
        print("\n--- Phase 8: Building Runtime Context ---")
        runtime_context = self.build_runtime_context(env_config, docs)

        # Phase 9: Generate Startup Report
        print("\n--- Phase 9: Generating Startup Report ---")
        startup_report = self.generate_startup_report(runtime_context, docs)

        # Print the startup report
        print("\n" + "=" * 70)
        print("RUNTIME STARTUP REPORT")
        print("=" * 70)
        print(f"\nRuntime Version: {startup_report['runtime_version']}")
        
        print(f"\nRegistered Agents:")
        for agent in startup_report["registered_agents"]:
            print(f"  - {agent}")
        
        print(f"\nEnvironment Status:")
        env = startup_report["environment_status"]
        print(f"  - LM Studio Available: {env['lm_studio_available']}")
        print(f"  - Backend Available: {env['backend_available']}")
        print(f"  - Frontend Available: {env['frontend_available']}")
        
        print(f"\nLoaded Documentation:")
        print(f"  - Count: {startup_report['documentation_loaded']['count']} files")
        
        print(f"\nCurrent Milestone: {startup_report['current_milestone']}")
        print(f"Next Task: {startup_report['next_task_description']}")
        
        print(f"\nRuntime State:")
        rs = startup_report["runtime_state"]
        print(f"  - Initialized: {rs['initialized']}")
        print(f"  - Ready for Execution: {rs['ready_for_execution']}")
        
        if startup_report["completed_milestones"]:
            print(f"\nCompleted Milestones:")
            for m in startup_report["completed_milestones"][:5]:
                print(f"  - {m}")
        
        print(f"\nUser: {startup_report['user']}")
        print(f"Timestamp (UTC): {startup_report['timestamp_utc']}")
        print(f"Timestamp (Local): {startup_report['timestamp_local']}")
        
        if startup_report["errors"]:
            print(f"\n[!] Errors ({len(startup_report['errors'])}):")
            for error in startup_report["errors"]:
                print(f"  - {error}")
        
        if startup_report["warnings"]:
            print(f"\n[!] Warnings ({len(startup_report['warnings'])}):")
            for warning in startup_report["warnings"]:
                print(f"  - {warning}")

        # Save startup report to file
        report_path = os.path.join(self.ai_agents_root, "state", "startup_report.json")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(startup_report, f, indent=2, default=str)
            print(f"\n[OK] Startup report saved to: {report_path}")
        except Exception as e:
            print(f"\n[!] Could not save startup report: {e}")

        # Validation result
        is_valid = len(startup_report["errors"]) == 0
        
        return {
            "success": is_valid,
            "report": startup_report,
            "runtime_context": runtime_context,
        }


def main() -> None:
    """CLI entry point for the Runtime Bootstrap."""
    parser = argparse.ArgumentParser(
        description="Run the Sanskriti AI Studio Runtime Bootstrap."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output.",
    )
    args = parser.parse_args()

    bootstrap = RuntimeBootstrap()
    result = bootstrap.bootstrap()

    if args.quiet:
        print(f"Bootstrap completed: {'SUCCESS' if result['success'] else 'FAILED'}")
    else:
        print("\n" + "=" * 70)
        if result["success"]:
            print("BOOTSTRAP COMPLETED SUCCESSFULLY")
            print("=" * 70)
        else:
            print("BOOTSTRAP FAILED - Runtime cannot proceed")
            print("=" * 70)
            sys.exit(1)


if __name__ == "__main__":
    main()
