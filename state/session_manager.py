from datetime import datetime
from typing import List, Optional
from storage.sqlite import get_database
from models.session import Session


class SessionManager:
    """CRUD operations for task session logs."""

    def __init__(self):
        self.db = get_database()

    def log_session(
        self,
        user_id: int,
        task_id: int,
        duration_minutes: int,
        notes: Optional[str] = None,
    ) -> tuple[bool, str, Optional[Session]]:
        """Create a session record for a task."""
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

            return True, "Session logged successfully!", session
        except Exception as exc:
            return False, f"Failed to log session: {str(exc)}", None

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
