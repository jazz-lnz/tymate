from datetime import datetime
import json
from typing import List, Optional
from storage.sqlite import get_database
from models.session import Session
from models.task import Task


class SessionManager:
    """CRUD operations for task session logs."""

    def __init__(self):
        self.db = get_database()

    def _log_task_event(
        self,
        user_id: int,
        task_id: int,
        event_type: str,
        message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Write task-related event entry from session operations."""
        try:
            self.db.insert(
                "task_events",
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "event_type": event_type,
                    "message": message,
                    "metadata": json.dumps(metadata or {}),
                    "created_at": datetime.now().isoformat(),
                },
            )
        except Exception:
            pass

    def add_session(
        self,
        user_id: int,
        task_id: int,
        duration_minutes: int,
        notes: Optional[str] = None,
        task: Optional[Task] = None,
    ) -> tuple[bool, str, Optional[Session]]:
        """Create a session record, update task status, and optionally append to task.sessions."""
        if duration_minutes is None or duration_minutes <= 0:
            return False, "Duration must be a positive number of minutes", None

        session = Session(
            user_id=user_id,
            task_id=task_id,
            duration_minutes=duration_minutes,
            notes=notes,
        )

        try:
            session_data = session.to_dict()
            session_data.pop("id")

            session_id = self.db.insert("task_sessions", session_data)
            session.id = session_id

            updated_rows = self.db.update(
                "tasks",
                {
                    "status": "In Progress",
                    "updated_at": datetime.now().isoformat(),
                },
                "id = ? AND status = ? AND is_deleted = 0",
                (task_id, "Not Started"),
            )

            self._log_task_event(
                user_id=user_id,
                task_id=task_id,
                event_type="TASK_SESSION_LOGGED",
                message="Session logged",
                metadata={
                    "duration_minutes": duration_minutes,
                    "notes": notes,
                },
            )

            if updated_rows:
                self._log_task_event(
                    user_id=user_id,
                    task_id=task_id,
                    event_type="TASK_STARTED",
                    message="Task auto-started from first session",
                )

            if task is not None:
                if task.sessions is None:
                    task.sessions = []
                task.sessions.append(session)

            return True, "Session logged successfully!", session
        except Exception as exc:
            return False, f"Failed to log session: {str(exc)}", None

    def log_session(
        self,
        user_id: int,
        task_id: int,
        duration_minutes: int,
        notes: Optional[str] = None,
    ) -> tuple[bool, str, Optional[Session]]:
        """Backward-compatible alias for add_session."""
        return self.add_session(
            user_id=user_id,
            task_id=task_id,
            duration_minutes=duration_minutes,
            notes=notes,
        )

    def get_sessions_for_task(self, task_id: int) -> List[Session]:
        """Fetch non-deleted sessions for a task."""
        rows = self.db.fetch_all(
            """
            SELECT * FROM task_sessions
            WHERE task_id = ? AND is_deleted = 0
            ORDER BY logged_at ASC
            """,
            (task_id,),
        )
        return [Session.from_dict(row) for row in rows]

    def get_total_minutes_for_task(self, task_id: int) -> int:
        """Get total minutes for a task by summing sessions."""
        result = self.db.fetch_one(
            """
            SELECT SUM(duration_minutes) as total_minutes
            FROM task_sessions
            WHERE task_id = ? AND is_deleted = 0
            """,
            (task_id,),
        )
        return int(result["total_minutes"] or 0) if result else 0

    def get_sessions_for_user_today(self, user_id: int) -> List[Session]:
        """Fetch today's sessions for a user."""
        today = datetime.now().date().isoformat()
        rows = self.db.fetch_all(
            """
            SELECT * FROM task_sessions
            WHERE user_id = ?
            AND is_deleted = 0
            AND DATE(logged_at) = ?
            ORDER BY logged_at ASC
            """,
            (user_id, today),
        )
        return [Session.from_dict(row) for row in rows]

    def get_sessions_for_user(self, user_id: int) -> List[Session]:
        """Fetch all non-deleted sessions for a user."""
        rows = self.db.fetch_all(
            """
            SELECT * FROM task_sessions
            WHERE user_id = ?
            AND is_deleted = 0
            ORDER BY logged_at ASC
            """,
            (user_id,),
        )
        return [Session.from_dict(row) for row in rows]

    def delete_session(self, session_id: int) -> tuple[bool, str]:
        """Soft delete a session (mark as deleted)."""
        try:
            existing = self.db.fetch_one(
                "SELECT user_id, task_id, duration_minutes, notes FROM task_sessions WHERE id = ?",
                (session_id,),
            )

            self.db.update(
                "task_sessions",
                {
                    "is_deleted": 1,
                    "deleted_at": datetime.now().isoformat(),
                },
                "id = ?",
                (session_id,),
            )

            if existing:
                self._log_task_event(
                    user_id=existing["user_id"],
                    task_id=existing["task_id"],
                    event_type="TASK_SESSION_DELETED",
                    message="Session deleted",
                    metadata={
                        "duration_minutes": existing.get("duration_minutes"),
                        "notes": existing.get("notes"),
                    },
                )
            return True, "Session deleted successfully"
        except Exception as exc:
            return False, f"Failed to delete session: {str(exc)}"
