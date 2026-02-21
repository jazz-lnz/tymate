"""
TYMATE Onboarding Manager
Handles initial time budget setup for working students
Concept: Budget your time like you budget money
UPDATED: Now accounts for wake time, bedtime, and real-time calculations
"""

from datetime import datetime, time, timedelta
from typing import Dict, Optional
from storage.sqlite import get_database

class OnboardingManager:
    """
    Manages the onboarding process to calculate user's time budget
    
    Core Concept:
    - Total hours in a day: 24 hours
    - Subtract sleep: 24 - sleep_hours = waking_hours
    - Subtract work (if applicable): waking_hours - work_hours = free_hours
    - User allocates free_hours to tasks (like budgeting money)
    - NOW: Accounts for wake time and bedtime for realistic calculations
    """
    
    def __init__(self):
        self.db = get_database()
    
    @staticmethod
    def parse_wake_time(wake_time_str: str) -> time:
        """Parse wake time string (HH:MM) to time object"""
        hour, minute = map(int, wake_time_str.split(':'))
        return time(hour, minute)
    
    @staticmethod
    def calculate_bedtime(wake_time: time, sleep_hours: float) -> time:
        """
        Calculate bedtime based on wake time and sleep hours
        
        Example:
        - Wake at 8:00 AM, sleep 8 hours → bedtime is 12:00 AM (midnight)
        - Wake at 7:00 AM, sleep 7 hours → bedtime is 12:00 AM (midnight)
        """
        today = datetime.now().date()
        wake_datetime = datetime.combine(today, wake_time)
        bedtime_datetime = wake_datetime - timedelta(hours=sleep_hours)
        
        if bedtime_datetime.date() < today:
            bedtime_datetime = bedtime_datetime + timedelta(days=1)
        
        return bedtime_datetime.time()
    
    @staticmethod
    def get_hours_until_bedtime(current_time, wake_time, sleep_hours):
        """
        Calculate hours from current time until next bedtime.
        Handles edge case where bedtime is early morning (e.g., 2 AM from 7 AM wake with 5h sleep).
        
        Args:
            current_time: Current datetime
            wake_time: Wake time as time object
            sleep_hours: Hours of sleep
            
        Returns:
            Hours until next bedtime (positive value)
        """
        bedtime = OnboardingManager.calculate_bedtime(wake_time, sleep_hours)
        
        today = current_time.date()
        bed_today = datetime.combine(today, bedtime)
        
        # Critical fix: If bedtime is before current time (e.g., 2 AM when it's 9 AM),
        # bedtime already happened - the next bedtime is tomorrow
        if bed_today <= current_time:
            bed_today = bed_today + timedelta(days=1)
        
        hours = (bed_today - current_time).total_seconds() / 3600
        return hours
    
    @staticmethod
    def get_hours_since_wake(current_time: datetime, wake_time: time) -> float:
        """Calculate how many hours have passed since wake time"""
        today = current_time.date()
        wake_dt = datetime.combine(today, wake_time)
        
        if current_time < wake_dt:
            yesterday_wake = wake_dt - timedelta(days=1)
            if current_time > yesterday_wake:
                time_since_wake = current_time - yesterday_wake
                return time_since_wake.total_seconds() / 3600
            return 0
        
        time_since_wake = current_time - wake_dt
        return time_since_wake.total_seconds() / 3600
    
    def calculate_time_budget(
        self,
        sleep_hours: float = 8.0,
        has_work: bool = False,
        work_hours_per_week: float = 0.0,
        work_days_per_week: int = 0,
        wake_time: str = "07:00"
    ) -> Dict[str, float]:
        """
        Calculate user's available time budget
        
        Args:
            sleep_hours: Hours of sleep per day (default: 8)
            has_work: Whether user has a job
            work_hours_per_week: Total work hours per week
            work_days_per_week: How many days they work
            wake_time: What time user wakes up (HH:MM format)
            
        Returns:
            Dictionary with time budget breakdown
        """
        
        # Base calculation
        total_hours_per_day = 24.0
        waking_hours_per_day = total_hours_per_day - sleep_hours
        
        # Calculate work hours per day (average)
        if has_work and work_hours_per_week > 0:
            work_hours_per_day = work_hours_per_week / 7
        else:
            work_hours_per_day = 0.0
        
        # Calculate free hours (available for tasks)
        free_hours_per_day = waking_hours_per_day - work_hours_per_day
        
        # Weekly calculations
        waking_hours_per_week = waking_hours_per_day * 7
        work_hours_per_week_actual = work_hours_per_week if has_work else 0.0
        free_hours_per_week = free_hours_per_day * 7
        
        # Calculate bedtime
        wake_time_obj = self.parse_wake_time(wake_time)
        bedtime_obj = self.calculate_bedtime(wake_time_obj, sleep_hours)
        
        return {
            # Daily breakdown
            "total_hours_per_day": total_hours_per_day,
            "sleep_hours_per_day": sleep_hours,
            "waking_hours_per_day": waking_hours_per_day,
            "work_hours_per_day": work_hours_per_day,
            "free_hours_per_day": free_hours_per_day,
            
            # Weekly breakdown
            "waking_hours_per_week": waking_hours_per_week,
            "work_hours_per_week": work_hours_per_week_actual,
            "free_hours_per_week": free_hours_per_week,
            
            # Time of day info
            "wake_time": wake_time,
            "bedtime": bedtime_obj.strftime("%H:%M"),
            
            # Additional info
            "has_work": has_work,
            "work_days_per_week": work_days_per_week if has_work else 0,
        }
    
    def save_user_profile(
        self,
        user_id: int,
        sleep_hours: float,
        has_work: bool,
        wake_time: str = "07:00",
        work_hours_per_week: float = 0.0,
        work_days_per_week: int = 0,
        study_goal_hours_per_day: Optional[float] = None
    ) -> bool:
        """
        Save user's onboarding profile and time budget
        
        Args:
            user_id: User ID
            sleep_hours: Hours of sleep per day
            has_work: Whether user has a job
            wake_time: What time user wakes up (HH:MM format)
            work_hours_per_week: Total work hours per week
            work_days_per_week: Days worked per week
            study_goal_hours_per_day: Optional study goal (recommended: 4-6 hours)
            
        Returns:
            True if successful
        """
        
        # Calculate time budget
        budget = self.calculate_time_budget(
            sleep_hours=sleep_hours,
            has_work=has_work,
            work_hours_per_week=work_hours_per_week,
            work_days_per_week=work_days_per_week,
            wake_time=wake_time
        )
        
        # Recommend study goal if not provided (30-40% of free time)
        if study_goal_hours_per_day is None:
            study_goal_hours_per_day = budget["free_hours_per_day"] * 0.35
        
        timestamp = datetime.now().isoformat()
        
        # Update users table with onboarding data
        self.db.update("users", {
            "sleep_hours": sleep_hours,
            "wake_time": wake_time,
            "has_work": 1 if has_work else 0,
            "work_hours_per_week": work_hours_per_week,
            "work_days_per_week": work_days_per_week,
            "study_goal_hours_per_day": study_goal_hours_per_day,
            "updated_at": timestamp,
        }, "id = ?", (user_id,))
        
        # Mark onboarding as completed in settings
        self.db.execute_query("""
            INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, "onboarding_completed", "true", timestamp))

        self.db.execute_query("""
            INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, "onboarding_date", timestamp, timestamp))
        
        self.db.commit()
        
        # Create default time budget entry
        self.db.insert("time_budgets", {
            "user_id": user_id,
            "category": "Study",
            "budget_type": "daily",
            "budget_hours": study_goal_hours_per_day,
            "start_date": datetime.now().date().isoformat(),
            "created_at": timestamp,
            "updated_at": timestamp,
        })
        
        return True
    
    def get_user_budget(self, user_id: int) -> Optional[Dict]:
        """
        Get user's current time budget
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with budget info or None if not set up
        """
        
        # Check if onboarding completed
        completed = self.db.fetch_one(
            "SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = ?",
            (user_id, "onboarding_completed")
        )
        
        if not completed or completed['setting_value'] != 'true':
            return None
        
        # Fetch user data from users table
        user = self.db.get_by_id("users", user_id)
        
        if not user:
            return None
        
        # Calculate bedtime
        wake_time_obj = self.parse_wake_time(user['wake_time'])
        bedtime_obj = self.calculate_bedtime(wake_time_obj, user['sleep_hours'])
        
        # Calculate work hours per day
        work_hours_per_day = user['work_hours_per_week'] / 7 if user['has_work'] else 0.0
        
        # Calculate free hours
        waking_hours_per_day = 24 - user['sleep_hours']
        free_hours_per_day = waking_hours_per_day - work_hours_per_day
        
        # Convert to dictionary
        return {
            "sleep_hours": user['sleep_hours'],
            "wake_time": user['wake_time'],
            "bedtime": bedtime_obj.strftime("%H:%M"),
            "has_work": bool(user['has_work']),
            "work_hours_per_week": user['work_hours_per_week'],
            "work_hours_per_day": work_hours_per_day,
            "work_days_per_week": user['work_days_per_week'],
            "study_goal_hours_per_day": user['study_goal_hours_per_day'],
            "waking_hours_per_day": waking_hours_per_day,
            "free_hours_per_day": free_hours_per_day,
            "free_hours_per_week": free_hours_per_day * 7,
        }
    
    def get_time_spent_today(self, user_id: int) -> Dict[str, float]:
        """
        Calculate how much time user has spent today
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with time spent by category
        """
        today = datetime.now().date().isoformat()
        
        # Get time logs for today
        time_logs = self.db.fetch_all("""
            SELECT category, SUM(hours) as total_hours
            FROM time_logs
            WHERE user_id = ? AND date = ?
            GROUP BY category
        """, (user_id, today))
        
        result = {
            "Study": 0.0,
            "Work": 0.0,
            "Personal": 0.0,
            "total": 0.0
        }
        
        for log in time_logs:
            category = log['category']
            hours = log['total_hours']
            result[category] = hours
            result['total'] += hours
        
        return result
    
    def get_time_spent_this_week(self, user_id: int) -> float:
        """
        Calculate total hours logged this week
        Uses actual_time from completed tasks as fallback when time_logs is empty
        
        Args:
            user_id: User ID
            
        Returns:
            Total hours spent this week
        """
        # Get start of week (Monday)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Try time_logs first
        result = self.db.fetch_one("""
            SELECT SUM(hours) as total_hours
            FROM time_logs
            WHERE user_id = ?
            AND date >= ?
        """, (user_id, start_of_week.isoformat()))
        
        if result and result["total_hours"]:
            return result["total_hours"]
        
        # Fallback: sum task session minutes logged this week
        session_minutes = self.db.fetch_one("""
            SELECT SUM(duration_minutes) as total_minutes
            FROM task_sessions
            WHERE user_id = ?
            AND DATE(logged_at) >= ?
            AND is_deleted = 0
        """, (user_id, start_of_week.isoformat()))

        if session_minutes and session_minutes["total_minutes"]:
            return round(session_minutes["total_minutes"] / 60.0, 2)
        return 0.0
    
    def get_remaining_budget(self, user_id: int, current_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calculate remaining time budget for today with REAL-TIME AWARENESS
        Like checking your bank account balance, but also considering store closing time!
        
        Args:
            user_id: User ID
            current_time: Current time (defaults to now)
            
        Returns:
            Dictionary with remaining hours (realistic and absolute)
        """
        
        if current_time is None:
            current_time = datetime.now()
        
        budget = self.get_user_budget(user_id)
        if not budget:
            return {"error": "Budget not set up"}
        
        spent = self.get_time_spent_today(user_id)
        
        # Parse wake time
        wake_time = self.parse_wake_time(budget["wake_time"])
        sleep_hours = budget["sleep_hours"]
        
        # Calculate time metrics with pre-wake handling
        today = current_time.date()
        wake_dt_today = datetime.combine(today, wake_time)
        
        # For evening wake times (noon or later), reference yesterday's wake
        if wake_time.hour >= 12:
            # Evening wake time (e.g., 11 PM)
            yesterday = today - timedelta(days=1)
            wake_dt_reference = datetime.combine(yesterday, wake_time)
            
            # Check if we're still within the same "day" (after yesterday's evening wake)
            if current_time >= wake_dt_reference:
                is_before_wake = False
                hours_since_wake = (current_time - wake_dt_reference).total_seconds() / 3600
                hours_until_wake = 0.0
                # Bedtime is sleep_hours after yesterday's wake
                bedtime_obj = self.calculate_bedtime(wake_time, sleep_hours)
                bed_dt = datetime.combine(today, bedtime_obj)
                if current_time >= bed_dt:
                    # Past bedtime, calculate for tomorrow
                    bed_dt = datetime.combine(today + timedelta(days=1), bedtime_obj)
                hours_until_bedtime = (bed_dt - current_time).total_seconds() / 3600
            else:
                # Before yesterday's evening wake (shouldn't happen but fallback)
                is_before_wake = True
                hours_until_wake = (wake_dt_today - current_time).total_seconds() / 3600
                hours_since_wake = 0.0
                hours_until_bedtime = budget["waking_hours_per_day"]
        else:
            # Morning wake time (standard case)
            if current_time < wake_dt_today:
                is_before_wake = True
                hours_until_wake = (wake_dt_today - current_time).total_seconds() / 3600
                hours_since_wake = 0.0
                hours_until_bedtime = budget["waking_hours_per_day"]
            else:
                is_before_wake = False
                hours_until_wake = 0.0
                hours_since_wake = self.get_hours_since_wake(current_time, wake_time)
                hours_until_bedtime = self.get_hours_until_bedtime(current_time, wake_time, sleep_hours)
        
        # Calculate remaining free time
        free_hours_budget = budget["free_hours_per_day"]
        free_remaining_absolute = max(0, free_hours_budget - spent["total"])
        free_remaining_realistic = min(free_remaining_absolute, max(0, hours_until_bedtime))
        
        # Calculate remaining study time (based on goal)
        study_goal = budget["study_goal_hours_per_day"]
        study_remaining_absolute = max(0, study_goal - spent.get("Study", 0))
        study_remaining_realistic = min(study_remaining_absolute, max(0, hours_until_bedtime))
        
        # Progress percentages
        waking_hours = budget["waking_hours_per_day"]
        day_progress = (hours_since_wake / waking_hours * 100) if waking_hours > 0 else 0
        study_progress = (spent.get("Study", 0) / study_goal * 100) if study_goal > 0 else 0
        
        # Status messages for time of day
        if is_before_wake:
            time_status = f"Day hasn't started yet. Wake in {hours_until_wake:.1f}h"
            time_status_color = "blue"
        elif hours_until_bedtime <= 0:
            time_status = "Past bedtime! Time to sleep."
            time_status_color = "red"
        elif hours_until_bedtime < 2:
            time_status = f"Only {hours_until_bedtime:.1f} hours until bedtime!"
            time_status_color = "orange"
        elif hours_until_bedtime < 4:
            time_status = f"{hours_until_bedtime:.1f} hours remaining today"
            time_status_color = "yellow"
        else:
            time_status = f"{hours_until_bedtime:.1f} hours remaining today"
            time_status_color = "green"
        
        # Status messages for study progress
        if study_remaining_realistic <= 0:
            study_status = "Study goal completed!" if spent.get("Study", 0) >= study_goal else "No time left today"
            study_status_color = "green" if spent.get("Study", 0) >= study_goal else "red"
        elif study_remaining_realistic < study_remaining_absolute:
            study_status = f"{study_remaining_realistic:.1f}h left (limited by bedtime)"
            study_status_color = "orange"
        else:
            study_status = f"{study_remaining_realistic:.1f}h remaining for study goal"
            study_status_color = "blue"
        
        return {
            # Time of day info
            "current_time": current_time.strftime("%I:%M %p"),
            "wake_time": wake_time.strftime("%I:%M %p"),
            "bedtime": budget["bedtime"],
            "hours_since_wake": round(hours_since_wake, 1),
            "hours_until_bedtime": round(hours_until_bedtime, 1),
            "hours_until_wake": round(hours_until_wake, 1),
            "day_progress_percent": round(day_progress, 1),
            
            # Absolute remaining (if time wasn't a constraint)
            "free_hours_remaining_absolute": round(free_remaining_absolute, 1),
            "study_hours_remaining_absolute": round(study_remaining_absolute, 1),
            
            # Realistic remaining (constrained by bedtime)
            "free_hours_remaining": round(free_remaining_realistic, 1),
            "study_hours_remaining": round(study_remaining_realistic, 1),
            
            # Spent
            "study_hours_spent": spent.get("Study", 0),
            "work_hours_spent": spent.get("Work", 0),
            "total_hours_spent": spent["total"],
            
            # Goals and budgets
            "study_goal": study_goal,
            "free_hours_budget": free_hours_budget,
            
            # Progress
            "study_progress_percent": round(study_progress, 1),
            
            # Status
            "time_status": time_status,
            "time_status_color": time_status_color,
            "study_status": study_status,
            "study_status_color": study_status_color,
            
            # Flags
            "is_past_bedtime": hours_until_bedtime <= 0,
            "is_before_wake": is_before_wake,
            "study_goal_met": spent.get("Study", 0) >= study_goal,
            "time_constrained": study_remaining_realistic < study_remaining_absolute,
        }
    
    def needs_onboarding(self, user_id: int) -> bool:
        """
        Check if user needs to complete onboarding
        
        Args:
            user_id: User ID
            
        Returns:
            True if onboarding needed
        """
        completed = self.db.fetch_one(
            "SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = ?",
            (user_id, "onboarding_completed")
        )
        
        return not completed or completed['setting_value'] != 'true'