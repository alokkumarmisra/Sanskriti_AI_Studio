#!/usr/bin/env python3
"""
Screenshot Lifecycle Management Module for Sanskriti AI Studio.

This module handles the lifecycle management of screenshots including:
- Session creation and tracking
- Archiving completed sessions
- Expiration handling
- Cleanup policy enforcement

Lifecycle Features:
- Create screenshot sessions
- Archive old or completed sessions
- Delete expired screenshots
- Enforce cleanup policies
- Track session state

Version: 1.0
Last Updated: 2026-08-07
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    """Screenshot session lifecycle status."""

    ACTIVE = "active"          # Session is currently active
    COMPLETED = "completed"     # Session tasks are done
    ARCHIVED = "archived"       # Session has been archived
    EXPIRED = "expired"         # Session has expired and can be cleaned


@dataclass
class CleanupPolicy:
    """Configuration for screenshot cleanup policies."""

    # Time-based retention
    default_retention_hours: int = 24      # Default hours before auto-expiry
    session_retention_days: int = 7        # Keep sessions for days
    
    # Size-based limits
    max_screenshots_per_session: int = 100  # Maximum screenshots per session
    max_session_directory_size_mb: float = 50.0  # Max session directory size
    
    # Archive settings
    archive_after_hours_idle: int = 48      # Archive sessions idle for this many hours
    archive_before_days_ago: int = 30       # Archive screenshots older than days
    
    # Cleanup schedule
    cleanup_check_interval_minutes: int = 60  # How often to check cleanup
    
    def __post_init__(self):
        """Validate configuration."""
        if self.default_retention_hours < 1:
            self.default_retention_hours = 24
        if self.session_retention_days < 1:
            self.session_retention_days = 7


class LifecycleManager:
    """
    Manager for screenshot lifecycle operations.

    Handles session management, archiving, expiration, and cleanup policies.
    """

    def __init__(self, policy: Optional[CleanupPolicy] = None):
        """
        Initialize the lifecycle manager.

        Args:
            policy: Cleanup policy configuration (uses defaults if None)
        """
        self.policy = policy or CleanupPolicy()
        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session info
        self._session_path = Path("runtime/screenshots")

    def create_session(self, session_name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new screenshot session.

        Args:
            session_name: Name/identifier for the session
            metadata: Optional metadata about the session

        Returns:
            Session information including ID and status
        """
        import uuid
        
        session_id = f"sess_{session_name}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        self._sessions[session_id] = {
            "name": session_name,
            "id": session_id,
            "created_at": now,
            "status": SessionStatus.ACTIVE.value,
            "last_accessed": now,
            "screenshot_count": 0,
            "metadata": metadata or {},
            "screenshots": [],
        }
        
        # Create session directory
        session_dir = self._session_path / "session" / session_name.replace("/", "_")
        session_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "session_id": session_id,
            "name": session_name,
            "status": SessionStatus.ACTIVE.value,
            "created_at": now,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Session info or None if not found
        """
        return self._sessions.get(session_id)

    def _get_screenshot_path(self, image_path: str) -> Path:
        """Convert an image path string to a Path object."""
        if not image_path:
            return Path("")
        
        return Path(image_path)

    def get_session_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get session by name.

        Args:
            name: Session name to look up

        Returns:
            Session info or None if not found
        """
        for session in self._sessions.values():
            if session["name"] == name:
                return session
        return None

    def add_screenshot_to_session(self, session_id: str, screenshot_metadata: Dict[str, Any]) -> bool:
        """
        Add a screenshot to a session.

        Args:
            session_id: The session ID
            screenshot_metadata: Metadata about the screenshot

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check screenshot limit
        if len(session["screenshots"]) >= self.policy.max_screenshots_per_session:
            print(f"[LIFECYCLE] Session {session_id} hit screenshot limit ({self.policy.max_screenshots_per_session})")
            return False
        
        session["screenshots"].append(screenshot_metadata)
        session["screenshot_count"] = len(session["screenshots"])
        session["last_accessed"] = datetime.now(timezone.utc).isoformat()
        
        return True

    def archive_session(self, session_id: str) -> Optional[str]:
        """
        Archive a completed session.

        Moves session directory to archive location.

        Args:
            session_id: The session ID to archive

        Returns:
            Path to archived session or None if failed
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Mark as completed first
        session["status"] = SessionStatus.COMPLETED.value
        
        # Create session info file
        session_info = {
            "session_name": session["name"],
            "session_id": session["id"],
            "screenshots": [
                {
                    "metadata": s,
                    "path": self._get_screenshot_path(s.get("image_path", ""))
                }
                for s in session.get("screenshots", [])
            ],
        }
        
        # Create archive path
        archived_name = session["name"].replace("/", "_")
        archive_dir = self._session_path / "archived" / f"{session['id'][:8]}_{archived_name}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Save session info
        info_path = archive_dir / "session_info.json"
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(session_info, f, indent=2)

        return str(archive_dir)

    def archive_all_idle_sessions(self, timeout_hours: int = 48) -> List[str]:
        """
        Archive all sessions that have been idle for the specified time.

        Args:
            timeout_hours: Hours of inactivity before archiving

        Returns:
            List of archived session paths
        """
        archived: List[str] = []
        now = datetime.now(timezone.utc)
        
        for session_id, session in self._sessions.items():
            last_accessed_str = session.get("last_accessed", "")
            if not last_accessed_str:
                continue
            
            try:
                last_accessed = datetime.fromisoformat(last_accessed_str.replace('Z', '+00:00'))
                idle_hours = (now - last_accessed).total_seconds() / 3600
                
                if idle_hours >= timeout_hours and session["status"] == SessionStatus.ACTIVE.value:
                    archived_path = self.archive_session(session_id)
                    if archived_path:
                        archived.append(archived_path)
                        
            except Exception as e:
                print(f"[LIFECYCLE] Error checking session {session_id}: {e}")
        
        return archived

    def mark_session_expired(self, session_id: str) -> bool:
        """
        Mark a session as expired.

        Args:
            session_id: The session ID to mark as expired

        Returns:
            True if successfully marked, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        now = datetime.now(timezone.utc).isoformat()
        session["status"] = SessionStatus.EXPIRED.value
        session["expired_at"] = now
        
        # Update screenshots to expired status
        for screenshot in session.get("screenshots", []):
            screenshot["status"] = "expired"
        
        return True

    def should_expire(self, session_id: str, hours: Optional[int] = None) -> bool:
        """
        Check if a session should expire based on retention policy.

        Args:
            session_id: The session ID to check
            hours: Override retention hours (optional)

        Returns:
            True if the session has exceeded its retention period
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        created_str = session.get("created_at", "")
        if not created_str:
            return False
        
        try:
            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            retention_hours = hours or self.policy.default_retention_hours
            
            # Check if screenshot count limit reached
            if len(session.get("screenshots", [])) >= self.policy.max_screenshots_per_session:
                return False  # Don't expire if under screenshot limit
            
            created_ts = created.timestamp()
            now_ts = datetime.now(timezone.utc).timestamp()
            
            return (now_ts - created_ts) > (retention_hours * 3600)
            
        except Exception:
            return False

    def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """
        Clean up expired sessions and their screenshots.

        Returns:
            Summary of cleanup operations performed
        """
        import shutil
        import glob
        
        cleaned: Dict[str, Any] = {
            "sessions_removed": 0,
            "screenshots_removed": 0,
            "bytes_freed": 0,
        }
        
        now = datetime.now(timezone.utc)
        
        # Get all session directories
        session_dir = self._session_path / "session"
        if not session_dir.exists():
            return cleaned
        
        for dir_entry in session_dir.iterdir():
            if not dir_entry.is_dir() or dir_entry.name.startswith("__"):
                continue
            
            # Parse session name from path
            try:
                session_name = dir_entry.name.replace("_", "/")
            except Exception:
                continue
            
            # Check if any screenshot is expired
            needs_cleanup = False
            for file_path in dir_entry.glob("*.png"):
                try:
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    age_hours = (now - modified_time).total_seconds() / 3600
                    
                    if age_hours > self.policy.default_retention_hours:
                        needs_cleanup = True
                        
                        # Remove expired files
                        file_path.unlink()
                        cleaned["screenshots_removed"] += 1
                        cleaned["bytes_freed"] += file_path.stat().st_size
                        
                except Exception:
                    pass
            
            if needs_cleanup or len(list(dir_entry.glob("*.png"))) == 0:
                try:
                    shutil.rmtree(dir_entry)
                    cleaned["sessions_removed"] += 1
                except Exception as e:
                    print(f"[LIFECYCLE] Error removing session {dir_entry}: {e}")
        
        return cleaned

    def cleanup_old_sessions(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """
        Remove sessions older than the specified age.

        Args:
            days_to_keep: Keep sessions newer than this many days

        Returns:
            Summary of cleanup operations
        """
        import shutil
        
        cleaned: Dict[str, Any] = {
            "sessions_removed": 0,
            "screenshots_removed": 0,
        }
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days_to_keep)
        
        session_dir = self._session_path / "session"
        if not session_dir.exists():
            return cleaned
        
        for dir_entry in session_dir.iterdir():
            if not dir_entry.is_dir() or dir_entry.name.startswith("__"):
                continue
            
            try:
                created_time = datetime.fromtimestamp(dir_entry.stat().st_ctime)
                if created_time < cutoff:
                    shutil.rmtree(dir_entry)
                    cleaned["sessions_removed"] += 1
                    
                    # Count screenshots removed
                    screenshot_count = len(list(dir_entry.glob("*.png")))
                    cleaned["screenshots_removed"] += screenshot_count
                        
            except Exception as e:
                print(f"[LIFECYCLE] Error processing session {dir_entry}: {e}")
        
        return cleaned

    def archive_by_age(self, days: int = 30) -> Dict[str, Any]:
        """
        Archive screenshots older than specified age.

        Args:
            days: Age in days before archiving

        Returns:
            Summary of archive operations
        """
        import shutil
        
        archived: Dict[str, Any] = {
            "archived": 0,
            "bytes_archived": 0,
        }
        
        session_dir = self._session_path / "session"
        if not session_dir.exists():
            return archived
        
        archive_base = self._session_path / "archived"
        archive_base.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        
        for dir_entry in session_dir.iterdir():
            if not dir_entry.is_dir() or dir_entry.name.startswith("__"):
                continue
            
            try:
                for file_path in list(dir_entry.glob("*.png")):
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if modified_time < cutoff:
                        # Create archive path
                        archived_name = f"{dir_entry.name}_{file_path.stem}_{int(file_path.stat().st_mtime)}"
                        archive_path = archive_base / f"{archived_name}{file_path.suffix}"
                        
                        try:
                            shutil.move(str(file_path), str(archive_path))
                            archived["archived"] += 1
                            archived["bytes_archived"] += file_path.stat().st_size
                            
                            # Optionally mark as archived
                            session = self.get_session_by_name(dir_entry.name)
                            if session:
                                screenshot_info = next(
                                    (s for s in session.get("screenshots", []) 
                                     if "image_path" in str(s).split("/")[-1] if "/" in str(s)), None
                                )
                        except Exception as e:
                            print(f"[LIFECYCLE] Error archiving {file_path}: {e}")
                        
            except Exception as e:
                pass
        
        return archived

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a session.

        Args:
            session_id: The session ID

        Returns:
            Statistics dictionary or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        screenshots = session.get("screenshots", [])
        
        total_size_bytes = 0
        for s in screenshots:
            path = str(s.get("image_path", ""))
            if "/" in path:
                base_dir = Path(str(self._session_path).replace("\\", "/"))
                try:
                    rel_parts = path.split("/")
                    # Rebuild path from session structure
                    dir_name = f"session/{rel_parts[1]}" if len(rel_parts) > 1 else ""
                    full_path = base_dir / dir_name / rel_parts[0] if "/" in path else base_dir / path
                    
                    if full_path.exists():
                        total_size_bytes += full_path.stat().st_size
                except Exception:
                    pass
        
        return {
            "session_id": session["id"],
            "name": session["name"],
            "status": session.get("status", ""),
            "created_at": session.get("created_at", ""),
            "screenshot_count": len(screenshots),
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_bytes / (1024 * 1024),
        }

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all active and completed sessions."""
        return [
            {
                "session_id": s["id"],
                "name": s["name"],
                "status": s.get("status", ""),
                "created_at": s.get("created_at", ""),
                "screenshot_count": s.get("screenshot_count", 0),
            }
            for s in self._sessions.values()
        ]

    def clear_sessions(self) -> int:
        """
        Clear all session tracking (keep actual files).

        Returns:
            Number of sessions cleared
        """
        count = len(self._sessions)
        self._sessions.clear()
        return count


__all__ = [
    "SessionStatus",
    "CleanupPolicy", 
    "LifecycleManager",
]
