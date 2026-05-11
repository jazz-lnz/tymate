import flet as ft
from datetime import datetime, timedelta, date
import time
import threading
import os

try:
    from flet.core.page import PageDisconnectedException
except Exception:
    PageDisconnectedException = None

from state.onboarding_manager import OnboardingManager
from utils.time_helpers import format_minutes
from managers.schedule_manager import ScheduleManager

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

    # Palette (matches app-wide theme)
    page_bg = "#DDE9FB"
    panel_bg = "#FFFFFF"
    soft_panel_bg = "#F6F8FB"
    border_color = "#B7C4D8"
    drop_shadow = ft.BoxShadow(
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
        offset=ft.Offset(0, 2),
    )
    title_color = "#23211E"
    accent_color = "#6E7889"

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
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=42, weight=ft.FontWeight.W_700, color=title_color)
    day_span = ft.TextSpan(
        now.strftime("%A"),
        style=ft.TextStyle(
            decoration=ft.TextDecoration.UNDERLINE,
            decoration_color=accent_color,
            color=accent_color,
            size=14,
        ),
    )
    date_span = ft.TextSpan(
        now.strftime(", %B %d, %Y"),
        style=ft.TextStyle(color=accent_color, size=14),
    )
    day_date_text = ft.Text(spans=[day_span, date_span])
    
    # Status messages
    color_map = {
        "red": ft.Colors.RED_700,
        "orange": ft.Colors.ORANGE_700,
        "yellow": ft.Colors.AMBER_700,
        "green": ft.Colors.GREEN_700,
        "blue": ft.Colors.BLUE_700,
    }

    def _build_status_msg(h_wake, h_bed):
        if hours_until_wake > 0:
            return f"Your day hasn't started yet. You can sleep in for {h_wake:.1f}h..."
        elif hours_until_bedtime <= 0:
            return "It's your bedtime, go to sleep! ಠ_ಠ"
        elif hours_until_bedtime < 2:
            return f"...only {h_bed:.1f} hours until bedtime O.O"
        elif hours_until_bedtime < 4:
            return f"{h_bed:.1f} hours remainingggg"
        else:
            return f"We still have {h_bed:.1f} hours today! Spend it well (⁠｡⁠•̀⁠ᴗ⁠-⁠)⁠✧♡"

    time_status_msg = _build_status_msg(hours_until_wake, hours_until_bedtime)
    
    time_status_text = ft.Text(
        time_status_msg,
        size=15,
        italic=True,
        color=title_color,
        weight=ft.FontWeight.W_500,
        text_align=ft.TextAlign.CENTER,
    )

    time_status_container = ft.Container(
        content=time_status_text,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        border_radius=10,
        bgcolor=panel_bg,
        border=ft.border.all(1.5, "#1A1A1A"),
        shadow=drop_shadow,
        alignment=ft.alignment.center,
    )
    
    # Function to update time every second
    def update_time():
        while True:
            try:
                now = datetime.now()
                time_text.value = now.strftime("%I:%M:%S %p")
                day_span.text = now.strftime("%A")
                date_span.text = now.strftime(", %B %d, %Y")

                if user_id:
                    live_remaining = onboarding_mgr.get_remaining_budget(user_id, now)
                else:
                    live_remaining = None

                wake_obj = onboarding_mgr.parse_wake_time(budget.get("wake_time", "07:00"))
                sleep_hours = budget.get("sleep_hours", 8.0)
                if live_remaining and "hours_until_bedtime" in live_remaining:
                    live_h_bed = live_remaining["hours_until_bedtime"]
                    live_h_wake = live_remaining.get("hours_until_wake", 0)
                else:
                    wake_dt = datetime.combine(now.date(), wake_obj)
                    live_h_wake = max(0, (wake_dt - now).total_seconds() / 3600) if now < wake_dt else 0
                    live_h_bed = onboarding_mgr.get_hours_until_bedtime(now, wake_obj, sleep_hours)

                time_status_text.value = _build_status_msg(live_h_wake, live_h_bed)

                try:
                    page.update()
                except Exception as e:
                    # Stop the loop cleanly if the page is disconnected
                    if PageDisconnectedException is not None and isinstance(e, PageDisconnectedException):
                        break
                    # Fall back: check by name for environments where import differs
                    if e.__class__.__name__ == "PageDisconnectedException":
                        break
                    # otherwise ignore transient assertion/attribute errors
                    pass
            except (AssertionError, AttributeError):
                # Controls may be detached; continue until page update fails explicitly
                pass
            time.sleep(1)
    
    # Get upcoming tasks from database
    from state.task_manager import TaskManager
    task_manager = TaskManager()
    upcoming_tasks = task_manager.get_upcoming_tasks(user_id) if user_id else []
    
    # Create time display section
    username = "there"
    if session:
        user_obj = session.get("user")
        if user_obj and hasattr(user_obj, "username") and user_obj.username:
            username = user_obj.username.split()[0]
        elif user_obj and isinstance(user_obj, dict) and user_obj.get("username"):
            username = user_obj["username"].split()[0]

    # Prefer a static UI avatar from assets for dashboard branding.
    ui_avatar_candidates = [
        "ui/lowkey-hyped.png",
        "ui/greeting_avatar.png",
        "ui/greeting_avatar.jpg",
        "ui/greeting_avatar.jpeg",
        "greeting_avatar.png",
        "avatar.png",
    ]
    avatar_src = next(
        (
            candidate
            for candidate in ui_avatar_candidates
            if os.path.exists(os.path.join("assets", candidate))
        ),
        None,
    )

    # Fallback to user profile photo if no dedicated UI asset exists yet.
    if not avatar_src and session:
        user_obj = session.get("user")
        if user_obj and hasattr(user_obj, "profile_photo") and user_obj.profile_photo:
            avatar_src = user_obj.profile_photo
        elif user_obj and isinstance(user_obj, dict):
            avatar_src = user_obj.get("profile_photo") or user_obj.get("profile_image") or user_obj.get("avatar_path")

    avatar_fallback = ft.Container(
        bgcolor="#E4EAF4",
        width=92,
        height=92,
        border_radius=46,
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.PERSON, color="#7E8DA5", size=40),
    )

    avatar_content = avatar_fallback
    if avatar_src:
        avatar_content = ft.Container(
            width=92,
            height=92,
            border_radius=46,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Image(src=avatar_src, width=92, height=92, fit=ft.ImageFit.COVER),
        )

    time_section = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Container(
                    width=92,
                    height=92,
                    right=8,
                    top=6,
                    border_radius=46,
                    bgcolor="transparent",
                    shadow=drop_shadow,
                    content=avatar_content,
                ),
                ft.Column(
                    controls=[
                        ft.Text(f"Hey, {username}! It's:", size=20, color=title_color, weight=ft.FontWeight.W_600),
                        time_text,
                        ft.Container(content=day_date_text, margin=ft.margin.only(top=-4)),
                        ft.Container(height=12),
                        time_status_container,
                    ],
                    spacing=0,
                ),
            ],
        ),
        padding=ft.padding.only(left=24, right=24, top=66, bottom=16),
    )

    # Start time update thread
    thread = threading.Thread(target=update_time, daemon=True)
    thread.start()

    # Calculate today's schedule data
    schedule_manager = ScheduleManager()
    today = datetime.now().date()
    free_minutes_today = schedule_manager.compute_free_time_today(user_id, today) if user_id else 0
    
    two_days_ahead = today + timedelta(days=2)
    needed_tasks = [
        t for t in upcoming_tasks
        if t.date_due and datetime.strptime(t.date_due, "%Y-%m-%d").date() <= two_days_ahead
    ]
    total_needed_minutes = sum(t.estimated_time or 0 for t in needed_tasks)
    
    minutes_surplus = free_minutes_today - total_needed_minutes
    if minutes_surplus >= 0:
        if minutes_surplus > 240:
            budget_verdict = "✓ You have room."
            verdict_color = "#2E7D32"
        else:
            budget_verdict = "✓ Tight, but doable."
            verdict_color = "#E65100"
    else:
        budget_verdict = f"⚠ You're short by {format_minutes(abs(minutes_surplus))}. Something has to move."
        verdict_color = "#C62828"

    def go_to_task_details(task_id):
        if not task_id:
            return
        if session is not None:
            session["selected_task_id"] = task_id
            session["task_details_create_mode"] = False
            session["task_details_edit_mode"] = False
        page.route = f"/tasks/{task_id}"
        route_change = session.get("route_change") if session else None
        if callable(route_change):
            route_change(page.route)
        else:
            page.update()
    
    # Create task items - compact single-row display
    task_items = []
    for task in upcoming_tasks:
        # Compute relative due label
        if task.date_due:
            try:
                due_date_obj = datetime.strptime(task.date_due, "%Y-%m-%d").date()
                delta_days = (due_date_obj - datetime.now().date()).days
                if delta_days < 0:
                    due_label = "overdue"
                elif delta_days == 0:
                    due_label = "today"
                elif delta_days == 1:
                    due_label = "tmrw"
                elif delta_days <= 7:
                    due_label = f"{delta_days}d"
                else:
                    due_label = due_date_obj.strftime("%b %d")
            except:
                due_label = task.date_due
        else:
            due_label = "no due"

        est_time_str = format_minutes(task.estimated_time) if task.estimated_time else "—"

        task_items.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            task.title,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=title_color,
                            expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            est_time_str,
                            size=12,
                            color=accent_color,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Container(width=8),
                        ft.Text(
                            due_label,
                            size=11,
                            color="#A43228" if due_label == "overdue" else accent_color,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                border_radius=8,
                bgcolor="#FFFFFF",
                border=ft.border.all(1, "#8D9BB0"),
                margin=ft.margin.only(bottom=5),
                ink=True,
                on_click=lambda e, task_id=task.id: go_to_task_details(task_id),
            )
        )

    upcoming_tasks_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Coming Up", size=16, weight=ft.FontWeight.W_700, color=title_color),
                ft.Divider(height=1, thickness=1, color=border_color),
                ft.Container(height=8),
                ft.Column(
                    controls=task_items if task_items else [
                        ft.Text("No upcoming tasks.", size=13, color=accent_color)
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    height=220,
                    spacing=0,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=16),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
        margin=ft.margin.symmetric(horizontal=24),
    )
    
    # Handle navigation to analytics page
    def go_to_analytics(e):
        page.route = "/analytics"
        page.update()

    time_budget_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Today's Budget", size=16, weight=ft.FontWeight.W_700, color=title_color),
                ft.Divider(height=1, thickness=1, color=border_color),
                ft.Container(height=6),
                ft.Row(
                    controls=[
                        ft.Text("Free time (after classes)", size=12, color=accent_color),
                        ft.Text(
                            format_minutes(free_minutes_today),
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=title_color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=4),
                ft.Row(
                    controls=[
                        ft.Text("Tasks due in 2 days", size=12, color=accent_color),
                        ft.Text(
                            format_minutes(total_needed_minutes),
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=title_color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=4),
                ft.Text(
                    budget_verdict,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=verdict_color,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=20),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
        margin=ft.margin.symmetric(horizontal=24),
    )

    # Today's stats (compact)
    total_tasks_count = len(upcoming_tasks)
    completed_today_count = task_manager.get_tasks_completed_today(user_id) if user_id else 0

    stats_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    f"{completed_today_count} done today",
                    size=13,
                    color=title_color,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(width=1, height=14, bgcolor=border_color),
                ft.Text(
                    f"{total_tasks_count} upcoming",
                    size=13,
                    color=accent_color,
                ),
                ft.Container(expand=True),
                ft.TextButton(
                    "View Analytics →",
                    style=ft.ButtonStyle(color=accent_color),
                    on_click=go_to_analytics,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
        margin=ft.margin.symmetric(horizontal=24),
    )

    dashboard_container = ft.Container(
        content=ft.Column(
            controls=[
                time_section,
                ft.Container(height=8),
                time_budget_section,
                ft.Container(height=16),
                upcoming_tasks_section,
                ft.Container(height=16),
                stats_row,
                ft.Container(height=24),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#DDE9FB", "#FFFFFF"],
        ),
    )

    return dashboard_container