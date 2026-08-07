#!/usr/bin/env python3
"""
Task Scheduler & Queue Manager for Sanskriti AI Studio.

This module provides a comprehensive task scheduling system that converts milestone plans
into executable task queues with full dependency management, priority-based execution,
status tracking, and recovery mechanisms.

Capabilities:
- Build dependency graphs from milestone plans
- Detect blocked tasks and circular dependencies
- Queue executable tasks with priority ordering
- Pause/Resume queue operations
- Retry failed tasks with configurable limits
- Cancel tasks (if dependencies allow)
- Reorder tasks within allowed ranges
- Continuously update MILESTONE_STATUS.md

Reuses existing components:
- Runtime Bootstrap (STEP 21.1)
- Context Manager (STEP 21.2)

Version: 1.0
Last Updated: 2026-08-05
"""

import argparse
import copy
import hashlib
import json
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENTS_ROOT = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.join(AI_AGENTS_ROOT, "..") if AI_AGENTS_ROOT.startswith(".") else os.path.dirname(AI_AGENTS_ROOT)
STATE_DIR = os.path.join(AI_AGENTS_ROOT, "state")
MILESTONE_STATUS_PATH = os.path.join(WORKSPACE_ROOT, "ai_agents", "state", "milestone_status.json")


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    """Task execution status enum."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Priority ordering for sorting (higher number = higher priority)
PRIORITY_ORDER = {
    TaskPriority.LOW: 0,
    TaskPriority.MEDIUM: 1,
    TaskPriority.HIGH: 2,
    TaskPriority.CRITICAL: 3,
}


@dataclass
class Task:
    """
    Reusable Task Model.
    
    Each task contains all necessary information for execution tracking and management.
    """
    # Identification
    task_id: str
    milestone_id: str = ""
    
    # Core information
    title: str = ""
    description: str = ""
    
    # Execution criteria
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # Prioritization
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_effort: str = "medium"  # low, medium, high
    
    # Execution state
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    # Assignment
    assigned_agent: Optional[str] = None
    
    # Timing
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    # Validation
    validation_status: str = ""  # passed, failed, pending, not_applicable
    
    # Review
    review_status: str = ""  # passed, failed, pending, not_applicable
    
    # Additional metadata
    execution_order: int = 0
    queued_at: Optional[str] = None
    last_updated: Optional[str] = field(default_factory=utc_now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "milestone_id": self.milestone_id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "priority": self.priority.value,
            "estimated_effort": self.estimated_effort,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "assigned_agent": self.assigned_agent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "validation_status": self.validation_status,
            "review_status": self.review_status,
            "execution_order": self.execution_order,
            "queued_at": self.queued_at,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task from a dictionary."""
        return cls(
            task_id=data.get("task_id", ""),
            milestone_id=data.get("milestone_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            dependencies=data.get("dependencies", []),
            priority=TaskPriority(data.get("priority", "medium")),
            estimated_effort=data.get("estimated_effort", "medium"),
            status=TaskStatus(data.get("status", "pending")),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            assigned_agent=data.get("assigned_agent"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            validation_status=data.get("validation_status", ""),
            review_status=data.get("review_status", ""),
            execution_order=data.get("execution_order", 0),
            queued_at=data.get("queued_at"),
            last_updated=data.get("last_updated", utc_now()),
        )


class DependencyGraph:
    """
    Dependency graph for task scheduling.
    
    Supports:
    - Sequential tasks (A -> B -> C)
    - Parallel tasks (A -> [B, C] -> D)
    - Conditional tasks (if A completed then run X else Y)
    - Blocked task detection
    - Circular dependency prevention
    """
    
    def __init__(self):
        self._adjacency: Dict[str, List[str]] = defaultdict(list)  # task -> [dependents]
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # task -> [dependencies]
        self._nodes: Set[str] = set()
    
    def add_task(self, task_id: str, dependencies: Optional[List[str]]) -> None:
        """Add a task with its dependencies.
        
        Args:
            task_id: Unique identifier for the task
            dependencies: List of task IDs this task depends on (can be empty)
        """
        if task_id not in self._nodes:
            self._nodes.add(task_id)
        
        # Use safe default for dependencies list
        deps = dependencies or []
        
        # Add reverse edges (dependencies point to this task)
        for dep in deps:
            self._reverse_adjacency[dep].append(task_id)
            
            # Add forward edges (this task depends on dep, so dep -> this)
            if dep and dep not in self._nodes:
                self._nodes.add(dep)
                self._adjacency[dep].append(task_id)
    
    def is_circular(self) -> Tuple[bool, Optional[str]]:
        """Check for circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle - reconstruct path
                    cycle_path = [node, neighbor]
                    return cycle_path
            
            rec_stack.remove(node)
            return None
        
        for node in self._nodes:
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return True, " -> ".join(cycle)
        
        return False, None
    
    def get_executable_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """Get tasks that are ready to execute (all dependencies satisfied)."""
        executable = []
        
        for task_id in self._nodes:
            if task_id in completed_tasks:
                continue
            
            # Check if all dependencies are satisfied
            deps = self._reverse_adjacency.get(task_id, [])
            unmet_deps = [d for d in deps if d not in completed_tasks]
            
            if not unmet_deps:
                executable.append(task_id)
        
        return executable
    
    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks that are blocked due to unsatisfied dependencies."""
        completed = self._nodes.copy()  # Track all known task IDs
        
        blocked = []
        for task_id in self._nodes:
            deps = self._reverse_adjacency.get(task_id, [])
            if deps:
                unmet = [d for d in deps if d not in completed]
                if unmet:
                    blocked.append({
                        "task_id": task_id,
                        "missing_dependencies": unmet,
                    })
        
        return blocked
    
    def detect_orphan_tasks(self) -> List[str]:
        """Detect tasks with no incoming edges (no dependencies)."""
        orphans = []
        for node in self._nodes:
            if not self._reverse_adjacency.get(node):
                orphans.append(node)
        return orphans
    
    def get_task_predecessors(self, task_id: str) -> List[str]:
        """Get all tasks that must complete before this one."""
        visited = set()
        
        def dfs(current: str) -> Set[str]:
            if current in visited:
                return set()
            visited.add(current)
            
            result = set()
            for dep in self._reverse_adjacency.get(current, []):
                result.update(dfs(dep))
            
            visited.discard(current)
            return result
        
        return list(dfs(task_id))


class TaskQueue:
    """Task Queue Manager with full CRUD operations."""
    
    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self._queue: List[Task] = []
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._paused: bool = False
        self._lock = threading.Lock()
    
    def enqueue(self, task: Task) -> bool:
        """Add a task to the queue if dependencies are satisfied."""
        with self._lock:
            existing = [t for t in self._queue if t.task_id == task.task_id]
            if existing:
                return False
            
            unmet_deps = []
            for dep in task.dependencies:
                if dep not in self._completed and dep not in self._failed:
                    unmet_deps.append(dep)
            
            if unmet_deps:
                print(f"[Queue] Skipping {task.task_id}: unmet dependencies {unmet_deps}")
                return False
            
            task.status = TaskStatus.QUEUED
            task.queued_at = utc_now()
            task.execution_order = len(self._queue) + 1
            
            self._queue.append(task)
            self._queue.sort(key=lambda t: PRIORITY_ORDER[t.priority], reverse=True)
            
            return True
    
    def dequeue(self, max_count: int = 1) -> List[Task]:
        """Remove and return tasks from queue for execution."""
        with self._lock:
            if self._paused:
                print("[Queue] Queue is paused")
                return []
            
            if not self._queue:
                print("[Queue] Queue is empty")
                return []
            
            self._queue.sort(key=lambda t: PRIORITY_ORDER[t.priority], reverse=True)
            
            tasks = self._queue[:max_count]
            self._queue = self._queue[max_count:]
            
            for task in tasks:
                task.status = TaskStatus.RUNNING
                task.start_time = utc_now()
            
            return tasks
    
    def peek(self, n: int = 1) -> List[Task]:
        """Look at queue without removing."""
        with self._lock:
            if self._paused:
                return []
            
            sorted_queue = sorted(self._queue, key=lambda t: PRIORITY_ORDER[t.priority], reverse=True)
            return sorted_queue[:n]
    
    def pause(self) -> None:
        """Pause queue operations."""
        with self._lock:
            self._paused = True
            print("[Queue] Queue paused")
    
    def resume(self) -> None:
        """Resume queue operations."""
        with self._lock:
            self._paused = False
            print("[Queue] Queue resumed")
    
    def retry(self, task_id: str) -> bool:
        """Retry a failed task."""
        with self._lock:
            for task in self._queue:
                if task.task_id == task_id:
                    task.retry_count += 1
                    task.start_time = None
                    task.end_time = None
                    return True
            
            if task_id in self._failed:
                print(f"[Queue] Task {task_id} not found or marked as failed permanently")
                return False
            
            return False
    
    def cancel(self, task_id: str) -> bool:
        """Cancel a task if dependencies allow."""
        with self._lock:
            task = next((t for t in self._queue if t.task_id == task_id), None)
            if not task:
                print(f"[Queue] Task {task_id} not found")
                return False
            
            dependents = self.graph.get_task_predecessors(task_id)
            
            if dependents:
                affected = [d for d in dependents if d not in self._completed]
                if affected:
                    print(f"[Queue] Cannot cancel {task_id}: affects {affected}")
                    return False
            
            task.status = TaskStatus.SKIPPED
            return True
    
    def reorder(self, from_order: int, to_order: int) -> bool:
        """Reorder a task within allowed range."""
        with self._lock:
            task_item = None
            for i, task in enumerate(self._queue):
                if task.execution_order == from_order:
                    task_item = task
                    break
            
            if not task_item:
                print(f"[Queue] Task at order {from_order} not found")
                return False
            
            self._queue.remove(task_item)
            
            target_index = min(to_order, len(self._queue) - 1)
            self._queue.insert(target_index, task_item)
            
            for i, t in enumerate(self._queue):
                t.execution_order = i + 1
            
            return True
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                "total_queued": len(self._queue),
                "total_completed": len(self._completed),
                "total_failed": len(self._failed),
                "paused": self._paused,
                "priority_distribution": {
                    p: sum(1 for t in self._queue if t.priority == p)
                    for p in TaskPriority
                },
            }


class TaskScheduler:
    """Main Task Scheduler that orchestrates task execution."""
    
    def __init__(self, 
                 graph: Optional[DependencyGraph] = None,
                 queue: Optional[TaskQueue] = None,
                 context_manager=None):
        self.graph = graph or DependencyGraph()
        self.queue = queue or TaskQueue(self.graph)
        self.context_manager = context_manager
        
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._running: Set[str] = set()
        self._current_task: Optional[Task] = None
        self._interrupted: bool = False
        self._max_parallel_tasks: int = 1
        self._agent_mapping: Dict[str, List[str]] = {}
    
    def load_plan(self, plan: Dict[str, Any]) -> bool:
        """Load a milestone plan and build dependency graph."""
        print("=" * 60)
        print("Task Scheduler - Loading Plan")
        print("=" * 60)
        
        tasks_data = plan.get("tasks", [])
        
        for task_data in tasks_data:
            task = Task.from_dict(task_data)
            
            # Add to graph (graph maintains its own node tracking)
            self.graph.add_task(task.task_id, task.dependencies)
            
            # Try to enqueue if dependencies satisfied
            if not self.queue.enqueue(task):
                pass  # Task is waiting for dependencies
        
        # Check for circular dependencies
        is_circular, cycle = self.graph.is_circular()
        if is_circular:
            print(f"[!] Circular dependency detected: {cycle}")
            return False
        
        orphans = self.graph.detect_orphan_tasks()
        total_nodes = len(self.graph._nodes)
        print(f"[OK] Graph built with {total_nodes} tasks, {len(orphans)} entry points")
        
        return True
    
    def select_next_task(self) -> Optional[Task]:
        """Select the next task to execute based on priority."""
        executable_ids = self.graph.get_executable_tasks(self._completed)
        
        if not executable_ids:
            print("[Scheduler] No executable tasks available")
            
            blocked = self.graph.get_blocked_tasks()
            if blocked:
                print(f"[!] Blocked tasks: {blocked}")
            
            return None
        
        queued_executable = [t for t in self.queue._queue 
                           if t.task_id in executable_ids]
        
        if queued_executable:
            return max(queued_executable, key=lambda t: PRIORITY_ORDER[t.priority])
        
        return None
    
    def assign_agent(self, task: Task) -> Optional[str]:
        """Assign a task to an available agent."""
        if not task.assigned_agent:
            return self._get_default_agent(task.title)
        return task.assigned_agent
    
    def _get_default_agent(self, title: str) -> Optional[str]:
        """Get default agent based on task type."""
        title_lower = title.lower()
        
        if "test" in title_lower or "lint" in title_lower or "build" in title_lower:
            return "testing_agent"
        elif "debug" in title_lower:
            return "debugger_agent"
        elif "review" in title_lower:
            return "reviewer_agent"
        elif "doc" in title_lower or "read" in title_lower:
            return "documentation_agent"
        
        return "coding_agent"
    
    def mark_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        self._completed.add(task_id)
        if task_id in self._running:
            self._running.discard(task_id)
        
        self._trigger_dependents(task_id)
    
    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self._failed.add(task_id)
        if task_id in self._running:
            self._running.discard(task_id)
        
        task = next((t for t in self.queue._queue if t.task_id == task_id), None)
        if task and task.retry_count < task.max_retries:
            print(f"[Scheduler] Task {task_id} will be retried (attempt {task.retry_count + 1}/{task.max_retries})")
            return
        
        print(f"[Scheduler] Task {task_id} marked as failed permanently")
    
    def _trigger_dependents(self, completed_task: str) -> None:
        """Trigger tasks whose dependencies are now satisfied."""
        for dependent_id in self.graph._reverse_adjacency.get(completed_task, []):
            task = next((t for t in self.queue._queue if t.task_id == dependent_id), None)
            
            if task and dependent_id not in self._completed and dependent_id not in self._failed:
                deps = self.graph._reverse_adjacency.get(dependent_id, [])
                unmet_deps = [d for d in deps if d not in self._completed]
                
                if not unmet_deps:
                    print(f"[Scheduler] Triggering dependent: {dependent_id}")
    
    def is_task_blocked(self, task: Task) -> bool:
        """Check if a task is blocked."""
        for dep in task.dependencies:
            if dep in self._failed:
                task_item = next((t for t in self.queue._queue if t.task_id == dep), None)
                if task_item and task_item.retry_count >= task_item.max_retries:
                    return True
        
        is_circular, _ = self.graph.is_circular()
        if is_circular:
            return True
        
        return False
    
    def should_stop_execution(self, task: Task) -> bool:
        """Check if execution should stop on blocked task."""
        if self.is_task_blocked(task):
            return True
        
        return False


class StatusTracker:
    """Tracks task status and updates milestone status."""
    
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.status_file = MILESTONE_STATUS_PATH
    
    def get_status_counts(self) -> Dict[str, int]:
        """Get counts for each status category."""
        pending = sum(1 for t in self.scheduler.queue._queue 
                     if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED])
        running = len(self.scheduler._running)
        completed = len(self.scheduler._completed)
        failed = len(self.scheduler._failed)
        
        blocked = sum(1 for t in self.scheduler.queue._queue 
                     if t.dependencies and any(d not in self.scheduler._completed for d in t.dependencies))
        skipped = sum(1 for t in self.scheduler.queue._queue 
                     if t.status == TaskStatus.SKIPPED)
        
        return {
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
            "total_queued": len(self.scheduler.queue._queue),
        }
    
    def update_status_file(self) -> bool:
        """Update milestone status with current status."""
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            
            counts = self.get_status_counts()
            tasks = self.scheduler.queue._queue
            
            queue_state = {
                "scheduler_type": "TaskScheduler",
                "timestamp": utc_now(),
                "status_counts": counts,
                "tasks": [t.to_dict() for t in tasks],
                "completed_task_ids": list(self.scheduler._completed),
                "failed_task_ids": list(self.scheduler._failed),
                "interrupted": self.scheduler._interrupted,
            }
            
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(queue_state, f, indent=2, default=str)
            
            print(f"[Status] Status saved to {self.status_file}")
            print(f"[Status] Queue: {counts['total_queued']} queued, {counts['completed']} completed, "
                  f"{counts['failed']} failed")
            
            return True
            
        except Exception as e:
            print(f"[Status] Failed to update status file: {e}")
            return False


