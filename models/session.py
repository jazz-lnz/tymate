from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """
    Session data model for task time tracking

    Attributes:
        id: Session ID (auto-generated)
        user_id: Owner user ID
        task_id: Linked Task ID
        duration_minutes: Length of session in minutes
        notes: Optional notes for this session
        logged_at: When the session happened
        created_at: When the session was created in system
        is_deleted: Soft delete flag
        deleted_at: When session was deleted
    """

    user_id: int
    task_id: int
    duration_minutes: int
    notes: Optional[str] = None
    id: Optional[int] = None
    logged_at: Optional[str] = None
    created_at: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        now = datetime.now().isoformat()
        if not self.logged_at:
            self.logged_at = now
        if not self.created_at:
            self.created_at = now

    def to_dict(self) -> dict:
        """Convert session to dictionary for database storage"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
            "logged_at": self.logged_at,
            "created_at": self.created_at,
            "is_deleted": 1 if self.is_deleted else 0,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create Session instance from dictionary (from database)"""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            task_id=data["task_id"],
            duration_minutes=data["duration_minutes"],
            notes=data.get("notes"),
            logged_at=data.get("logged_at"),
            created_at=data.get("created_at"),
            is_deleted=bool(data.get("is_deleted", 0)),
            deleted_at=data.get("deleted_at"),
        )
