from datetime import date as date_type, datetime
from typing import List, Optional

from storage.sqlite import get_database


class ScheduleManager:
    """CRUD operations and free-time computation for class/work schedules."""

    BASIC_NEEDS_BUFFER_MINUTES = 90

    def __init__(self):
        self.db = get_database()

    def add_class_block(
        self,
        user_id: int,
        day_of_week: int,
        start_time: str,
        end_time: str,
        course_name: Optional[str] = None,
    ) -> tuple[bool, str, Optional[int]]:
        """Add a class schedule block for a user."""
        if day_of_week < 0 or day_of_week > 6:
            return False, "day_of_week must be between 0 and 6", None

        try:
            normalized_start = self._parse_time(start_time)
            normalized_end = self._parse_time(end_time)
        except ValueError:
            return False, "start_time and end_time must be in HH:MM format", None

        start_time_minutes = self._time_to_minutes(normalized_start)
        end_time_minutes = self._time_to_minutes(normalized_end)
        if end_time_minutes <= start_time_minutes:
            raise ValueError(
                "Class block must start and end on the same day — overnight ranges are not allowed."
            )

        now = datetime.now().isoformat()
        data = {
            "user_id": user_id,
            "day_of_week": day_of_week,
            "start_time": normalized_start,
            "end_time": normalized_end,
            "course_name": course_name,
            "location": None,
            "created_at": now,
            "updated_at": now,
        }

        try:
            block_id = self.db.insert("class_schedule", data)
            return True, "Class block added successfully", block_id
        except Exception as exc:
            return False, f"Failed to add class block: {str(exc)}", None

    def get_classes_for_day(self, user_id: int, day_of_week: int) -> List[dict]:
        """Return class blocks for a user on a given weekday (0=Monday)."""
        return self.db.fetch_all(
            """
            SELECT *
            FROM class_schedule
            WHERE user_id = ? AND day_of_week = ?
            ORDER BY start_time ASC
            """,
            (user_id, day_of_week),
        )

    def delete_class_block(self, block_id: int) -> tuple[bool, str]:
        """Delete a class block by ID."""
        try:
            deleted = self.db.delete("class_schedule", "id = ?", (block_id,))
            if deleted == 0:
                return False, "Class block not found"
            return True, "Class block deleted successfully"
        except Exception as exc:
            return False, f"Failed to delete class block: {str(exc)}"

    def compute_free_time_today(self, user_id: int, date) -> int:
        """
        Compute free time in minutes for a date.

        Logic:
        - Get user's wake_time + sleep_hours from users table
        - Compute total awake minutes for the day
        - Subtract class block minutes for that weekday
        - Subtract a fixed 90-minute basic-needs buffer
        """
        target_date = self._normalize_date(date)
        weekday = target_date.weekday()

        user = self.db.fetch_one(
            """
            SELECT wake_time, sleep_hours
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )

        wake_time = user["wake_time"] if user and user.get("wake_time") else "07:00"
        sleep_hours = float(user["sleep_hours"]) if user and user.get("sleep_hours") is not None else 8.0

        self._parse_time(wake_time)

        awake_minutes = max(0, int(round((24.0 - sleep_hours) * 60)))

        class_blocks = self.get_classes_for_day(user_id, weekday)
        intervals: list[tuple[int, int]] = []
        for block in class_blocks:
            try:
                start = self._time_to_minutes(block["start_time"])
                end = self._time_to_minutes(block["end_time"])
            except ValueError:
                continue

            if end <= start:
                continue

            intervals.append((start, end))

        intervals.sort(key=lambda item: item[0])
        merged: list[list[int]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)

        class_minutes = sum(end - start for start, end in merged)

        free_minutes = awake_minutes - class_minutes - self.BASIC_NEEDS_BUFFER_MINUTES
        return max(0, free_minutes)

    def _normalize_date(self, value) -> date_type:
        """Accept datetime/date/ISO date string and return date."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date_type):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value).date()
        raise ValueError("date must be a date, datetime, or ISO date string")

    def _parse_time(self, value: str) -> str:
        """Parse HH:MM or HH:MM:SS time strings and normalize to HH:MM."""
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                dt = datetime.strptime(value, fmt)
                return f"{dt.hour:02d}:{dt.minute:02d}"
            except ValueError:
                continue
        raise ValueError("Invalid time format")

    def _time_to_minutes(self, value: str) -> int:
        """Convert an HH:MM or HH:MM:SS string to absolute minutes from midnight."""
        normalized = self._parse_time(value)
        hours, minutes = normalized.split(":")
        return int(hours) * 60 + int(minutes)

    def _minutes_between(self, start_time: str, end_time: str) -> int:
        """Compute minutes between two normalized times."""
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)
        return max(0, end_minutes - start_minutes)