class RecoveryManager:
    """Handles recovery after interruption."""
    
    def __init__(self, status_file: str = MILESTONE_STATUS_PATH):
        self.status_file = status_file
        self._saved_queues: List[Dict[str, Any]] = []
        self._completed_task_ids: Set[str] = set()
        self._failed_task_ids: Set[str] = set()
    
    def save_state(self, scheduler: TaskScheduler) -> None:
        """Save current execution state for recovery."""
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            
            state = {
                "timestamp": utc_now(),
                "completed_task_ids": list(scheduler._completed),
                "failed_task_ids": list(scheduler._failed),
                "running_task_id": list(scheduler._running)[0] if scheduler._running else None,
                "interrupted": scheduler._interrupted,
                "queue_snapshot": [t.to_dict() for t in scheduler.queue._queue],
            }
            
            with open(self.status_file.replace(".json", "_state.json"), "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            
            print(f"[Recovery] State saved to {self.status_file.replace('.json', '_state.json')}")
            
        except Exception as e:
            print(f"[Recovery] Failed to save state: {e}")
    
    def restore_state(self, scheduler: TaskScheduler) -> Optional[Dict[str, Any]]:
        """Restore execution state from saved file."""
        try:
            marker_file = self.status_file.replace(".json", "_interrupted.json")
            
            if not os.path.exists(marker_file):
                return None
            
            with open(marker_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            scheduler._completed = set(state.get("completed_task_ids", []))
            scheduler._failed = set(state.get("failed_task_ids", []))
            
            running_id = state.get("running_task_id")
            if running_id:
                scheduler._running.add(running_id)
            
            scheduler._interrupted = state.get("interrupted", False)
            
            print(f"[Recovery] State restored from {marker_file}")
            print(f"[Recovery] Completed: {len(scheduler._completed)}, Failed: {len(scheduler._failed)}")
            
            return state
            
        except Exception as e:
            print(f"[Recovery] Failed to restore state: {e}")
            return None


class TaskSchedulerCLI:
    """Command-line interface for Task Scheduler."""
    
    def __init__(self):
        self.scheduler = TaskScheduler()
        self.status_tracker = StatusTracker(self.scheduler)
    
    def bootstrap(self, plan_path: str) -> Dict[str, Any]:
        """Initialize scheduler with a plan file."""
        print("=" * 60)
        print("Task Scheduler & Queue Manager - Sanskriti AI Studio")
        print("=" * 60)
        
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
        
        plan_id = plan.get("plan_id", "unknown")
        request = plan.get("request", "No request")
        
        print(f"[Scheduler] Plan ID: {plan_id}")
        print(f"[Scheduler] Request: {request[:100]}...")
        
        self.scheduler.load_plan(plan)
        
        os.makedirs(os.path.dirname(MILESTONE_STATUS_PATH), exist_ok=True)
        with open(MILESTONE_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump({"plan_id": plan_id, "status_counts": self.status_tracker.get_status_counts()}, 
                     f, indent=2, default=str)
        
        print(f"[OK] Scheduler initialized for plan {plan_id}")
        
        return {
            "success": True,
            "plan_id": plan_id,
            "total_tasks": len(plan.get("tasks", [])),
        }
    
    def show_queue(self) -> Dict[str, Any]:
        """Display current queue status."""
        counts = self.status_tracker.get_status_counts()
        
        print("\n" + "=" * 60)
        print("Current Queue Status")
        print("=" * 60)
        
        print(f"\nStatus Counts:")
        for status, count in counts.items():
            print(f"  {status}: {count}")
        
        if self.scheduler.queue._queue:
            print("\nQueue Tasks (prioritized):")
            for i, task in enumerate(self.scheduler.queue._queue):
                print(f"\n  [{i+1}] {task.task_id}")
                print(f"      Title: {task.title}")
                print(f"      Status: {task.status.value}")
                print(f"      Priority: {task.priority.value}")
                print(f"      Dependencies: {task.dependencies}")
        
        return counts


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Task Scheduler & Queue Manager for Sanskriti AI Studio"
    )
    parser.add_argument(
        "--plan",
        type=str,
        help="Path to milestone plan JSON file",
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["bootstrap", "show_queue", "enqueue", "dequeue", "pause", "resume"],
        default="bootstrap",
        help="Action to perform",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore from interrupted state",
    )
    
    args = parser.parse_args()
    
    cli = TaskSchedulerCLI()
    
    if args.restore:
        recovery = RecoveryManager(MILESTONE_STATUS_PATH)
        state = recovery.restore_state(cli.scheduler)
        
        if state:
            print("[Recovery] Restore complete")
        else:
            print("[Recovery] No interrupted state found")
    else:
        if args.plan:
            result = cli.bootstrap(args.plan)
            
            if args.action == "show_queue":
                queue_info = cli.show_queue()
        
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
