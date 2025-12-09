import flet as ft
from datetime import datetime, timedelta
import time
import threading

from components.task_card import TaskCard
from state.onboarding_manager import OnboardingManager

def DashboardPage(page: ft.Page, session: dict = None):
    """
    TYMATE Dashboard Page - Minimalist line-based design
    Shows current time, upcoming tasks, analytics preview, and time budget
    UPDATED: Now uses real-time budget calculations with wake/bedtime awareness
    
    Args:
        page: Flet page
        session: Session data (contains user_id and onboarding data)
    """
    
    # Initialize onboarding manager
    onboarding_mgr = OnboardingManager()
    
    user_id = session.get("user_id") if session else None

    # Get user's budget (from DB if user_id available, else fallback)
    budget = onboarding_mgr.get_user_budget(user_id) if user_id else None
    if not budget:
        # Default values if no data
        budget = {
            "free_hours_per_day": 16.0,
            "study_goal_hours_per_day": 5.6,
            "work_hours_per_day": 0.0,
            "wake_time": "07:00",
            "bedtime": "23:00",
            "sleep_hours": 8.0,
        }
    user_data = {
        "has_work": budget.get("has_work", False),
        "sleep_hours": budget.get("sleep_hours", 8.0),
    }
    
    # Calculate remaining budget for today using REAL-TIME logic
    time_spent_today = onboarding_mgr.get_time_spent_today(user_id) if user_id else {
        "Study": 0.0,
        "Work": 0.0,
        "Personal": 0.0,
        "total": 0.0,
    }
    
    study_goal = budget.get("study_goal_hours_per_day", 5.6)
    free_hours = budget.get("free_hours_per_day", 16.0)

    # Calculate realistic remaining time
    current_time = datetime.now()
    remaining = onboarding_mgr.get_remaining_budget(user_id, current_time) if user_id else None
    if not remaining or "error" in remaining:
        wake_obj = onboarding_mgr.parse_wake_time(budget.get("wake_time", "07:00"))
        sleep_hours = budget.get("sleep_hours", 8.0)
        today = current_time.date()
        wake_dt = datetime.combine(today, wake_obj)
        is_before_wake = current_time < wake_dt

        if is_before_wake:
            hours_until_wake = (wake_dt - current_time).total_seconds() / 3600
            hours_until_bedtime = budget.get("waking_hours_per_day", 24 - sleep_hours)
        else:
            hours_until_wake = 0.0
            hours_until_bedtime = onboarding_mgr.get_hours_until_bedtime(current_time, wake_obj, sleep_hours)

        study_remaining = min(max(0, study_goal - time_spent_today.get("Study", 0)), max(0, hours_until_bedtime))
        free_remaining = min(max(0, free_hours - time_spent_today.get("total", 0)), max(0, hours_until_bedtime))
        study_remaining_absolute = max(0, study_goal - time_spent_today.get("Study", 0))
    else:
        hours_until_bedtime = remaining["hours_until_bedtime"]
        hours_until_wake = remaining.get("hours_until_wake", 0)
        study_remaining = remaining["study_hours_remaining"]
        free_remaining = remaining["free_hours_remaining"]
        study_remaining_absolute = remaining["study_hours_remaining_absolute"]
        time_spent_today["total"] = remaining["total_hours_spent"]
        time_spent_today["Study"] = remaining.get("study_hours_spent", time_spent_today.get("Study", 0))
    
    # Calculate progress values (0.0 to 1.0)
    study_progress = min(1.0, time_spent_today["Study"] / study_goal) if study_goal > 0 else 0
    work_progress = 0.0
    
    # Get current date and time
    now = datetime.now()
    
    # Create time display with real-time updates
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=48, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    date_text = ft.Text(now.strftime("%A, %B %d. %Y"), size=16, color=ft.Colors.GREY_600)
    
    # Status messages
    color_map = {
        "red": ft.Colors.RED_700,
        "orange": ft.Colors.ORANGE_700,
        "yellow": ft.Colors.AMBER_700,
        "green": ft.Colors.GREEN_700,
        "blue": ft.Colors.BLUE_700,
    }

    if user_id and remaining and "time_status" in remaining:
        time_status_msg = remaining["time_status"]
        time_status_color = color_map.get(remaining.get("time_status_color", "green"), ft.Colors.GREEN_700)
    else:
        if hours_until_wake > 0:
            time_status_msg = f"Day hasn't started yet. Wake in {hours_until_wake:.1f}h"
            time_status_color = color_map["blue"]
        elif hours_until_bedtime <= 0:
            time_status_msg = "Past bedtime! Time to sleep."
            time_status_color = color_map["red"]
        elif hours_until_bedtime < 2:
            time_status_msg = f"Only {hours_until_bedtime:.1f} hours until bedtime"
            time_status_color = color_map["orange"]
        elif hours_until_bedtime < 4:
            time_status_msg = f"{hours_until_bedtime:.1f} hours remaining today"
            time_status_color = color_map["yellow"]
        else:
            time_status_msg = f"{hours_until_bedtime:.1f} hours remaining today"
            time_status_color = color_map["green"]
    
    time_status_text = ft.Text(
        time_status_msg,
        size=14,
        color=time_status_color,
        weight=ft.FontWeight.W_600,
    )
    
    time_status_container = ft.Container(
        content=time_status_text,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=6,
        bgcolor=ft.Colors.GREY_200,
        alignment=ft.alignment.center,
    )
    
    # Function to update time every second
    def update_time():
        while True:
            now = datetime.now()
            time_text.value = now.strftime("%I:%M:%S %p")
            date_text.value = now.strftime("%A, %B %d. %Y")

            if user_id:
                live_remaining = onboarding_mgr.get_remaining_budget(user_id, now)
            else:
                live_remaining = None

            if live_remaining and "time_status" in live_remaining:
                time_status_text.value = live_remaining["time_status"]
                time_status_text.color = color_map.get(live_remaining.get("time_status_color", "green"), ft.Colors.GREEN_700)
            else:
                wake_obj = onboarding_mgr.parse_wake_time(budget.get("wake_time", "07:00"))
                sleep_hours = budget.get("sleep_hours", 8.0)
                today = now.date()
                wake_dt = datetime.combine(today, wake_obj)
                is_before_wake = now < wake_dt

                if is_before_wake:
                    hours_until_wake = (wake_dt - now).total_seconds() / 3600
                    time_status_text.value = f"Day hasn't started yet. Wake in {hours_until_wake:.1f}h"
                    time_status_text.color = ft.Colors.BLUE_700
                else:
                    fallback_hours_until_bed = onboarding_mgr.get_hours_until_bedtime(now, wake_obj, sleep_hours)
                    if fallback_hours_until_bed <= 0:
                        time_status_text.value = "Past bedtime! Time to sleep."
                        time_status_text.color = ft.Colors.RED_700
                    elif fallback_hours_until_bed < 2:
                        time_status_text.value = f"Only {fallback_hours_until_bed:.1f} hours until bedtime"
                        time_status_text.color = ft.Colors.ORANGE_700
                    elif fallback_hours_until_bed < 4:
                        time_status_text.value = f"{fallback_hours_until_bed:.1f} hours remaining today"
                        time_status_text.color = ft.Colors.AMBER_700
                    else:
                        time_status_text.value = f"{fallback_hours_until_bed:.1f} hours remaining today"
                        time_status_text.color = ft.Colors.GREEN_700

            page.update()
            time.sleep(1)
    
    # Start time update thread
    thread = threading.Thread(target=update_time, daemon=True)
    thread.start()
    
    # Get upcoming tasks from database
    from state.task_manager import TaskManager
    task_manager = TaskManager()
    upcoming_tasks = task_manager.get_upcoming_tasks(user_id) if user_id else []
    
    # Create time display section
    time_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Current Time", size=20, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                time_text,
                date_text,
                ft.Container(height=20),
                time_status_container,
            ],
            spacing=0,
        ),
        padding=20,
    )
    
    # Helper function to check if mobile
    def is_mobile():
        return page.window.width < 768
    
    # Create task items - custom inline display
    task_items = []
    for task in upcoming_tasks:
        # date_due is stored as string (YYYY-MM-DD), convert for display
        if task.date_due:
            try:
                due_date = datetime.strptime(task.date_due, "%Y-%m-%d")
                due_str = due_date.strftime("%b %d, %Y")
            except:
                due_str = task.date_due
        else:
            due_str = "No due date"
            
        task_items.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(task.title, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900),
                        ft.Text(f"Due: {due_str}", size=12, color=ft.Colors.GREY_600),
                    ],
                    spacing=2,
                ),
                width=600,
                padding=12,
                border_radius=6,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                margin=ft.margin.only(bottom=8),
            )
        )

    upcoming_tasks_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Upcoming Tasks", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ft.Container(
                    height=2,
                    bgcolor=ft.Colors.GREY_400,
                    margin=ft.margin.only(top=12, bottom=16),
                ),
                ft.Column(
                    controls=task_items,
                    scroll=ft.ScrollMode.AUTO,
                    height=280,
                    spacing=0,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        expand=True,
    )
    
    # Get real analytics data for chart
    from services.analytics_engine import AnalyticsEngine
    analytics_engine = AnalyticsEngine()
    chart_data = analytics_engine.get_dashboard_chart_data(user_id, days=7)["daily_data"] if user_id else []
    
    # Create bar chart with real data
    days = []
    bars = []
    max_value = max([d["tasks"] for d in chart_data]) if chart_data else 1
    
    for day_data in chart_data:
        days.append(day_data["date"])
        height = (day_data["tasks"] / max_value * 120) if max_value > 0 else 0
        bars.append(
            ft.Container(
                width=50,
                height=max(height, 2),
                bgcolor=ft.Colors.GREY_600,
                border_radius=2,
                tooltip=f"{day_data['tasks']} tasks, {day_data['hours']}h",
            )
        )
    
    # Handle navigation to analytics page
    def go_to_analytics(e):
        page.route = "/analytics"
        page.update()
    
    analytics_preview = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Overview of the Past Week", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_FULL_OUTLINED,
                            icon_size=20,
                            icon_color=ft.Colors.GREY_700,
                            tooltip="View full analytics",
                            on_click=go_to_analytics,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    height=2,
                    bgcolor=ft.Colors.GREY_400,
                    margin=ft.margin.only(top=12, bottom=16),
                ),
                ft.Container(
                    content=ft.Row(
                        controls=bars if bars else [ft.Text("Complete tasks to see analytics", size=12, color=ft.Colors.GREY_600)],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    height=280,
                    padding=10,
                ),
                ft.Row(
                    controls=[ft.Text(day, size=11, color=ft.Colors.GREY_600) for day in days] if days else [],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
    )
    
    time_budget_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Time Budget Information", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ft.Container(
                    height=2,
                    bgcolor=ft.Colors.GREY_400,
                    margin=ft.margin.only(top=12, bottom=16),
                ),
                
                # Budget overview
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Free Time", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f"{free_remaining:.1f} / {free_hours:.1f} hrs left",
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.GREY_900,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=4),
                        ft.Row(
                            controls=[
                                ft.Text("Wake Time", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    budget.get("wake_time", "07:00"),
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.GREY_900,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=4),
                        ft.Row(
                            controls=[
                                ft.Text("Bedtime", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    budget.get("bedtime", "23:00"),
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.GREY_900,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=4),
                        ft.Row(
                            controls=[
                                ft.Text("Sleep", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f"{user_data.get('sleep_hours', 8)} hrs/day",
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.GREY_900,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=0,
                ),
                
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        expand=True,
    )
    
    # Summary Cards - Get real data from database
    total_tasks_count = len(upcoming_tasks)
    completed_today_count = task_manager.get_tasks_completed_today(user_id) if user_id else 0
    hours_this_week = onboarding_mgr.get_time_spent_this_week(user_id) if user_id else 0.0
    completion_rate = task_manager.get_completion_rate(user_id) if user_id else 0.0
    
    summary_cards = ft.Row(
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Total Tasks", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                        ft.Container(height=6),
                        ft.Text(str(total_tasks_count), size=32, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=8,
                padding=16,
                width=200,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.GREY_100,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Completed Today", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                        ft.Container(height=6),
                        ft.Text(str(completed_today_count), size=32, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=8,
                padding=16,
                width=200,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.GREY_100,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Hours This Week", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                        ft.Container(height=6),
                        ft.Text(f"{hours_this_week:.1f}", size=32, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=8,
                padding=16,
                width=200,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.GREY_100,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Completion Rate", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                        ft.Container(height=6),
                        ft.Text(f"{completion_rate:.0f}%", size=32, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                border=ft.border.all(2, ft.Colors.GREY_300),
                border_radius=8,
                padding=16,
                width=200,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.GREY_100,
            ),
        ],
        spacing=16,
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
    # Build responsive layout based on screen size
    def build_layout():
        if is_mobile():
            # Mobile layout: stack everything vertically
            return ft.Column(
                controls=[
                    time_section,
                    ft.Container(height=2),
                    time_budget_section,
                    ft.Container(height=24),
                    analytics_preview,
                    ft.Container(height=24),
                    upcoming_tasks_section,
                    ft.Container(height=24),
                    summary_cards,
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        else:
            # Desktop layout: two-column design
            return ft.Column(
                controls=[
                    # Top section with left and right columns
                    ft.Row(
                        controls=[
                            # Left column
                            ft.Column(
                                controls=[
                                    time_section,
                                    upcoming_tasks_section,
                                ],
                                expand=1,
                            ),
                            
                            ft.Container(width=24),
                            
                            # Right column
                            ft.Column(
                                controls=[
                                    analytics_preview,
                                    time_budget_section,
                                ],
                                expand=1,
                            ),
                        ],
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),

                    # Bottom section with summary cards
                    ft.Container(height=12),
                    ft.Container(
                        content=summary_cards,
                        alignment=ft.alignment.center,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            )
    
    dashboard_container = ft.Container(
        content=build_layout(),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.GREY_50,
    )
    
    # Add window resize listener
    def on_window_resize(e=None):
        dashboard_container.content = build_layout()
        page.update()
    
    page.on_resized = on_window_resize
    
    return dashboard_container