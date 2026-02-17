from datetime import datetime, timedelta
from typing import List, Optional
from storage.sqlite import get_database
from models.task import Task
from state.session_manager import SessionManager

class TaskManager:
    """
    Manages task operations (Create, Read, Update, Delete)
    """
    
    def __init__(self):
        self.db = get_database()
    
    # ==================== CREATE ====================
    
    def create_task(
        self, 
        user_id: int,
        title: str,
        source: str,
        category: str,
        date_given: str,
        date_due: str,
        description: str = None,
        estimated_time: int = None,
        status: str = "Not Started",
        completed_at: str = None,
    ) -> tuple[bool, str, Optional[Task]]:
        
        # Validate
        if not title or not title.strip():
            return False, "Task title is required", None
        
        # Create task object
        task = Task(
            user_id=user_id,
            title=title.strip(),
            source=source,
            category=category,
            date_given=date_given,
            date_due=date_due,
            description=description,
            estimated_time=estimated_time,
            status=status,
            completed_at=completed_at,
        )
        
        try:
            # Save to database
            task_data = task.to_dict()
            task_data.pop("id")  # Let DB auto-generate
            
            task_id = self.db.insert("tasks", task_data)
            task.id = task_id
            
            return True, "Task created successfully!", task
            
        except Exception as e:
            return False, f"Failed to create task: {str(e)}", None
    
    # ==================== READ ====================

    def get_task(self, task_id: int, include_deleted: bool = False) -> Optional[Task]:
        """
        Get a single task by ID
        
        Args:
            task_id: Task ID
            include_deleted: when True, return task even if soft-deleted

        Returns:
            Task object or None
        """
        if include_deleted:
            query = "SELECT * FROM tasks WHERE id = ?"
        else:
            query = "SELECT * FROM tasks WHERE id = ? AND is_deleted = 0"

        task_data = self.db.fetch_one(query, (task_id,))

        if task_data:
            return Task.from_dict(task_data)
        return None
    
    def get_user_tasks(
        self,
        user_id: int,
        status_filter: str = None,
        category_filter: str = None,
        include_deleted: bool = False
    ) -> List[Task]:
        """
        Get all tasks for a user with optional filters
        
        Args:
            user_id: User ID
            status_filter: Filter by status (optional)
            category_filter: Filter by category (optional)
            include_deleted: Include deleted tasks
            
        Returns:
            List of Task objects
        """
        
        # Build query
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]
        
        if not include_deleted:
            query += " AND is_deleted = 0"
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
        
        query += " ORDER BY created_at DESC"
        
        # Execute query
        tasks_data = self.db.fetch_all(query, tuple(params))
        
        # Convert to Task objects
        return [Task.from_dict(data) for data in tasks_data]
    
    def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """Get all overdue tasks for a user"""
        all_tasks = self.get_user_tasks(user_id)
        return [task for task in all_tasks if task.is_overdue()]
    
    def get_upcoming_tasks(self, user_id: int, limit: int = 5) -> List[Task]:
        """Get upcoming tasks (not completed, sorted by due date)"""
        tasks = self.db.fetch_all("""
            SELECT * FROM tasks
            WHERE user_id = ?
            AND is_deleted = 0
            AND status != 'Completed'
            ORDER BY
                CASE WHEN date_due IS NULL THEN 1 ELSE 0 END,
                date_due ASC
            LIMIT ?
        """, (user_id, limit))
        
        return [Task.from_dict(data) for data in tasks]
    
    def get_task_stats(self, user_id: int) -> dict:
        """Get task statistics for a user"""
        stats = {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
            "overdue": 0,
        }
        
        tasks = self.get_user_tasks(user_id)
        stats["total"] = len(tasks)
        
        for task in tasks:
            if task.status == "Completed":
                stats["completed"] += 1
            elif task.status == "In Progress":
                stats["in_progress"] += 1
            elif task.status == "Not Started":
                stats["not_started"] += 1
            
            if task.is_overdue():
                stats["overdue"] += 1
        
        return stats
    
    def get_tasks_completed_today(self, user_id: int) -> int:
        """Get count of tasks completed today"""
        today = datetime.now().date().isoformat()
        result = self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE user_id = ?
            AND DATE(completed_at) = ?
            AND is_deleted = 0
        """, (user_id, today))
        return result["count"] if result else 0
    
    def get_completion_rate(self, user_id: int, days: int = 30) -> float:
        """Get completion rate percentage for last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get total tasks created in period
        total = self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE user_id = ?
            AND date_given >= ?
            AND is_deleted = 0
        """, (user_id, cutoff_date))
        
        # Get completed tasks in period
        completed = self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE user_id = ?
            AND date_given >= ?
            AND status = 'Completed'
            AND is_deleted = 0
        """, (user_id, cutoff_date))
        
        if not total or total["count"] == 0:
            return 0.0
        
        return round((completed["count"] / total["count"]) * 100, 1)
    
    # ==================== UPDATE ====================
    
    def update_task(
        self,
        task_id: int,
        **updates
    ) -> tuple[bool, str]:
        """
        Update a task
        
        Args:
            task_id: Task ID
            **updates: Fields to update (title, description, status, etc.)
            
        Returns:
            Tuple of (success: bool, message: str)
        """

        # Check task exists (allow soft-deleted in case caller wants to restore/update)
        task = self.get_task(task_id, include_deleted=True)
        if not task:
            return False, "Task not found"
        
        # Add updated timestamp
        updates["updated_at"] = datetime.now().isoformat()
        
        # If marking as completed, set completed_at
        if updates.get("status") == "Completed" and task.status != "Completed":
            updates["completed_at"] = datetime.now().isoformat()
        
        try:
            self.db.update("tasks", updates, "id = ?", (task_id,))
            return True, "Task updated successfully!"
        except Exception as e:
            return False, f"Failed to update task: {str(e)}"
    
    def mark_complete(
        self,
        task_id: int,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Mark a task as completed and optionally log a session."""
        task = self.get_task(task_id, include_deleted=True)
        if not task:
            return False, "Task not found"

        if duration_minutes is not None:
            session_manager = SessionManager()
            ok, msg, _ = session_manager.log_session(
                user_id=task.user_id,
                task_id=task_id,
                duration_minutes=duration_minutes,
                notes=notes,
            )
            if not ok:
                return False, msg

        updates = {
            "status": "Completed",
            "completed_at": datetime.now().isoformat(),
        }

        return self.update_task(task_id, **updates)

    def mark_in_progress(self, task_id: int) -> tuple[bool, str]:
        """Mark a task as in progress"""
        return self.update_task(task_id, status="In Progress")
    
    # ==================== DELETE ====================
    
    def delete_task(self, task_id: int, soft_delete: bool = True) -> tuple[bool, str]:
        """
        Delete a task (soft or hard delete)
        
        Args:
            task_id: Task ID
            soft_delete: If True, mark as deleted. If False, permanently delete.
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        # Check task exists
        task = self.get_task(task_id)
        if not task:
            return False, "Task not found"
        
        try:
            if soft_delete:
                # Soft delete (mark as deleted)
                self.db.update(
                    "tasks",
                    {
                        "is_deleted": 1,
                        "deleted_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "id = ?",
                    (task_id,)
                )
                return True, "Task moved to trash"
            else:
                # Hard delete (permanently remove)
                self.db.delete("tasks", "id = ?", (task_id,))
                return True, "Task permanently deleted"
                
        except Exception as e:
            return False, f"Failed to delete task: {str(e)}"
    
    def restore_task(self, task_id: int) -> tuple[bool, str]:
        """Restore a soft-deleted task"""
        try:
            self.db.update(
                "tasks",
                {
                    "is_deleted": 0,
                    "deleted_at": None,
                    "updated_at": datetime.now().isoformat()
                },
                "id = ?",
                (task_id,)
            )
            return True, "Task restored successfully!"
        except Exception as e:
            return False, f"Failed to restore task: {str(e)}"


# Example usage
if __name__ == "__main__":
    manager = TaskManager()
    
    # Create a task
    success, msg, task = manager.create_task(
        user_id=1,
        title="Complete CS 319 Project",
        description="Implement RBAC and security features",
        category="School",
        priority="High",
        due_date="2025-12-10"
    )
    
    print(f"Create: {msg}")
    if task:
        print(f"Created task: {task}")
        
        # Update task
        success, msg = manager.update_task(
            task.id,
            status="In Progress"
        )
        print(f"Update: {msg}")
        
        # Get task stats
        stats = manager.get_task_stats(1)
        print(f"Stats: {stats}")