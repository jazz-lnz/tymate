from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .session import Session

@dataclass
class Task:
    """
    Task data model (Invoice-style for students)
    
    Attributes:
        id: Task ID (auto-generated)
        user_id: Owner user ID
        title: Task name/title *REQUIRED*
        source: Who assigned it (course name, workplace, or "Personal") *REQUIRED*
        category: Type of task *REQUIRED* - fixed options
        date_given: When task was assigned (YYYY-MM-DD) *REQUIRED*
        date_due: Due date (YYYY-MM-DD) *REQUIRED*
        description: Detailed description (optional)
        estimated_time: Estimated minutes to complete (optional)
        status: Current status (Not Started, In Progress, Completed)
        completed_at: When task was completed
        created_at: When task was created in system
        updated_at: Last modification time
        is_deleted: Soft delete flag
        deleted_at: When task was deleted
    """
    
    # Required fields (invoice-style)
    user_id: int
    title: str
    source: str  # Course name, Workplace, or "Personal" - free text
    category: str  # Must be one of CATEGORIES
    date_given: str  # YYYY-MM-DD
    date_due: str  # YYYY-MM-DD
    
    # Optional fields
    id: Optional[int] = None
    description: Optional[str] = None
    estimated_time: Optional[int] = None
    sessions: Optional[list["Session"]] = None
    status: str = "Not Started"
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided"""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for database storage"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "source": self.source,
            "category": self.category,
            "date_given": self.date_given,
            "date_due": self.date_due,
            "description": self.description,
            "estimated_time": self.estimated_time,
            "status": self.status,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": 1 if self.is_deleted else 0,
            "deleted_at": self.deleted_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create Task instance from dictionary (from database)"""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            title=data["title"],
            source=data["source"],
            category=data["category"],
            date_given=data["date_given"],
            date_due=data["date_due"],
            description=data.get("description"),
            estimated_time=data.get("estimated_time"),
            status=data.get("status", "Not Started"),
            completed_at=data.get("completed_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_deleted=bool(data.get("is_deleted", 0)),
            deleted_at=data.get("deleted_at"),
        )
    
    def mark_complete(self):
        """Mark task as completed"""
        self.status = "Completed"
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def compute_actual_minutes(self, sessions: list["Session"]) -> int:
        """Pass in session objects, get total minutes back."""
        return sum(
            session.duration_minutes
            for session in sessions
            if not session.is_deleted and session.duration_minutes is not None
        )

    @property
    def actual_time(self) -> Optional[int]:
        """Backwards-compatible alias for total minutes."""
        if not self.sessions:
            return None
        return self.compute_actual_minutes(self.sessions)
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.date_due or self.status == "Completed":
            return False
        
        try:
            due = datetime.fromisoformat(self.date_due)
            return datetime.now().date() > due.date()
        except:
            return False
    
    def days_to_complete(self) -> Optional[int]:
        """
        Calculate days from date_given to completion
        Returns None if not completed
        """
        if not self.completed_at or not self.date_given:
            return None
        
        try:
            given = datetime.fromisoformat(self.date_given).date()
            completed = datetime.fromisoformat(self.completed_at).date()
            return (completed - given).days
        except:
            return None
    
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if not self.date_due:
            return None
        
        try:
            due = datetime.fromisoformat(self.date_due).date()
            today = datetime.now().date()
            return (due - today).days
        except:
            return None
    
    def is_group_task(self) -> bool:
        """Check if task is a group task"""
        return "group" in self.category.lower()
    
    def time_accuracy(self) -> Optional[float]:
        """
        Calculate estimation accuracy (for analytics)
        Returns None if no estimated or actual time
        Returns positive if underestimated, negative if overestimated
        """
        if self.estimated_time is None or not self.sessions:
            return None

        return self.compute_actual_minutes(self.sessions) - self.estimated_time
    
    def get_implicit_priority(self) -> str:
        """
        Get implicit priority based on category
        quiz < learning task < project (for analytics)
        """
        category_lower = self.category.lower()
        if "quiz" in category_lower:
            return "Low"
        elif "learning task" in category_lower:
            return "Medium"
        elif "project" in category_lower:
            return "High"
        else:
            return "Medium"
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"Task(id={self.id}, title='{self.title}', source='{self.source}', status='{self.status}')"


# Category constants (fixed options for dropdown)
CATEGORIES = [
    "quiz",
    "learning task (individual)",
    "learning task (group)",
    "project (individual)",
    "project (group)",
    "study/review",
    "others"
]

STATUSES = ["Not Started", "In Progress", "Completed"]