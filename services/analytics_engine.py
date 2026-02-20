"""
Emerging Tech Feature: Predictive Analytics & Smart Recommendations
FIXED VERSION with proper error handling and date parsing
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from storage.sqlite import get_database
from collections import defaultdict
import statistics


class AnalyticsEngine:
    """
    Advanced analytics engine for task and time management insights
    """
    
    def __init__(self):
        self.db = get_database()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Safely parse date string with multiple format attempts"""
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        
        # Last resort: try to extract just the date part
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except:
            return None
    
    # ==================== Core Analytics ====================
    
    def get_task_completion_metrics(self, user_id: int, days: int = 30) -> Dict:
        """
        Analyze task completion patterns with robust error handling
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Get completed tasks
            completed = self.db.fetch_all("""
                SELECT 
                    t.id,
                    t.date_given,
                    t.date_due,
                    t.completed_at,
                    t.category,
                    t.estimated_time,
                    SUM(ts.duration_minutes) as actual_minutes,
                    t.status
                FROM tasks t
                LEFT JOIN task_sessions ts
                    ON ts.task_id = t.id AND ts.is_deleted = 0
                WHERE t.user_id = ? 
                AND t.status = 'Completed'
                AND t.completed_at IS NOT NULL
                AND t.date_given >= ?
                AND t.is_deleted = 0
                GROUP BY t.id
            """, (user_id, cutoff_date))
            
            if not completed:
                return self._empty_metrics()
            
            # Calculate metrics
            completion_times = []
            on_time_count = 0
            late_count = 0
            category_stats = defaultdict(lambda: {"completed": 0, "total": 0})
            time_accuracy = []
            
            for task in completed:
                try:
                    # Parse dates safely
                    date_given = self._parse_date(task["date_given"])
                    completed_at = self._parse_date(task["completed_at"])
                    date_due = self._parse_date(task["date_due"])
                    
                    if not all([date_given, completed_at, date_due]):
                        continue
                    
                    # Days from given to completion
                    days_taken = (completed_at - date_given).days
                    if days_taken >= 0:  # Only positive values
                        completion_times.append(days_taken)
                    
                    # On-time vs late
                    if completed_at.date() <= date_due.date():
                        on_time_count += 1
                    else:
                        late_count += 1
                    
                    # Category stats
                    category = task["category"] or "Uncategorized"
                    category_stats[category]["completed"] += 1
                    
                    # Time estimation accuracy
                    if task["estimated_time"] and task["actual_minutes"]:
                        est = int(task["estimated_time"])
                        act = int(task["actual_minutes"])
                        if est > 0:
                            accuracy = (act / est) * 100
                            if 10 <= accuracy <= 500:  # Reasonable bounds
                                time_accuracy.append(accuracy)
                
                except Exception as e:
                    print(f"Error processing task: {e}")
                    continue
            
            # Get total tasks by category for completion rate
            all_tasks = self.db.fetch_all("""
                SELECT category, COUNT(*) as count
                FROM tasks
                WHERE user_id = ? AND date_given >= ? AND is_deleted = 0
                GROUP BY category
            """, (user_id, cutoff_date))
            
            for task in all_tasks:
                category = task["category"] or "Uncategorized"
                category_stats[category]["total"] = task["count"]
            
            # Calculate averages with fallbacks
            total_counted = on_time_count + late_count
            if total_counted == 0:
                return self._empty_metrics()
            
            avg_completion_days = statistics.mean(completion_times) if completion_times else 0
            median_completion_days = statistics.median(completion_times) if completion_times else 0
            
            # Task velocity (tasks per week)
            weeks = days / 7
            task_velocity = len(completed) / weeks if weeks > 0 else 0
            
            # Time estimation accuracy
            avg_time_accuracy = statistics.mean(time_accuracy) if time_accuracy else 100
            
            return {
                "avg_completion_days": round(avg_completion_days, 1),
                "median_completion_days": round(median_completion_days, 1),
                "on_time_percentage": round((on_time_count / total_counted) * 100, 1),
                "late_percentage": round((late_count / total_counted) * 100, 1),
                "task_velocity": round(task_velocity, 1),
                "total_completed": len(completed),
                "category_completion_rates": {
                    cat: round((stats["completed"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
                    for cat, stats in category_stats.items()
                },
                "time_estimation_accuracy": round(avg_time_accuracy, 1),
                "time_accuracy_status": self._get_accuracy_status(avg_time_accuracy),
            }
        
        except Exception as e:
            print(f"Error in get_task_completion_metrics: {e}")
            return self._empty_metrics()
    
    def get_procrastination_score(self, user_id: int) -> Dict:
        """
        Calculate procrastination patterns with error handling
        """
        try:
            # Get tasks from last 60 days
            tasks = self.db.fetch_all("""
                SELECT 
                    date_given,
                    date_due,
                    completed_at,
                    status
                FROM tasks
                WHERE user_id = ? 
                AND is_deleted = 0
                AND date_given >= date('now', '-60 days')
            """, (user_id,))
            
            if not tasks or len(tasks) == 0:
                return {
                    "score": 0,
                    "level": "No data",
                    "color": "green",
                    "last_minute_percentage": 0,
                    "overdue_percentage": 0,
                    "insights": ["Complete more tasks to get insights"]
                }
            
            last_minute_completions = 0
            overdue_tasks = 0
            total_analyzed = 0
            
            for task in tasks:
                try:
                    date_given = self._parse_date(task["date_given"])
                    date_due = self._parse_date(task["date_due"])
                    
                    if not all([date_given, date_due]):
                        continue
                    
                    total_days = (date_due - date_given).days
                    
                    if task["completed_at"]:
                        completed_at = self._parse_date(task["completed_at"])
                        if not completed_at:
                            continue
                        
                        days_before_due = (date_due - completed_at).days
                        
                        # Last minute completion (within 20% of time window or last day)
                        if total_days > 0 and (days_before_due <= max(1, total_days * 0.2)):
                            last_minute_completions += 1
                        
                        # Late completion
                        if completed_at.date() > date_due.date():
                            overdue_tasks += 1
                        
                        total_analyzed += 1
                    
                    elif task["status"] != "Completed":
                        # Check if currently overdue
                        if datetime.now().date() > date_due.date():
                            overdue_tasks += 1
                            total_analyzed += 1
                
                except Exception as e:
                    print(f"Error processing task for procrastination: {e}")
                    continue
            
            if total_analyzed == 0:
                return {
                    "score": 0,
                    "level": "No data",
                    "color": "green",
                    "last_minute_percentage": 0,
                    "overdue_percentage": 0,
                    "insights": ["Complete more tasks to get insights"]
                }
            
            # Calculate procrastination score (0-100)
            last_minute_ratio = last_minute_completions / total_analyzed
            overdue_ratio = overdue_tasks / total_analyzed
            
            score = int((last_minute_ratio * 50 + overdue_ratio * 50) * 100)
            
            # Determine level
            if score < 20:
                level = "Excellent"
                color = "green"
            elif score < 40:
                level = "Good"
                color = "green"
            elif score < 60:
                level = "Moderate"
                color = "yellow"
            elif score < 80:
                level = "High"
                color = "orange"
            else:
                level = "Very High"
                color = "red"
            
            insights = []
            if last_minute_completions > total_analyzed * 0.3:
                insights.append(f"You complete {int(last_minute_ratio*100)}% of tasks at the last minute")
            if overdue_tasks > total_analyzed * 0.2:
                insights.append(f"{int(overdue_ratio*100)}% of tasks are completed late or overdue")
            if score < 40:
                insights.append("Great work! You're staying on top of your tasks")
            
            return {
                "score": score,
                "level": level,
                "color": color,
                "last_minute_percentage": round(last_minute_ratio * 100, 1),
                "overdue_percentage": round(overdue_ratio * 100, 1),
                "insights": insights if insights else ["Keep up the good work!"],
            }
        
        except Exception as e:
            print(f"Error in get_procrastination_score: {e}")
            return {
                "score": 0,
                "level": "Error",
                "color": "green",
                "last_minute_percentage": 0,
                "overdue_percentage": 0,
                "insights": ["Unable to calculate"]
            }
    
    def get_productivity_trends(self, user_id: int, weeks: int = 12) -> Dict:
        """
        Analyze productivity trends with fixed date handling
        """
        try:
            cutoff_date = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
            
            # Get completed tasks grouped by week
            completed = self.db.fetch_all("""
                SELECT 
                    date(t.completed_at) as completion_date,
                    SUM(ts.duration_minutes) as actual_minutes
                FROM tasks t
                LEFT JOIN task_sessions ts
                    ON ts.task_id = t.id AND ts.is_deleted = 0
                WHERE t.user_id = ?
                AND t.status = 'Completed'
                AND t.completed_at IS NOT NULL
                AND t.completed_at >= ?
                AND t.is_deleted = 0
                GROUP BY t.id
                ORDER BY t.completed_at
            """, (user_id, cutoff_date))
            
            # Group by week manually
            weekly_stats = defaultdict(lambda: {"tasks": 0, "minutes": 0})
            
            for task in completed:
                try:
                    comp_date = self._parse_date(task["completion_date"])
                    if not comp_date:
                        continue
                    
                    # Get ISO week
                    year, week, _ = comp_date.isocalendar()
                    week_key = f"{year}-W{week:02d}"
                    
                    weekly_stats[week_key]["tasks"] += 1
                    if task["actual_minutes"]:
                        weekly_stats[week_key]["minutes"] += int(task["actual_minutes"])
                
                except Exception as e:
                    print(f"Error processing weekly task: {e}")
                    continue
            
            # Convert to list
            weekly_data = [
                {
                    "week": week,
                    "tasks_completed": stats["tasks"],
                    "minutes_logged": int(stats["minutes"]),
                }
                for week, stats in sorted(weekly_stats.items())
            ]
            
            # Calculate trend
            if len(weekly_data) >= 2:
                recent_count = min(4, len(weekly_data))
                older_count = min(4, len(weekly_data))
                
                recent_avg = statistics.mean([w["tasks_completed"] for w in weekly_data[-recent_count:]])
                older_avg = statistics.mean([w["tasks_completed"] for w in weekly_data[:older_count]])
                
                if recent_avg > older_avg * 1.1:
                    trend = "improving"
                elif recent_avg < older_avg * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            # Predict next week
            if len(weekly_data) >= 3:
                predicted_tasks = statistics.mean([w["tasks_completed"] for w in weekly_data[-3:]])
            else:
                predicted_tasks = 0
            
            current_avg = statistics.mean([w["tasks_completed"] for w in weekly_data[-4:]]) if len(weekly_data) >= 4 else 0
            
            return {
                "weekly_data": weekly_data,
                "trend": trend,
                "predicted_next_week": round(predicted_tasks, 0),
                "current_week_average": round(current_avg, 1),
            }
        
        except Exception as e:
            print(f"Error in get_productivity_trends: {e}")
            return {
                "weekly_data": [],
                "trend": "error",
                "predicted_next_week": 0,
                "current_week_average": 0,
            }
    
    def get_category_insights(self, user_id: int) -> List[Dict]:
        """
        Analyze performance by task category with error handling
        """
        try:
            data = self.db.fetch_all("""
                SELECT 
                    t.category,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed,
                    AVG(ts_totals.total_minutes) as avg_actual_minutes,
                    AVG(CASE WHEN t.estimated_time IS NOT NULL THEN t.estimated_time ELSE NULL END) as avg_estimated_minutes,
                    COUNT(CASE WHEN t.status = 'Completed' AND t.completed_at > t.date_due THEN 1 ELSE NULL END) as late_count
                FROM tasks t
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_minutes
                    FROM task_sessions
                    WHERE is_deleted = 0
                    GROUP BY task_id
                ) ts_totals ON ts_totals.task_id = t.id
                WHERE t.user_id = ?
                AND t.is_deleted = 0
                AND t.date_given >= date('now', '-60 days')
                GROUP BY t.category
                HAVING total_tasks > 0
                ORDER BY total_tasks DESC
            """, (user_id,))
            
            insights = []
            for row in data:
                try:
                    total = row["total_tasks"] or 0
                    completed = row["completed"] or 0
                    late = row["late_count"] or 0
                    
                    completion_rate = (completed / total * 100) if total > 0 else 0
                    on_time_rate = ((completed - late) / completed * 100) if completed > 0 else 0
                    
                    # Time accuracy
                    time_accuracy = None
                    if row["avg_estimated_minutes"] and row["avg_actual_minutes"]:
                        est = int(row["avg_estimated_minutes"])
                        act = int(row["avg_actual_minutes"])
                        if est > 0:
                            time_accuracy = (act / est) * 100
                    
                    insights.append({
                        "category": row["category"] or "Uncategorized",
                        "total_tasks": total,
                        "completion_rate": round(completion_rate, 1),
                        "on_time_rate": round(on_time_rate, 1),
                        "avg_minutes": int(row["avg_actual_minutes"] or 0),
                        "time_accuracy": round(time_accuracy, 1) if time_accuracy else None,
                    })
                
                except Exception as e:
                    print(f"Error processing category insight: {e}")
                    continue
            
            return insights
        
        except Exception as e:
            print(f"Error in get_category_insights: {e}")
            return []
    
    def get_peak_productivity_hours(self, user_id: int) -> Dict:
        """
        Identify when user is most productive
        """
        try:
            logs = self.db.fetch_all("""
                SELECT 
                    start_time,
                    hours
                FROM time_logs
                WHERE user_id = ?
                AND start_time IS NOT NULL
                AND hours > 0
            """, (user_id,))
            
            hour_productivity = defaultdict(lambda: {"hours": 0, "count": 0})
            
            for log in logs:
                if log["start_time"]:
                    try:
                        hour = int(log["start_time"].split(":")[0])
                        if 0 <= hour <= 23:
                            hour_productivity[hour]["hours"] += float(log["hours"])
                            hour_productivity[hour]["count"] += 1
                    except:
                        continue
            
            # Find peak hours
            peak_hours = sorted(
                [(h, d["hours"] / d["count"]) for h, d in hour_productivity.items() if d["count"] > 0],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            return {
                "peak_hours": [f"{h:02d}:00" for h, _ in peak_hours] if peak_hours else [],
                "productivity_by_hour": dict(hour_productivity),
            }
        
        except Exception as e:
            print(f"Error in get_peak_productivity_hours: {e}")
            return {"peak_hours": [], "productivity_by_hour": {}}
    
    # ==================== Smart Recommendations ====================
    
    def generate_smart_tips(self, user_id: int) -> List[Dict]:
        """
        Generate personalized smart tips based on analytics
        """
        tips = []
        
        try:
            completion_metrics = self.get_task_completion_metrics(user_id)
            procrastination = self.get_procrastination_score(user_id)
            category_insights = self.get_category_insights(user_id)
            
            # Tip 1: Time estimation
            accuracy = completion_metrics["time_estimation_accuracy"]
            if accuracy < 80:
                tips.append({
                    "type": "time_estimation",
                    "priority": "high",
                    "title": "Improve Time Estimates",
                    "message": f"Your time estimates are {accuracy:.0f}% accurate. Try adding buffer time.",
                    "action": "Review past tasks to calibrate estimates",
                })
            elif accuracy > 120:
                tips.append({
                    "type": "time_estimation",
                    "priority": "medium",
                    "title": "You're Overestimating",
                    "message": f"You're estimating {accuracy:.0f}% of actual time needed.",
                    "action": "Reduce time estimates by 15%",
                })
            
            # Tip 2: Procrastination
            if procrastination["score"] > 60:
                tips.append({
                    "type": "procrastination",
                    "priority": "high",
                    "title": "Tackle Procrastination",
                    "message": f"Procrastination score: {procrastination['score']}/100",
                    "action": "Start tasks within 24 hours of receiving them",
                })
            
            # Tip 3: Category performance
            if category_insights:
                worst_category = min(category_insights, key=lambda x: x["completion_rate"])
                if worst_category["completion_rate"] < 60:
                    tips.append({
                        "type": "category_focus",
                        "priority": "medium",
                        "title": f"Improve {worst_category['category']} Tasks",
                        "message": f"{worst_category['completion_rate']:.0f}% completion rate",
                        "action": f"Break down tasks into smaller subtasks",
                    })
            
            # Tip 4: Task velocity
            velocity = completion_metrics["task_velocity"]
            if 0 < velocity < 2:
                tips.append({
                    "type": "productivity",
                    "priority": "medium",
                    "title": "Increase Task Completion",
                    "message": f"Completing {velocity:.1f} tasks/week. Aim for 3-5.",
                    "action": "Set a goal to complete 1 task every 2 days",
                })
            
            # Tip 5: On-time completion
            late_pct = completion_metrics["late_percentage"]
            if late_pct > 30:
                tips.append({
                    "type": "deadline",
                    "priority": "high",
                    "title": "Meet More Deadlines",
                    "message": f"{late_pct:.0f}% of tasks completed late",
                    "action": "Set personal deadlines 2 days before due dates",
                })
        
        except Exception as e:
            print(f"Error generating smart tips: {e}")
        
        return tips
    
    # ==================== Visualization Data ====================
    
    def get_dashboard_chart_data(self, user_id: int, days: int = 7) -> Dict:
        """
        Get data for dashboard visualization with error handling
        """
        try:
            data = []
            today = datetime.now().date()
            
            for i in range(days):
                date = today - timedelta(days=days - i - 1)
                date_str = date.strftime("%Y-%m-%d")
                
                # Count completed tasks for this day
                count = self.db.fetch_one("""
                    SELECT COUNT(*) as count
                    FROM tasks
                    WHERE user_id = ?
                    AND DATE(completed_at) = ?
                    AND status = 'Completed'
                    AND is_deleted = 0
                """, (user_id, date_str))
                
                # Get task session minutes logged on this date
                minutes = self.db.fetch_one("""
                    SELECT SUM(ts.duration_minutes) as total
                    FROM task_sessions ts
                    JOIN tasks t ON t.id = ts.task_id
                    WHERE ts.user_id = ?
                    AND DATE(ts.logged_at) = ?
                    AND ts.is_deleted = 0
                    AND t.is_deleted = 0
                """, (user_id, date_str))
                
                data.append({
                    "date": date.strftime("%a")[:3],  # Mon, Tue, etc (shortened)
                    "full_date": date_str,
                    "tasks": count["count"] if count else 0,
                    "minutes": int(minutes["total"] or 0) if minutes else 0,
                })
            
            return {"daily_data": data}
        
        except Exception as e:
            print(f"Error in get_dashboard_chart_data: {e}")
            return {"daily_data": []}
    
    def get_detailed_analytics_data(self, user_id: int) -> Dict:
        """
        Get comprehensive analytics for full analytics page
        """
        return {
            "completion_metrics": self.get_task_completion_metrics(user_id),
            "procrastination": self.get_procrastination_score(user_id),
            "productivity_trends": self.get_productivity_trends(user_id),
            "category_insights": self.get_category_insights(user_id),
            "peak_hours": self.get_peak_productivity_hours(user_id),
            "smart_tips": self.generate_smart_tips(user_id),
            "chart_data": self.get_dashboard_chart_data(user_id, days=30),
        }
    
    # ==================== Helper Methods ====================
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no data available"""
        return {
            "avg_completion_days": 0,
            "median_completion_days": 0,
            "on_time_percentage": 0,
            "late_percentage": 0,
            "task_velocity": 0,
            "total_completed": 0,
            "category_completion_rates": {},
            "time_estimation_accuracy": 100,
            "time_accuracy_status": "No data",
        }
    
    def _get_accuracy_status(self, accuracy: float) -> str:
        """Get status label for time estimation accuracy"""
        if 90 <= accuracy <= 110:
            return "Excellent"
        elif 80 <= accuracy <= 120:
            return "Good"
        elif 70 <= accuracy <= 130:
            return "Fair"
        else:
            return "Needs Improvement"