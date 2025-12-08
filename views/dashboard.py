import flet as ft
from datetime import datetime, timedelta
import time
import threading

from components.task_card import TaskCard
from state.onboarding_manager import OnboardingManager

def DashboardPage(page: ft.Page, session: dict = None):
    """
    TYMATE Dashboard Page
    Shows current time, upcoming tasks, analytics preview, and time budget
    UPDATED: Now uses real-time budget calculations with wake/bedtime awareness
    
    Args:
        page: Flet page
        session: Session data (contains user_id and onboarding data)
    """
    
    # Initialize onboarding manager
    onboarding_mgr = OnboardingManager()
    
    # Get user's budget (from session or database)
    # For now, use session data from onboarding
    if session and "time_budget" in session:
        budget = session["time_budget"]
        user_data = session.get("user_data", {})
    else:
        # Default values if no session (for testing)
        budget = {
            "free_hours_per_day": 16.0,
            "study_goal_hours_per_day": 5.6,
            "work_hours_per_day": 0.0,
            "wake_time": "07:00",
            "bedtime": "23:00",
        }
        user_data = {
            "has_work": False,
            "sleep_hours": 8.0,
        }
    
    # Calculate remaining budget for today using REAL-TIME logic
    # TODO: Get actual time logs from database
    # For now, use mock data
    time_spent_today = {
        "Study": 2.0,   # 2 hours studied so far
        "Work": 0.0,    # 0 hours worked
        "total": 2.0,
    }
    
    study_goal = budget.get("study_goal_hours_per_day", 5.6)
    free_hours = budget.get("free_hours_per_day", 16.0)
    
    # NEW: Calculate realistic remaining time (considering bedtime)
    current_time = datetime.now()
    wake_time = onboarding_mgr.parse_wake_time(budget.get("wake_time", "07:00"))
    sleep_hours = user_data.get("sleep_hours", 8.0)
    
    hours_until_bedtime = onboarding_mgr.get_hours_until_bedtime(
        current_time, wake_time, sleep_hours
    )
    hours_since_wake = onboarding_mgr.get_hours_since_wake(
        current_time, wake_time
    )
    
    # Calculate absolute remaining (ignoring time constraint)
    study_remaining_absolute = max(0, study_goal - time_spent_today["Study"])
    free_remaining_absolute = max(0, free_hours - time_spent_today["total"])
    
    # Calculate realistic remaining (constrained by bedtime)
    study_remaining = min(study_remaining_absolute, max(0, hours_until_bedtime))
    free_remaining = min(free_remaining_absolute, max(0, hours_until_bedtime))
    
    # Calculate progress values (0.0 to 1.0)
    study_progress = min(1.0, time_spent_today["Study"] / study_goal) if study_goal > 0 else 0
    work_progress = 0.0  # Will be calculated when work logging is implemented
    
    # Get current date and time
    now = datetime.now()
    
    # Create time display with real-time updates
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=36, weight=ft.FontWeight.BOLD)
    date_text = ft.Text(now.strftime("%A, %B %d, %Y"), size=14, color=ft.Colors.GREY_700)
    
    # NEW: Status messages based on time remaining
    if hours_until_bedtime <= 0:
        time_status_msg = "Past bedtime! Time to sleep. 😴"
        time_status_color = ft.Colors.RED_600
    elif hours_until_bedtime < 2:
        time_status_msg = f"Only {hours_until_bedtime:.1f} hours until bedtime! ⏰"
        time_status_color = ft.Colors.ORANGE_600
    elif hours_until_bedtime < 4:
        time_status_msg = f"{hours_until_bedtime:.1f} hours remaining today"
        time_status_color = ft.Colors.AMBER_600
    else:
        time_status_msg = f"{hours_until_bedtime:.1f} hours remaining today"
        time_status_color = ft.Colors.GREEN_600
    
    time_status_text = ft.Text(
        time_status_msg,
        size=12,
        color=time_status_color,
        weight=ft.FontWeight.BOLD,
    )
    
    # Function to update time every second
    def update_time():
        while True:
            now = datetime.now()
            time_text.value = now.strftime("%I:%M:%S %p")
            date_text.value = now.strftime("%A, %B %d, %Y")
            
            # Update time remaining status
            current_hours_until_bed = onboarding_mgr.get_hours_until_bedtime(
                now, wake_time, sleep_hours
            )
            
            if current_hours_until_bed <= 0:
                time_status_text.value = "Past bedtime! Time to sleep. 😴"
                time_status_text.color = ft.Colors.RED_600
            elif current_hours_until_bed < 2:
                time_status_text.value = f"Only {current_hours_until_bed:.1f} hours until bedtime! ⏰"
                time_status_text.color = ft.Colors.ORANGE_600
            elif current_hours_until_bed < 4:
                time_status_text.value = f"{current_hours_until_bed:.1f} hours remaining today"
                time_status_text.color = ft.Colors.AMBER_600
            else:
                time_status_text.value = f"{current_hours_until_bed:.1f} hours remaining today"
                time_status_text.color = ft.Colors.GREEN_600
            
            page.update()
            time.sleep(1)
    
    # Start time update thread
    thread = threading.Thread(target=update_time, daemon=True)
    thread.start()
    
    # Sample upcoming tasks data
    # TODO: Get from database
    upcoming_tasks = [
        {"title": "Wireframe", "due_date": "Nov. 17, 2025"},
        {"title": "App Dev - LT", "due_date": "Nov. 17, 2025"},
        {"title": "A&O - LT", "due_date": "Nov. 17, 2025"},
        {"title": "A&O - Project Checking", "due_date": "Nov. 17, 2025"},
        {"title": "InfoAssurance - Project", "due_date": "Nov. 17, 2025"},
    ]
    
    # Create time display section
    time_section = ft.Column(
        controls=[
            ft.Text("Current Time", size=14, color=ft.Colors.GREY_700),
            time_text,
            date_text,
            ft.Container(height=5),
            time_status_text,
        ],
        spacing=5,
    )
    
    # Helper function to check if mobile
    def is_mobile():
        return page.window.width < 768
    
    # Create upcoming tasks list using TaskCard
    task_items = [TaskCard(task["title"], task["due_date"]) for task in upcoming_tasks]

    upcoming_tasks_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Upcoming Tasks", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Column(
                    controls=task_items,
                    scroll=ft.ScrollMode.AUTO,
                    height=280,
                ),
            ],
        ),
        bgcolor=ft.Colors.GREY_100,
        border_radius=12,
        padding=20,
        expand=True,
    )
    
    # Create simple bar chart for analytics
    # TODO: Get real data from database
    bar_heights = [120, 40, 0, 0, 0, 0, 0]  # Monday has 3 hours, Tuesday 1 hour
    days = ["Mon", "Tues", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    bars = []
    for height in bar_heights:
        bars.append(
            ft.Container(
                width=50,
                height=height,
                bgcolor=ft.Colors.BLUE_400,
                border_radius=4,
            )
        )
    
    analytics_preview = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Analytics Preview", size=18, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_FULL,
                            icon_size=20,
                            tooltip="View full analytics",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(
                        controls=bars,
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    height=150,
                    padding=10,
                ),
                ft.Row(
                    controls=[ft.Text(day, size=12) for day in days],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ],
        ),
        bgcolor=ft.Colors.GREY_100,
        border_radius=12,
        padding=20,
    )
    
    # ==================== UPDATED: Real Time Budget Display ====================
    
    # Progress bar text showing "X / Y hours"
    study_progress_text = ft.Text(
        f"{time_spent_today['Study']:.1f} / {study_goal:.1f} hours",
        size=12,
        color=ft.Colors.BLUE_700,
        weight=ft.FontWeight.BOLD,
    )
    
    work_progress_text = ft.Text(
        f"{time_spent_today['Work']:.1f} / {budget.get('work_hours_per_day', 0):.1f} hours",
        size=12,
        color=ft.Colors.ORANGE_700,
        weight=ft.FontWeight.BOLD,
    )
    
    # Remaining hours message - NOW WITH REALISTIC TIME CONSIDERATION
    if study_remaining <= 0:
        if time_spent_today["Study"] >= study_goal:
            remaining_message = "Study goal completed! Great job! 🎉"
            message_color = ft.Colors.GREEN_600
            message_bg = ft.Colors.GREEN_50
        else:
            remaining_message = "No time left today to reach your study goal"
            message_color = ft.Colors.RED_600
            message_bg = ft.Colors.RED_50
    elif study_remaining < study_remaining_absolute:
        remaining_message = f"{study_remaining:.1f} hours remaining (limited by bedtime at {budget.get('bedtime', '23:00')})"
        message_color = ft.Colors.ORANGE_600
        message_bg = ft.Colors.ORANGE_50
    else:
        remaining_message = f"{study_remaining:.1f} hours remaining to meet your study goal."
        message_color = ft.Colors.BLUE_600
        message_bg = ft.Colors.BLUE_50
    
    time_budget_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Today's Time Budget", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                # Budget overview card with wake/bedtime info
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("⏰ Free Time:", size=12),
                                    ft.Text(
                                        f"{free_remaining:.1f} / {free_hours:.1f} hrs left",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREEN_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("🌅 Wake Time:", size=12),
                                    ft.Text(
                                        budget.get("wake_time", "07:00"),
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("🌙 Bedtime:", size=12),
                                    ft.Text(
                                        budget.get("bedtime", "23:00"),
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("😴 Sleep:", size=12),
                                    ft.Text(
                                        f"{user_data.get('sleep_hours', 8)} hrs/day",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=8,
                    padding=10,
                ),
                
                ft.Container(height=15),
                
                # Study time progress
                ft.Row(
                    controls=[
                        ft.Text("Study Time", size=12, color=ft.Colors.GREY_700),
                        study_progress_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ProgressBar(
                    value=study_progress,
                    color=ft.Colors.BLUE_400,
                    bgcolor=ft.Colors.BLUE_100,
                    height=10,
                    expand=True,
                ),
                
                ft.Container(height=15),
                
                # Work time progress (if applicable)
                ft.Row(
                    controls=[
                        ft.Text("Work Time", size=12, color=ft.Colors.GREY_700),
                        work_progress_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ProgressBar(
                    value=work_progress,
                    color=ft.Colors.ORANGE_400,
                    bgcolor=ft.Colors.ORANGE_100,
                    height=10,
                    expand=True,
                ),
                
                ft.Container(height=15),
                
                # Remaining hours message with realistic calculation
                ft.Container(
                    content=ft.Text(
                        remaining_message,
                        size=12,
                        color=message_color,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=message_bg,
                    border_radius=8,
                    padding=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        bgcolor=ft.Colors.GREY_100,
        border_radius=12,
        padding=20,
        expand=True,
    )
    
    # ==================== Summary Cards with Real Data ====================
    
    # TODO: Get from database
    total_tasks_count = len(upcoming_tasks)
    completed_today_count = 0
    hours_this_week = time_spent_today["total"] * 3  # Mock: assume 3 days logged
    completion_rate = 0.0  # Will calculate when tasks are in DB
    
    summary_cards = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Total Tasks", size=12, color=ft.Colors.GREY_600),
                                ft.Text(str(total_tasks_count), size=24, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=80,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Completed Today", size=12, color=ft.Colors.GREY_600),
                                ft.Text(str(completed_today_count), size=24, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=80,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Hours This Week", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"{hours_this_week:.1f}", size=24, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=80,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Completion Rate", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"{completion_rate:.0f}%", size=24, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=80,
                        alignment=ft.alignment.center,
                    ),
                ],
                spacing=10,
            ),
        ],
    )
    
    # Build responsive layout based on screen size
    def build_layout():
        if is_mobile():
            # Mobile layout: stack everything vertically
            return ft.Column(
                controls=[
                    time_section,
                    ft.Container(height=20),
                    time_budget_section,
                    ft.Container(height=20),
                    analytics_preview,
                    ft.Container(height=20),
                    upcoming_tasks_section,
                    ft.Container(height=20),
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
                                    ft.Container(height=20),
                                    upcoming_tasks_section,
                                ],
                                expand=1,
                            ),
                            
                            ft.Container(width=20),
                            
                            # Right column
                            ft.Column(
                                controls=[
                                    analytics_preview,
                                    ft.Container(height=20),
                                    time_budget_section,
                                ],
                                expand=1,
                            ),
                        ],
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    
                    # Bottom section with summary cards
                    ft.Container(height=20),
                    summary_cards,
                ],
                scroll=ft.ScrollMode.AUTO,
            )
    
    dashboard_container = ft.Container(
        content=build_layout(),
        padding=20,
        expand=True,
    )
    
    # Add window resize listener to rebuild layout
    def on_window_resize(e=None):
        dashboard_container.content = build_layout()
        page.update()
    
    page.on_resized = on_window_resize
    
    return dashboard_container