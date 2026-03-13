import calendar
import json
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

    def _log_task_event(
        self,
        user_id: int,
        task_id: int,
        event_type: str,
        message: Optional[str] = None,
        metadata: Optional[dict] = None,
        created_at: Optional[str] = None,
    ):
        """Write a task lifecycle event entry."""
        try:
            self.db.insert(
                "task_events",
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "event_type": event_type,
                    "message": message,
                    "metadata": json.dumps(metadata or {}),
                    "created_at": created_at or datetime.now().isoformat(),
                },
            )
        except Exception:
            # Event logs should not block the primary task operation.
            pass

    def get_task_events(self, task_id: int) -> List[dict]:
        """Fetch timeline events for one task (newest first)."""
        rows = self.db.fetch_all(
            """
            SELECT * FROM task_events
            WHERE task_id = ?
            ORDER BY created_at DESC
            """,
            (task_id,),
        )
        return rows

    @staticmethod
    def _normalize_minutes(value) -> Optional[int]:
        """Normalize minute inputs to optional int minutes."""
        if value is None or value == "":
            return None

        try:
            minutes = int(value)
        except (TypeError, ValueError):
            raise ValueError("Minutes must be an integer")

        if minutes < 0:
            raise ValueError("Minutes cannot be negative")

        return minutes

    @staticmethod
    def _parse_iso_date(value: Optional[str]):
        """Parse YYYY-MM-DD (or ISO datetime) into date, or return None."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    
    # ==================== CREATE ====================
    
    def create_task(
        self, 
        user_id: int,
        title: str,
        source: str,
        category: str,
        date_given: str,
        date_due: Optional[str],
        description: str = None,
        estimated_time: Optional[int] = None,
        status: str = "Not Started",
        is_recurring: bool = False,
        recurrence_type: Optional[str] = None,
        recurrence_interval: int = 1,
        recurrence_until: Optional[str] = None,
        completed_at: str = None,
    ) -> tuple[bool, str, Optional[Task]]:
        
        # Validate
        if not title or not title.strip():
            return False, "Task title is required", None
        
        try:
            estimated_minutes = self._normalize_minutes(estimated_time)
        except ValueError as e:
            return False, str(e), None

        try:
            recurrence_interval = int(recurrence_interval)
            if recurrence_interval < 1:
                return False, "Recurrence interval must be at least 1", None
        except (TypeError, ValueError):
            return False, "Recurrence interval must be an integer", None

        recurrence_type = recurrence_type.lower() if recurrence_type else None
        if recurrence_type and recurrence_type not in ("daily", "weekly", "monthly"):
            return False, "Recurrence type must be daily, weekly, or monthly", None
        if not is_recurring:
            recurrence_type = None
            recurrence_interval = 1
            recurrence_until = None

        if recurrence_until:
            recurrence_until = recurrence_until.strip()
            if not self._parse_iso_date(recurrence_until):
                return False, "Repeat-until date must be YYYY-MM-DD", None

        # Create task object
        task = Task(
            user_id=user_id,
            title=title.strip(),
            source=source,
            category=category,
            date_given=date_given,
            date_due=date_due,
            description=description,
            estimated_time=estimated_minutes,
            status=status,
            is_recurring=is_recurring,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_until=recurrence_until,
            completed_at=completed_at,
        )
        
        try:
            # Save to database
            task_data = task.to_dict()
            task_data.pop("id")  # Let DB auto-generate
            
            task_id = self.db.insert("tasks", task_data)
            task.id = task_id
            self._log_task_event(
                user_id=user_id,
                task_id=task_id,
                event_type="TASK_CREATED",
                message="Task created",
                metadata={
                    "title": task.title,
                    "status": task.status,
                    "date_due": task.date_due,
                },
            )
            
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
            elif task.status in ("Started", "In Progress"):
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
        event_date: Optional[str] = None,
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
        
        if "estimated_time" in updates:
            try:
                updates["estimated_time"] = self._normalize_minutes(updates.get("estimated_time"))
            except ValueError as e:
                return False, str(e)

        if "recurrence_type" in updates and updates.get("recurrence_type"):
            normalized_recurrence = str(updates.get("recurrence_type")).lower()
            if normalized_recurrence not in ("daily", "weekly", "monthly"):
                return False, "Recurrence type must be daily, weekly, or monthly"
            updates["recurrence_type"] = normalized_recurrence

        if "recurrence_interval" in updates:
            try:
                recurrence_interval = int(updates.get("recurrence_interval"))
            except (TypeError, ValueError):
                return False, "Recurrence interval must be an integer"
            if recurrence_interval < 1:
                return False, "Recurrence interval must be at least 1"
            updates["recurrence_interval"] = recurrence_interval

        if "is_recurring" in updates and not updates.get("is_recurring"):
            updates["recurrence_type"] = None
            updates["recurrence_interval"] = 1
            updates["recurrence_until"] = None

        if "recurrence_until" in updates and updates.get("recurrence_until"):
            recurrence_until = str(updates.get("recurrence_until")).strip()
            if not self._parse_iso_date(recurrence_until):
                return False, "Repeat-until date must be YYYY-MM-DD"
            updates["recurrence_until"] = recurrence_until
        elif "recurrence_until" in updates:
            updates["recurrence_until"] = None

        # Add updated timestamp
        updates["updated_at"] = datetime.now().isoformat()
        
        # If marking as completed, set completed_at (use event_date if caller supplied one)
        if updates.get("status") == "Completed" and task.status != "Completed":
            if "completed_at" not in updates:
                updates["completed_at"] = event_date or datetime.now().isoformat()
        
        try:
            self.db.update("tasks", updates, "id = ?", (task_id,))

            old_status = task.status
            new_status = updates.get("status", task.status)
            if "status" in updates and old_status != new_status:
                if new_status == "Completed":
                    event_type = "TASK_COMPLETED"
                    message = "Task marked as completed"
                elif old_status == "Completed" and new_status != "Completed":
                    event_type = "TASK_UNCOMPLETED"
                    message = f"Task moved back to {new_status}"
                elif new_status == "In Progress":
                    event_type = "TASK_STARTED"
                    message = "Task marked in progress"
                else:
                    event_type = "TASK_STATUS_UPDATED"
                    message = f"Task status changed to {new_status}"

                self._log_task_event(
                    user_id=task.user_id,
                    task_id=task_id,
                    event_type=event_type,
                    message=message,
                    metadata={"from": old_status, "to": new_status},
                    created_at=event_date,
                )
            else:
                changed_fields = [k for k in updates.keys() if k != "updated_at"]
                if changed_fields:
                    self._log_task_event(
                        user_id=task.user_id,
                        task_id=task_id,
                        event_type="TASK_UPDATED",
                        message="Task details updated",
                        metadata={"fields": changed_fields},
                    )

            return True, "Task updated successfully!"
        except Exception as e:
            return False, f"Failed to update task: {str(e)}"
    
    def mark_complete(
        self,
        task_id: int,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
        event_date: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Mark a task as completed and optionally log a session."""
        task = self.get_task(task_id, include_deleted=False)
        if not task:
            return False, "Task not found"

        if duration_minutes is not None:
            try:
                normalized_duration = self._normalize_minutes(duration_minutes)
            except ValueError as e:
                return False, str(e)

            if normalized_duration == 0:
                return False, "Duration must be greater than 0 minutes"

            session_manager = SessionManager()
            ok, msg, _ = session_manager.log_session(
                user_id=task.user_id,
                task_id=task_id,
                duration_minutes=normalized_duration,
                notes=notes,
            )
            if not ok:
                return False, msg

        updates = {
            "status": "Completed",
            "completed_at": event_date or datetime.now().isoformat(),
        }

        ok, msg = self.update_task(task_id, event_date=event_date, **updates)
        if not ok:
            return ok, msg

        if task.is_recurring and task.recurrence_type:
            next_due_date = self._compute_next_due_date(
                task.date_due,
                task.date_given,
                task.recurrence_type,
                task.recurrence_interval,
            )

            repeat_until_date = self._parse_iso_date(task.recurrence_until)
            next_due = self._parse_iso_date(next_due_date)
            if repeat_until_date and next_due and next_due > repeat_until_date:
                return True, "Task completed. Repeat-until reached, no new occurrence created"

            created, create_msg, _ = self.create_task(
                user_id=task.user_id,
                title=task.title,
                source=task.source,
                category=task.category,
                date_given=datetime.now().date().isoformat(),
                date_due=next_due_date,
                description=task.description,
                estimated_time=task.estimated_time,
                status="Not Started",
                is_recurring=True,
                recurrence_type=task.recurrence_type,
                recurrence_interval=task.recurrence_interval,
                recurrence_until=task.recurrence_until,
                completed_at=None,
            )
            if created:
                return True, "Task completed and next recurring task was created"
            return True, f"Task completed, but next recurring task was not created: {create_msg}"

        return ok, msg

    @staticmethod
    def _compute_next_due_date(
        date_due: Optional[str],
        date_given: Optional[str],
        recurrence_type: str,
        recurrence_interval: int,
    ) -> str:
        """Compute next due date for recurring task from a stable anchor date."""
        anchor_str = date_due or date_given or datetime.now().date().isoformat()
        try:
            anchor_date = datetime.fromisoformat(anchor_str).date()
        except ValueError:
            anchor_date = datetime.now().date()

        if recurrence_type == "daily":
            next_date = anchor_date + timedelta(days=recurrence_interval)
        elif recurrence_type == "weekly":
            next_date = anchor_date + timedelta(weeks=recurrence_interval)
        else:
            months_to_add = recurrence_interval
            month_index = anchor_date.month - 1 + months_to_add
            year = anchor_date.year + (month_index // 12)
            month = (month_index % 12) + 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(anchor_date.day, max_day)
            next_date = anchor_date.replace(year=year, month=month, day=day)

        return next_date.isoformat()

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
                        "is_recurring": 0,
                        "recurrence_type": None,
                        "recurrence_interval": 1,
                        "recurrence_until": None,
                        "deleted_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "id = ?",
                    (task_id,)
                )
                self._log_task_event(
                    user_id=task.user_id,
                    task_id=task_id,
                    event_type="TASK_DELETED",
                    message="Task moved to trash",
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
            task = self.get_task(task_id, include_deleted=True)
            if task:
                self._log_task_event(
                    user_id=task.user_id,
                    task_id=task_id,
                    event_type="TASK_RESTORED",
                    message="Task restored from trash",
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