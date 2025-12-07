"""
TYMATE Onboarding Manager
Handles initial time budget setup for working students
Concept: Budget your time like you budget money
"""

from datetime import datetime
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
    """
    
    def __init__(self):
        self.db = get_database()
    
    def calculate_time_budget(
        self,
        sleep_hours: float = 8.0,
        has_work: bool = False,
        work_hours_per_week: float = 0.0,
        work_days_per_week: int = 0
    ) -> Dict[str, float]:
        """
        Calculate user's available time budget
        
        Args:
            sleep_hours: Hours of sleep per day (default: 8)
            has_work: Whether user has a job
            work_hours_per_week: Total work hours per week
            work_days_per_week: How many days they work
            
        Returns:
            Dictionary with time budget breakdown
        """
        
        # Base calculation
        total_hours_per_day = 24.0
        waking_hours_per_day = total_hours_per_day - sleep_hours
        
        # Calculate work hours per day (average)
        if has_work and work_hours_per_week > 0:
            work_hours_per_day = work_hours_per_week / 7  # Spread across week
        else:
            work_hours_per_day = 0.0
        
        # Calculate free hours (available for tasks)
        free_hours_per_day = waking_hours_per_day - work_hours_per_day
        
        # Weekly calculations
        waking_hours_per_week = waking_hours_per_day * 7
        work_hours_per_week_actual = work_hours_per_week if has_work else 0.0
        free_hours_per_week = free_hours_per_day * 7
        
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
            
            # Additional info
            "has_work": has_work,
            "work_days_per_week": work_days_per_week if has_work else 0,
        }
    
    def save_user_profile(
        self,
        user_id: int,
        sleep_hours: float,
        has_work: bool,
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
            work_days_per_week=work_days_per_week
        )
        
        # Recommend study goal if not provided (30-40% of free time)
        if study_goal_hours_per_day is None:
            study_goal_hours_per_day = budget["free_hours_per_day"] * 0.35
        
        # Save settings
        timestamp = datetime.now().isoformat()
        
        settings_to_save = [
            ("sleep_hours", str(sleep_hours)),
            ("has_work", str(has_work)),
            ("work_hours_per_week", str(work_hours_per_week)),
            ("work_days_per_week", str(work_days_per_week)),
            ("study_goal_hours_per_day", str(study_goal_hours_per_day)),
            ("waking_hours_per_day", str(budget["waking_hours_per_day"])),
            ("free_hours_per_day", str(budget["free_hours_per_day"])),
            ("free_hours_per_week", str(budget["free_hours_per_week"])),
            ("onboarding_completed", "true"),
            ("onboarding_date", timestamp),
        ]
        
        for key, value in settings_to_save:
            self.db.cursor.execute("""
                INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, key, value, timestamp))
        
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
        
        # Fetch all settings
        settings_query = """
            SELECT setting_key, setting_value 
            FROM settings 
            WHERE user_id = ?
        """
        settings = self.db.fetch_all(settings_query, (user_id,))
        
        # Convert to dictionary
        budget_dict = {s['setting_key']: s['setting_value'] for s in settings}
        
        # Convert strings to appropriate types
        return {
            "sleep_hours": float(budget_dict.get("sleep_hours", 8)),
            "has_work": budget_dict.get("has_work", "False") == "True",
            "work_hours_per_week": float(budget_dict.get("work_hours_per_week", 0)),
            "work_days_per_week": int(budget_dict.get("work_days_per_week", 0)),
            "study_goal_hours_per_day": float(budget_dict.get("study_goal_hours_per_day", 4)),
            "waking_hours_per_day": float(budget_dict.get("waking_hours_per_day", 16)),
            "free_hours_per_day": float(budget_dict.get("free_hours_per_day", 16)),
            "free_hours_per_week": float(budget_dict.get("free_hours_per_week", 112)),
            "onboarding_date": budget_dict.get("onboarding_date"),
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
    
    def get_remaining_budget(self, user_id: int) -> Dict[str, float]:
        """
        Calculate remaining time budget for today
        Like checking your bank account balance!
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with remaining hours
        """
        
        budget = self.get_user_budget(user_id)
        if not budget:
            return {"error": "Budget not set up"}
        
        spent = self.get_time_spent_today(user_id)
        
        # Calculate remaining free time
        remaining_free_hours = budget["free_hours_per_day"] - spent["total"]
        
        # Calculate remaining study time (based on goal)
        remaining_study_hours = budget["study_goal_hours_per_day"] - spent.get("Study", 0)
        
        return {
            "free_hours_remaining": max(0, remaining_free_hours),
            "study_hours_remaining": max(0, remaining_study_hours),
            "study_hours_spent": spent.get("Study", 0),
            "work_hours_spent": spent.get("Work", 0),
            "total_hours_spent": spent["total"],
            "study_goal": budget["study_goal_hours_per_day"],
            "free_hours_budget": budget["free_hours_per_day"],
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


# Example usage scenarios
def example_working_student():
    """Example: Working student with part-time job"""
    manager = OnboardingManager()
    
    # Student works 20 hours/week at a coffee shop (4 days)
    budget = manager.calculate_time_budget(
        sleep_hours=7,
        has_work=True,
        work_hours_per_week=20,
        work_days_per_week=4
    )
    
    print("Working Student Budget:")
    print(f"  Free time per day: {budget['free_hours_per_day']:.1f} hours")
    print(f"  Free time per week: {budget['free_hours_per_week']:.1f} hours")
    print(f"  Work hours per day (avg): {budget['work_hours_per_day']:.1f} hours")
    
    return budget


def example_regular_student():
    """Example: Regular student, no job"""
    manager = OnboardingManager()
    
    budget = manager.calculate_time_budget(
        sleep_hours=8,
        has_work=False
    )
    
    print("\nRegular Student Budget:")
    print(f"  Free time per day: {budget['free_hours_per_day']:.1f} hours")
    print(f"  Free time per week: {budget['free_hours_per_week']:.1f} hours")
    
    return budget


if __name__ == "__main__":
    example_working_student()
    example_regular_student()