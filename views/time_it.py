import flet as ft
from datetime import datetime, timedelta
import time
import threading
from state.task_manager import TaskManager
from state.session_manager import SessionManager
from utils.time_helpers import format_minutes


def TimeItPage(page: ft.Page, session: dict = None):
    """
    Time It page with Timer and Log modes for tracking task sessions
    
    Args:
        page: Flet page
        session: Session with user info
    """
    
    # Check if user is logged in
    if not session or not session.get("user"):
        return ft.Container(
            content=ft.Text("Please login first", size=20),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    task_manager = TaskManager()
    session_manager = SessionManager()
    user_id = session["user"].id
    
    # Load user tasks
    user_tasks = task_manager.get_user_tasks(user_id, status_filter="Not Started")
    user_tasks.extend(task_manager.get_user_tasks(user_id, status_filter="In Progress"))
    user_tasks.extend(task_manager.get_user_tasks(user_id, status_filter="Started"))

    draft = session.get("time_it_draft", {}) or {}
    
    # Timer state
    timer_running = False
    timer_paused = False
    elapsed_seconds = int(draft.get("elapsed_seconds", 0) or 0)
    selected_task_id = None
    timer_thread_active = True
    
    # ==================== TIMER MODE ====================
    
    # Timer display (MM:SS format)
    timer_display = ft.Text(
        "00:00",
        size=72,
        weight=ft.FontWeight.W_700,
        color=ft.Colors.BLUE_700,
        text_align=ft.TextAlign.CENTER,
    )
    
    # Task dropdown for timer mode
    timer_options = [
        ft.dropdown.Option(f"{task.title} (ID: {task.id})")
        for task in user_tasks
    ] if user_tasks else [ft.dropdown.Option("No active tasks")]
    timer_option_values = {opt.key for opt in timer_options}
    draft_task_value = draft.get("task_dropdown_value")
    initial_task_value = None
    if draft_task_value in timer_option_values:
        initial_task_value = draft_task_value
    elif user_tasks:
        initial_task_value = f"{user_tasks[0].title} (ID: {user_tasks[0].id})"

    timer_task_dropdown = ft.Dropdown(
        label="Select Task",
        width=350,
        options=timer_options,
        value=initial_task_value,
        border_color=ft.Colors.GREY_400,
    )

    if elapsed_seconds > 0:
        timer_display.value = f"{elapsed_seconds // 60:02d}:{elapsed_seconds % 60:02d}"
    
    def update_timer_display():
        """Update timer display every second"""
        nonlocal timer_running, timer_paused, elapsed_seconds
        
        while timer_thread_active:
            try:
                if timer_running and not timer_paused:
                    elapsed_seconds += 1
                    minutes = elapsed_seconds // 60
                    seconds = elapsed_seconds % 60
                    timer_display.value = f"{minutes:02d}:{seconds:02d}"
                    timer_display.update()
            except (AssertionError, AttributeError):
                # Control may have been detached from page if user navigated away
                pass
            time.sleep(1)
    
    timer_thread = threading.Thread(target=update_timer_display, daemon=True)
    timer_thread.start()

    def save_timer_draft():
        if elapsed_seconds > 0:
            session["time_it_draft"] = {
                "elapsed_seconds": elapsed_seconds,
                "task_dropdown_value": timer_task_dropdown.value,
            }
        else:
            session.pop("time_it_draft", None)

    def cleanup_time_it(preserve_progress: bool = True):
        nonlocal timer_running, timer_paused, timer_thread_active
        if preserve_progress:
            save_timer_draft()
        else:
            session.pop("time_it_draft", None)
        timer_running = False
        timer_paused = False
        timer_thread_active = False

    def discard_current_session():
        nonlocal timer_running, timer_paused, elapsed_seconds
        timer_running = False
        timer_paused = False
        elapsed_seconds = 0
        session.pop("time_it_draft", None)
        try:
            timer_display.value = "00:00"
            start_button.disabled = False
            pause_button.disabled = True
            pause_button.text = "Pause"
            stop_button.disabled = True
            timer_task_dropdown.disabled = False
            page.update()
        except (AssertionError, AttributeError):
            pass

    session["time_it_is_timer_running"] = lambda: timer_running and not timer_paused
    session["time_it_is_timer_paused"] = lambda: timer_running and timer_paused
    session["time_it_has_active_progress"] = lambda: elapsed_seconds > 0
    session["time_it_cleanup"] = cleanup_time_it
    session["time_it_discard_current_session"] = discard_current_session

    def extract_task_id(dropdown_value: str):
        if dropdown_value and "(ID:" in dropdown_value:
            try:
                return int(dropdown_value.split("(ID: ")[1].rstrip(")"))
            except (ValueError, IndexError):
                return None
        return None
    
    def start_timer(e):
        nonlocal timer_running, timer_paused
        task_id = extract_task_id(timer_task_dropdown.value)
        if task_id is None:
            show_message("Please select a valid task before starting the timer", "warning")
            return
        timer_running = True
        timer_paused = False
        start_button.disabled = True
        pause_button.disabled = False
        stop_button.disabled = False
        timer_task_dropdown.disabled = True
        page.update()
    
    def pause_timer(e):
        nonlocal timer_paused
        timer_paused = not timer_paused
        pause_button.text = "Resume" if timer_paused else "Pause"
        if timer_paused:
            save_timer_draft()
        page.update()
    
    def stop_timer(e):
        nonlocal timer_running, timer_paused, elapsed_seconds
        # Extract task ID from dropdown
        nonlocal selected_task_id
        selected_task_id = extract_task_id(timer_task_dropdown.value)
        if selected_task_id is None:
            show_message("Please select a valid task before stopping the timer", "warning")
            return

        timer_running = False
        timer_paused = False
        
        if elapsed_seconds == 0:
            show_message("Timer has no elapsed time", "warning")
            start_button.disabled = False
            pause_button.disabled = True
            pause_button.text = "Pause"
            stop_button.disabled = True
            timer_task_dropdown.disabled = False
            page.update()
            return
        
        # Convert seconds to minutes (round down)
        duration_minutes = elapsed_seconds // 60
        if duration_minutes < 1:
            show_message("Sessions under 1 minute are not logged.", "warning")
            elapsed_seconds = 0
            session.pop("time_it_draft", None)
            timer_display.value = "00:00"
            timer_display.update()

            start_button.disabled = False
            pause_button.disabled = True
            pause_button.text = "Pause"
            stop_button.disabled = True
            timer_task_dropdown.disabled = False
            page.update()
            return
        
        # Log session
        success, message, logged_session = session_manager.add_session(
            user_id=user_id,
            task_id=selected_task_id,
            duration_minutes=duration_minutes,
            notes=None,
        )
        
        if success:
            show_message(f"Session logged: {format_minutes(duration_minutes)}", "success")
            # Reset timer
            elapsed_seconds = 0
            session.pop("time_it_draft", None)
            timer_display.value = "00:00"
            timer_display.update()
            refresh_session_history()
        else:
            show_message(message, "error")
        
        # Reset button states
        start_button.disabled = False
        pause_button.disabled = True
        pause_button.text = "Pause"
        stop_button.disabled = True
        timer_task_dropdown.disabled = False
        page.update()
    
    # Timer buttons
    start_button = ft.ElevatedButton(
        "Start",
        on_click=start_timer,
        width=100,
    )
    
    pause_button = ft.ElevatedButton(
        "Pause",
        on_click=pause_timer,
        width=100,
        disabled=True,
    )
    
    stop_button = ft.ElevatedButton(
        "Stop",
        on_click=stop_timer,
        width=100,
        disabled=True,
    )
    
    timer_buttons_row = ft.Row(
        controls=[start_button, pause_button, stop_button],
        spacing=12,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    if elapsed_seconds > 0 and extract_task_id(timer_task_dropdown.value) is not None:
        timer_running = True
        timer_paused = True
        start_button.disabled = True
        pause_button.disabled = False
        pause_button.text = "Resume"
        stop_button.disabled = False
        timer_task_dropdown.disabled = True
    
    timer_mode_content = ft.Column(
        controls=[
            ft.Text("Timer Mode", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
            ft.Container(
                content=ft.Text(
                    "Note: Switching app tabs pauses the timer! Keep this page open to track time AND to stay aware of why you're here ദ്ദി◝ ⩊ ◜.ᐟ",
                    size=12,
                    color=ft.Colors.ORANGE_800,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ft.Colors.ORANGE_50,
                border=ft.border.all(1, ft.Colors.ORANGE_200),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                width=520,
                alignment=ft.alignment.center,
            ),
            ft.Container(height=12),
            timer_task_dropdown,
            ft.Container(height=20),
            timer_display,
            ft.Container(height=20),
            timer_buttons_row,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # ==================== LOG MODE ====================
    
    # Task dropdown for log mode
    log_task_dropdown = ft.Dropdown(
        label="Select Task",
        width=350,
        options=[
            ft.dropdown.Option(f"{task.title} (ID: {task.id})") 
            for task in user_tasks
        ] if user_tasks else [ft.dropdown.Option("No active tasks")],
        value=f"{user_tasks[0].title} (ID: {user_tasks[0].id})" if user_tasks else None,
        border_color=ft.Colors.GREY_400,
    )
    
    # Minutes input field
    minutes_input = ft.TextField(
        label="Duration (minutes)",
        width=350,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.Colors.GREY_400,
        hint_text="e.g., 45",
    )
    
    # Notes field
    notes_input = ft.TextField(
        label="Notes (optional)",
        width=350,
        border_color=ft.Colors.GREY_400,
        multiline=True,
        min_lines=2,
        max_lines=4,
        hint_text="What did you accomplish?",
    )

    user_tasks_for_history = task_manager.get_user_tasks(user_id, include_deleted=False)
    task_titles_by_id = {
        task.id: task.title for task in user_tasks_for_history if task.id is not None
    }
    session_history_container = ft.Column(spacing=8)
    history_filter_mode = "today"
    history_search_query = ""

    history_title_text = ft.Text("Session History (Today)", size=16, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    history_total_label = ft.Text("Total Session Time", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600)
    history_total_value = ft.Text(format_minutes(0), size=18, color=ft.Colors.GREY_900, weight=ft.FontWeight.W_700)

    history_today_button = ft.ElevatedButton("Today")
    history_week_button = ft.ElevatedButton("This Week")
    history_all_button = ft.ElevatedButton("All")
    history_search_field = ft.TextField(
        label="Search history",
        hint_text="Filter by task or notes",
        width=320,
        border_color=ft.Colors.GREY_400,
    )

    def update_history_toggle_buttons():
        is_today = history_filter_mode == "today"
        is_week = history_filter_mode == "week"
        history_today_button.bgcolor = ft.Colors.GREY_800 if is_today else ft.Colors.GREY_200
        history_today_button.color = ft.Colors.WHITE if is_today else ft.Colors.GREY_700
        history_week_button.bgcolor = ft.Colors.GREY_800 if is_week else ft.Colors.GREY_200
        history_week_button.color = ft.Colors.WHITE if is_week else ft.Colors.GREY_700
        history_all_button.bgcolor = ft.Colors.GREY_800 if history_filter_mode == "all" else ft.Colors.GREY_200
        history_all_button.color = ft.Colors.WHITE if history_filter_mode == "all" else ft.Colors.GREY_700

    def refresh_session_history():
        nonlocal history_search_query
        if history_filter_mode == "today":
            sessions = session_manager.get_sessions_for_user_today(user_id)
        elif history_filter_mode == "week":
            all_sessions = session_manager.get_sessions_for_user(user_id)
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            next_week_start = week_start + timedelta(days=7)
            sessions = []
            for session_item in all_sessions:
                if not session_item.logged_at:
                    continue
                try:
                    logged_date = datetime.fromisoformat(session_item.logged_at).date()
                except ValueError:
                    continue
                if week_start <= logged_date < next_week_start:
                    sessions.append(session_item)
        else:
            sessions = session_manager.get_sessions_for_user(user_id)

        q = history_search_query.strip().lower()
        if q:
            filtered_sessions = []
            for session_item in sessions:
                title = task_titles_by_id.get(session_item.task_id, f"Task #{session_item.task_id}")
                notes = session_item.notes or ""
                if q in title.lower() or q in notes.lower():
                    filtered_sessions.append(session_item)
            sessions = filtered_sessions

        session_history_container.controls.clear()
        if history_filter_mode == "today":
            history_title_text.value = "Session History (Today)"
        elif history_filter_mode == "week":
            history_title_text.value = "Session History (This Week)"
        else:
            history_title_text.value = "Session History (All)"
        total_minutes = sum(session.duration_minutes or 0 for session in sessions)
        history_total_value.value = format_minutes(total_minutes)
        update_history_toggle_buttons()

        if not sessions:
            empty_msg = (
                "No sessions logged yet today."
                if history_filter_mode == "today"
                else "No sessions logged yet this week."
                if history_filter_mode == "week"
                else "No sessions logged yet."
            )
            session_history_container.controls.append(
                ft.Text(
                    empty_msg,
                    size=12,
                    color=ft.Colors.GREY_600,
                )
            )
        else:
            for logged_session in reversed(sessions):
                title = task_titles_by_id.get(logged_session.task_id, f"Task #{logged_session.task_id}")
                logged_at_text = ""
                if logged_session.logged_at:
                    try:
                        logged_at_text = datetime.fromisoformat(logged_session.logged_at).strftime("%b %d, %I:%M %p")
                    except ValueError:
                        logged_at_text = str(logged_session.logged_at)

                session_history_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                                        ft.Container(expand=True),
                                        ft.Text(format_minutes(logged_session.duration_minutes), size=12, color=ft.Colors.BLUE_700),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(logged_at_text, size=11, color=ft.Colors.GREY_600),
                                ft.Text(logged_session.notes, size=11, color=ft.Colors.GREY_700)
                                if logged_session.notes
                                else ft.Container(height=0),
                            ],
                            spacing=2,
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=6,
                        bgcolor=ft.Colors.GREY_50,
                    )
                )

        if session_history_container.page is not None:
            session_history_container.update()

    def show_today_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "today"
        refresh_session_history()
        page.update()

    def show_all_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "all"
        refresh_session_history()
        page.update()

    def on_history_search_change(e):
        nonlocal history_search_query
        history_search_query = e.control.value or ""
        refresh_session_history()
        page.update()

    def show_week_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "week"
        refresh_session_history()
        page.update()

    history_today_button.on_click = show_today_history
    history_week_button.on_click = show_week_history
    history_all_button.on_click = show_all_history
    history_search_field.on_change = on_history_search_change
    
    def submit_log(e):
        # Extract task ID
        task_id = extract_task_id(log_task_dropdown.value)
        if task_id is None:
            show_message("Please select a task", "warning")
            return
        
        # Validate minutes
        if not minutes_input.value or minutes_input.value.strip() == "":
            show_message("Please enter duration in minutes", "warning")
            return
        
        try:
            duration_minutes = int(minutes_input.value)
            if duration_minutes <= 0:
                show_message("Duration must be a positive number", "warning")
                return
        except ValueError:
            show_message("Duration must be a valid number", "warning")
            return
        
        # Log session
        notes = notes_input.value.strip() if notes_input.value else None
        success, message, logged_session = session_manager.add_session(
            user_id=user_id,
            task_id=task_id,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        
        if success:
            show_message(f"Session logged: {format_minutes(duration_minutes)}", "success")
            # Clear inputs
            minutes_input.value = ""
            notes_input.value = ""
            refresh_session_history()
            page.update()
        else:
            show_message(message, "error")
    
    submit_button = ft.ElevatedButton(
        "Submit",
        on_click=submit_log,
        width=200,
    )
    
    log_mode_content = ft.Column(
        controls=[
            ft.Text("Log Mode", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
            ft.Container(height=12),
            log_task_dropdown,
            ft.Container(height=12),
            minutes_input,
            ft.Container(height=12),
            notes_input,
            ft.Container(height=20),
            submit_button,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # ==================== MODE TOGGLE ====================
    
    # Create tabs for mode selection
    def on_tabs_change(e):
        nonlocal timer_paused
        if e.control.selected_index == 1 and timer_running and not timer_paused:
            timer_paused = True
            pause_button.text = "Resume"
            save_timer_draft()
            show_message("Timer auto-paused after switching to Log tab", "info")
            page.update()

    tabs = ft.Tabs(
        selected_index=0,
        on_change=on_tabs_change,
        tabs=[
            ft.Tab(
                text="Timer",
                content=ft.Container(
                    content=timer_mode_content,
                    padding=24,
                ),
            ),
            ft.Tab(
                text="Log",
                content=ft.Container(
                    content=log_mode_content,
                    padding=24,
                ),
            ),
        ],
    )

    mode_panel = ft.Container(
        content=tabs,
        height=450,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        padding=ft.padding.only(bottom=8),
    )

    history_panel = ft.Container(
        content=session_history_container,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        padding=10,
    )

    refresh_session_history()
    
    # ==================== STATUS MESSAGE ====================
    
    status_message = ft.Text(
        "",
        size=14,
        weight=ft.FontWeight.W_500,
        visible=False,
    )
    
    def show_message(text: str, msg_type: str = "info"):
        """Display a status message"""
        color_map = {
            "success": ft.Colors.GREEN_700,
            "error": ft.Colors.RED_700,
            "warning": ft.Colors.ORANGE_700,
            "info": ft.Colors.BLUE_700,
        }
        status_message.value = text
        status_message.color = color_map.get(msg_type, ft.Colors.BLUE_700)
        status_message.visible = True
        status_message.update()
        
        # Auto-hide after 3 seconds
        def hide_message():
            time.sleep(3)
            try:
                status_message.visible = False
                status_message.update()
            except (AssertionError, AttributeError):
                # Control may have been detached from page if user navigated away
                pass
        
        threading.Thread(target=hide_message, daemon=True).start()
    
    # ==================== MAIN LAYOUT ====================
    
    # Header
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Time It", size=32, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
                ft.Text(
                    "Track time on tasks with Timer or Log modes",
                    size=14,
                    color=ft.Colors.GREY_600,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(
                    height=1,
                    bgcolor=ft.Colors.GREY_300,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=4,
        ),
        padding=ft.padding.only(left=24, top=20, bottom=0),
    )
    
    # Content area
    content = ft.Container(
        content=ft.Column(
            controls=[
                mode_panel,
                ft.Container(height=24),
                history_title_text,
                ft.Container(height=8),
                ft.Row(
                    controls=[history_today_button, history_week_button, history_all_button],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=8),
                history_search_field,
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            history_total_label,
                            ft.Container(expand=True),
                            history_total_value,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                ),
                ft.Container(height=8),
                history_panel,
                ft.Container(height=20),
                status_message,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
    )
    
    # Main page layout
    return ft.Column(
        controls=[
            header,
            content,
        ],
        spacing=0,
        expand=True,
    )
