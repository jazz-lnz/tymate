import flet as ft
from datetime import datetime, timedelta
import time
import threading
from state.task_manager import TaskManager
from models.task import CATEGORIES, STATUSES
from utils.time_helpers import format_minutes

def TasksPage(page: ft.Page, session: dict = None):
    """
    Tasks management page with full CRUD functionality (Minimalist line-based design)
    
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
    user_id = session["user"].id
    EST_COLUMN_WIDTH = 130
    CATEGORY_COLUMN_WIDTH = 170
    STATUS_COLUMN_WIDTH = 115
    DUE_COLUMN_WIDTH = 130
    REPEAT_COLUMN_WIDTH = 120

    # Add database lock to prevent recursive cursor usage
    db_lock = threading.Lock()
    
    search_query = "" # for search button

    # Current filter (due-date based)
    current_filter = "week"
    # Current sort option
    sort_option = "Date"
    
    # Track current tasks for responsive rebuild
    current_tasks = []
    
    # Get current date/time
    now = datetime.now()
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=48, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    date_text = ft.Text(now.strftime("%A, %B %d. %Y"), size=16, color=ft.Colors.GREY_600)

    def go_to(route: str):
        page.route = route
        route_change = session.get("route_change") if session else None
        if callable(route_change):
            route_change(route)

    def update_time():
        while True:
            try:
                now = datetime.now()
                time_text.value = now.strftime("%I:%M:%S %p")
                date_text.value = now.strftime("%A, %B %d. %Y")
                time_text.update()
                date_text.update()
            except:
                pass  # Ignore errors during page updates
            time.sleep(1)

    thread = threading.Thread(target=update_time, daemon=True)
    thread.start()

    time_display = ft.Column(
        controls=[
            ft.Text("Current Time", size=14, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500),
            ft.Container(height=4),
            time_text,
            date_text,
        ],
        spacing=0,
    )
    
    # Task list container
    task_list_container = ft.Column(spacing=0)
    
    # Filter tabs container (will be updated dynamically)
    filter_tabs_container = ft.Row(spacing=8)
    
    # Total time display (define before load_tasks)
    total_time_text = ft.Text(format_minutes(0), size=18, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    total_time_label = ft.Text("Total Estimated Time", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600)
    
    # Status message display
    status_message_text = ft.Text("", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500)
    feedback_dialog = None

    def show_action_feedback(message: str, kind: str = "info"):
        """Show transient action feedback (success/error/info)."""
        nonlocal feedback_dialog
        color_map = {
            "success": ft.Colors.GREEN_700,
            "error": ft.Colors.RED_700,
            "warning": ft.Colors.ORANGE_700,
            "info": ft.Colors.BLUE_700,
        }
        title_map = {
            "success": "Success",
            "error": "Error",
            "warning": "Warning",
            "info": "Notice",
        }

        if feedback_dialog is not None:
            feedback_dialog.open = False

        feedback_dialog = ft.AlertDialog(
            title=ft.Text(title_map.get(kind, "Notice"), color=color_map.get(kind, ft.Colors.BLUE_700)),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: setattr(feedback_dialog, "open", False) or page.update()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(feedback_dialog)
    
    def get_status_message():
        """Get time status message similar to dashboard"""
        try:
            from state.onboarding_manager import OnboardingManager
            
            onboarding_mgr = OnboardingManager()
            current_time = datetime.now()
            remaining = onboarding_mgr.get_remaining_budget(user_id, current_time)
            
            color_map = {
                "red": ft.Colors.RED_700,
                "orange": ft.Colors.ORANGE_700,
                "yellow": ft.Colors.AMBER_700,
                "green": ft.Colors.GREEN_700,
                "blue": ft.Colors.BLUE_700,
            }
            
            time_status_msg = ""
            time_status_color = ft.Colors.GREY_700
            
            if remaining and "time_status" in remaining:
                # Use 'time_status' key from the returned dict
                time_status_msg = remaining.get("time_status", "")
                status_color_key = remaining.get("time_status_color", "green")
                time_status_color = color_map.get(status_color_key, ft.Colors.GREEN_700)
            
            return time_status_msg, time_status_color
        except Exception as e:
            print(f"Error getting status message: {e}")
            import traceback
            traceback.print_exc()
            return "", ft.Colors.GREY_700
    
    def update_status_message():
        """Update the status message display"""
        try:
            msg, color = get_status_message()
            status_message_text.value = msg
            status_message_text.color = color
            if status_message_text.page is not None:
                status_message_text.update()
        except Exception as e:
            print(f"Error updating status message: {e}")
            # Silently fail to avoid breaking the page
    
    def get_total_estimated_time():
        """Calculate sum of estimated time for non-completed tasks"""
        total = 0
        for task in current_tasks:
            if task.status != "Completed" and task.estimated_time is not None:
                total += task.estimated_time
        return total
    
    def update_total_time():
        """Update the total estimated time display"""
        total = get_total_estimated_time()
        total_time_text.value = format_minutes(total)
        if total_time_text.page is not None:
            total_time_text.update()

    def parse_due_date(task):
        """Parse task due date (YYYY-MM-DD) into a date object."""
        if not task.date_due:
            return None
        try:
            return datetime.strptime(task.date_due, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def is_in_current_due_filter(task):
        """Return True if task matches the selected due-date window."""
        due_date = parse_due_date(task)
        if current_filter == "all":
            return True
        if due_date is None:
            return False

        today = datetime.now().date()
        if current_filter == "today":
            return due_date == today
        if current_filter == "week":
            week_start = today - timedelta(days=today.weekday())
            next_week_start = week_start + timedelta(days=7)
            return week_start <= due_date < next_week_start
        if current_filter == "overdue":
            return due_date < today and task.status != "Completed"
        return True

    def load_tasks(filter_status=None):
        # Acquire lock before database operations - prevents app freeze due to recursive cursor use
        with db_lock:
            # show loading indicator
            task_list_container.controls.clear()
            task_list_container.controls.append(
                ft.Container(
                    content=ft.ProgressRing(width=30, height=30, color=ft.Colors.GREY_600),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
            # only update the control if it's already attached to the page
            if task_list_container.page is not None:
                task_list_container.update()

            nonlocal current_filter, search_query
            current_filter = filter_status or "all"

            # Load all tasks from your TaskManager
            tasks = task_manager.get_user_tasks(user_id, include_deleted=False)

        # Apply due-date filtering
        tasks = [t for t in tasks if is_in_current_due_filter(t)]

        # Apply search filter
        if search_query.strip() != "":
            q = search_query.lower()
            tasks = [
                t for t in tasks
                if q in t.title.lower()
                or q in t.source.lower()
                or q in t.category.lower()
            ]

        # Sort tasks by date_due (earliest first)
        tasks.sort(key=lambda t: t.date_due if t.date_due else "9999-12-31")

        # Clear and rebuild UI
        task_list_container.controls.clear()

        if not tasks:
            task_list_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No matching tasks found.",
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            nonlocal current_tasks
            current_tasks = tasks
            for task in tasks:
                task_list_container.controls.append(create_task_card(task))

        # Update filter tabs to reflect current selection
        update_filter_tabs()
        
        # Update total estimated time
        update_total_time()
        
        # Defer status message update to avoid cursor conflict
        def deferred_status_update():
            time.sleep(0.1)  # Small delay to ensure DB operations complete
            try:
                update_status_message()
            except:
                pass
        
        threading.Thread(target=deferred_status_update, daemon=True).start()
        
        # Only update task list container if it's already attached to the page (skip on initial load of tasks)
        if task_list_container.page is not None:
            task_list_container.update()
        if filter_tabs_container.page is not None:
            filter_tabs_container.update()

    
    def create_task_card(task):
        """Create a task card UI element (Minimalist line-based design - responsive with wrapping)"""
        
        # Status badge color
        status_colors = {
            "Not Started": ft.Colors.GREY_400,
            "In Progress": ft.Colors.BLUE_400,
            "Completed": ft.Colors.GREEN_600,
                "Started": ft.Colors.BLUE_300,
        }
        
        due_label = f"Due: {task.date_due}" if task.date_due else "Due: No due date"
        recurrence_label = ""
        if task.is_recurring and task.recurrence_type:
            recurrence_label = f"Repeats: {task.recurrence_type.title()}"
            if task.recurrence_until:
                recurrence_label += f" until {task.recurrence_until}"

        # Check if overdue
        is_overdue = task.is_overdue()
        # Responsive: stack on mobile, single row on desktop
        is_mobile = page.window.width < 768
        
        if is_mobile:
            # Mobile: Stacked layout for readability
            return ft.Container(
                content=ft.Column(
                    controls=[
                        # First row: source and status summary
                        ft.Row(
                            controls=[
                                ft.Text(
                                    task.source,
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        task.status,
                                        size=12,
                                        color=ft.Colors.WHITE if task.status != "Not Started" else ft.Colors.GREY_800,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=status_colors.get(task.status, ft.Colors.GREY_300),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=4,
                                ),
                            ],
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        
                        # Second row: task title opens details
                        ft.TextButton(
                            text=task.title,
                            on_click=lambda e, t=task: open_task_details(t),
                            style=ft.ButtonStyle(
                                padding=0,
                                color={
                                    ft.ControlState.DEFAULT: ft.Colors.GREY_900 if task.status != "Completed" else ft.Colors.GREY_600,
                                },
                                text_style=ft.TextStyle(
                                    size=17,
                                    weight=ft.FontWeight.W_600 if task.status != "Completed" else ft.FontWeight.W_400,
                                ),
                                overlay_color=ft.Colors.TRANSPARENT,
                            ),
                        ),
                        
                        # Third row: category, status, due date, time
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        task.category, 
                                        size=12,
                                        color=ft.Colors.GREY_800,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=ft.Colors.GREY_100,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=4,
                                    border=ft.border.all(1, ft.Colors.GREY_300),
                                ),
                                ft.Text(
                                    due_label,
                                    size=13,
                                    color=ft.Colors.RED_600 if is_overdue else ft.Colors.GREY_600,
                                    weight=ft.FontWeight.W_500 if is_overdue else ft.FontWeight.W_400,
                                ),
                                ft.Text(
                                    recurrence_label,
                                    size=12,
                                    color=ft.Colors.BLUE_700,
                                    weight=ft.FontWeight.W_500,
                                    visible=bool(recurrence_label),
                                ),
                                ft.Text(
                                    f"Est: {format_minutes(task.estimated_time)}" if task.estimated_time is not None else "—",
                                    size=13,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            spacing=8,
                            wrap=True,
                        ),
                    ],
                    spacing=6,
                ),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=6,
                padding=12,
                margin=ft.margin.only(bottom=6),
            )
        else:
            # Desktop: Single row layout
            return ft.Container(
                content=ft.Row(
                    controls=[
                        # Source (before title)
                        ft.Text(
                            task.source,
                            size=13,
                            color=ft.Colors.GREY_700,
                            width=110,
                        ),
                        
                        # Task title opens details
                        ft.TextButton(
                            text=task.title,
                            on_click=lambda e, t=task: open_task_details(t),
                            style=ft.ButtonStyle(
                                padding=0,
                                color={
                                    ft.ControlState.DEFAULT: ft.Colors.GREY_900 if task.status != "Completed" else ft.Colors.GREY_600,
                                },
                                text_style=ft.TextStyle(
                                    size=16,
                                    weight=ft.FontWeight.W_600 if task.status != "Completed" else ft.FontWeight.W_400,
                                ),
                                overlay_color=ft.Colors.TRANSPARENT,
                                alignment=ft.Alignment(-1, 0),
                            ),
                            expand=True,
                        ),
                        
                        # Category label (neutral to avoid status color confusion)
                        ft.Container(
                            content=ft.Text(
                                task.category, 
                                size=12,
                                color=ft.Colors.GREY_800,
                                weight=ft.FontWeight.W_500,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=5,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            width=CATEGORY_COLUMN_WIDTH,
                            alignment=ft.alignment.center,
                        ),
                        
                        # Due date
                        ft.Text(
                            due_label,
                            size=13,
                            color=ft.Colors.RED_600 if is_overdue else ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500 if is_overdue else ft.FontWeight.W_400,
                            width=DUE_COLUMN_WIDTH,
                        ),
                        
                        # Status badge
                        ft.Container(
                            content=ft.Text(
                                task.status, 
                                size=12,
                                color=ft.Colors.WHITE if task.status != "Not Started" else ft.Colors.GREY_800,
                                weight=ft.FontWeight.W_500,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            bgcolor=status_colors.get(task.status, ft.Colors.GREY_300),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=5,
                            width=STATUS_COLUMN_WIDTH,
                            alignment=ft.alignment.center,
                        ),

                        ft.Text(
                            recurrence_label,
                            size=12,
                            color=ft.Colors.BLUE_700,
                            weight=ft.FontWeight.W_500,
                            width=REPEAT_COLUMN_WIDTH,
                            visible=bool(recurrence_label),
                        ),

                        # Time info
                        ft.Text(
                            f"Est: {format_minutes(task.estimated_time)}" if task.estimated_time is not None else "—",
                            size=13,
                            color=ft.Colors.GREY_600,
                            width=EST_COLUMN_WIDTH,
                            text_align=ft.TextAlign.RIGHT,
                        ),

                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    wrap=False,
                ),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=6,
                padding=12,
                margin=ft.margin.only(bottom=6),
            )
    
    def show_task_form(task=None):
        """Unified create/edit task form with date pickers and inline validation."""
        is_edit = task is not None

        title_field = ft.TextField(label="Title *", width=420, value=task.title if is_edit else "", border_color=ft.Colors.GREY_400)
        source_field = ft.TextField(
            label="Source *",
            width=420,
            value=task.source if is_edit else "",
            hint_text="e.g., CS 319, Starbucks, Personal",
            helper_text="Use consistent source names for cleaner grouping.",
            border_color=ft.Colors.GREY_400,
        )
        category_dropdown = ft.Dropdown(
            label="Category *",
            width=420,
            options=[ft.dropdown.Option(cat) for cat in CATEGORIES],
            value=task.category if is_edit else "others",
            border_color=ft.Colors.GREY_400,
        )

        date_given_field = ft.TextField(
            label="Date Given *",
            width=300,
            value=(task.date_given if is_edit else datetime.now().strftime("%Y-%m-%d")),
            border_color=ft.Colors.GREY_400,
        )
        due_date_field = ft.TextField(
            label="Due Date (optional)",
            width=300,
            value=(task.date_due if is_edit else ""),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.GREY_400,
        )

        def build_date_input(target_field: ft.TextField, label: str):
            target_field.label = label
            target_field.expand = True
            target_field.read_only = True
            target_field.filled = True
            target_field.bgcolor = ft.Colors.WHITE
            target_field.content_padding = ft.padding.symmetric(horizontal=14, vertical=14)
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=ft.Colors.BLUE_GREY_500, size=18),
                        target_field,
                        ft.IconButton(
                            icon=ft.Icons.ARROW_DROP_DOWN_CIRCLE_OUTLINED,
                            tooltip=f"Pick {label}",
                            icon_color=ft.Colors.BLUE_GREY_600,
                            on_click=lambda e: open_picker(target_field),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
            )

        def open_picker(target_field: ft.TextField):
            def on_change(e):
                if e.control.value:
                    picked = e.control.value
                    if hasattr(picked, "date"):
                        target_field.value = picked.date().isoformat()
                    else:
                        target_field.value = str(picked)
                    page.update()

            picker = ft.DatePicker(on_change=on_change)
            page.open(picker)

        estimated_time_field = ft.TextField(
            label="Estimated Minutes",
            width=200,
            value=(str(task.estimated_time) if is_edit and task.estimated_time else ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="e.g., 120",
            border_color=ft.Colors.GREY_400,
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=200,
            options=[ft.dropdown.Option(stat) for stat in STATUSES],
            value=task.status if is_edit else "Not Started",
            border_color=ft.Colors.GREY_400,
        )
        recurrence_dropdown = ft.Dropdown(
            label="Repeat",
            width=160,
            options=[
                ft.dropdown.Option("none", "No repeat"),
                ft.dropdown.Option("daily", "Daily"),
                ft.dropdown.Option("weekly", "Weekly"),
                ft.dropdown.Option("monthly", "Monthly"),
            ],
            value=(task.recurrence_type if is_edit and task.is_recurring and task.recurrence_type else "none"),
            border_color=ft.Colors.GREY_400,
        )
        recurrence_interval_field = ft.TextField(
            label="Every",
            width=90,
            value=(str(task.recurrence_interval) if is_edit and getattr(task, "recurrence_interval", None) else "1"),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="1",
            border_color=ft.Colors.GREY_400,
        )
        recurrence_until_field = ft.TextField(
            label="Repeat Until",
            width=180,
            value=(task.recurrence_until if is_edit and task.recurrence_until else ""),
            hint_text="YYYY-MM-DD",
            border_color=ft.Colors.GREY_400,
            visible=(recurrence_dropdown.value != "none"),
        )

        description_field = ft.TextField(
            label="Notes / Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=420,
            value=(task.description if is_edit and task.description else ""),
            border_color=ft.Colors.GREY_400,
        )

        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def on_repeat_change(e):
            recurrence_until_field.visible = (e.control.value != "none")
            recurrence_interval_field.visible = (e.control.value != "none")
            if e.control.value == "none":
                recurrence_until_field.value = ""
                recurrence_interval_field.value = "1"
            page.update()

        recurrence_dropdown.on_change = on_repeat_change
        recurrence_interval_field.visible = recurrence_dropdown.value != "none"

        def save_form(e):
            if not title_field.value or not title_field.value.strip():
                error_text.value = "Task title is required"
                page.update()
                return
            if not source_field.value or not source_field.value.strip():
                error_text.value = "Source is required"
                page.update()
                return
            if not date_given_field.value or not date_given_field.value.strip():
                error_text.value = "Date Given is required"
                page.update()
                return

            try:
                est_time = int(estimated_time_field.value) if estimated_time_field.value else None
            except ValueError:
                error_text.value = "Estimated minutes must be a whole number"
                page.update()
                return

            try:
                rec_interval = int(recurrence_interval_field.value or "1")
            except ValueError:
                error_text.value = "Repeat interval must be a whole number"
                page.update()
                return

            payload = dict(
                title=title_field.value.strip(),
                source=source_field.value.strip(),
                category=category_dropdown.value,
                date_given=date_given_field.value.strip(),
                date_due=due_date_field.value.strip() if due_date_field.value and due_date_field.value.strip() else None,
                description=description_field.value.strip() if description_field.value else None,
                estimated_time=est_time,
                status=status_dropdown.value,
                is_recurring=recurrence_dropdown.value != "none",
                recurrence_type=recurrence_dropdown.value if recurrence_dropdown.value != "none" else None,
                recurrence_interval=rec_interval,
                recurrence_until=recurrence_until_field.value.strip() if recurrence_until_field.value and recurrence_until_field.value.strip() else None,
            )

            if is_edit:
                success, msg = task_manager.update_task(task.id, **payload)
            else:
                success, msg, _ = task_manager.create_task(user_id=user_id, completed_at=None, **payload)

            if success:
                dialog.open = False
                load_tasks(current_filter)
                show_action_feedback(msg or ("Task updated successfully" if is_edit else "Task created successfully"), "success")
            else:
                error_text.value = msg
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Edit Task" if is_edit else "Create Task", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text("Basics", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                    title_field,
                    source_field,
                    category_dropdown,
                    ft.Container(height=8),
                    ft.Text("Schedule", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                    build_date_input(date_given_field, "Date Given *"),
                    build_date_input(due_date_field, "Due Date (optional)"),
                    ft.Container(height=8),
                    ft.Text("Time", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                    ft.Row([estimated_time_field, status_dropdown], spacing=10),
                    ft.Row([recurrence_dropdown, recurrence_interval_field, recurrence_until_field], spacing=10),
                    ft.Container(height=8),
                    ft.Text("Notes", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                    description_field,
                    error_text,
                ],
                width=500,
                tight=True,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(
                    "Save",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_form,
                ),
            ],
        )
        page.open(dialog)

    def show_add_dialog(e):
        if session is not None:
            session["task_details_create_mode"] = True
            session["task_details_edit_mode"] = True
            session["selected_task_id"] = None
        go_to("/tasks/new")

    def open_task_details(task):
        if not task or task.id is None:
            show_action_feedback("Task details are unavailable for this item", "warning")
            return
        if session is not None:
            session["selected_task_id"] = task.id
        go_to(f"/tasks/{task.id}")
    
    # Search field
    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value
        load_tasks(current_filter)

    search_field = ft.TextField(
        hint_text="Search tasks...",
        prefix_icon=ft.Icons.SEARCH,
        on_change=on_search_change,
        border_color=ft.Colors.GREY_400,
        height=50,
        expand=True,
    )

    # Filter tabs - create dynamically
    def create_filter_tab(label, status):
        def on_click(e):
            load_tasks(status)

        is_selected = (current_filter == status)

        return ft.ElevatedButton(
            label,
            bgcolor=ft.Colors.GREY_800 if is_selected else ft.Colors.GREY_200,
            color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_700,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

    def update_filter_tabs():
        """Update filter tabs to reflect current selection"""
        filter_tabs_container.controls.clear()
        filter_tabs_container.controls.extend([
            create_filter_tab("Today", "today"),
            create_filter_tab("This Week", "week"),
            create_filter_tab("Overdue", "overdue"),
            create_filter_tab("All", "all"),
        ])
    
    # Initialize filter tabs
    update_filter_tabs()
    
    # Check if mobile
    def is_mobile():
        return page.window.width < 768
    
    # Build filter row based on screen size
    def build_filter_row():
        if is_mobile():
            # Mobile: Stack vertically
            return ft.Column(
                controls=[
                    search_field,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[filter_tabs_container],
                        wrap=True,
                        spacing=6,
                        run_spacing=6,
                    ),
                    ft.Container(height=12),
                    ft.ElevatedButton(
                        "Add New Task",
                        bgcolor=ft.Colors.ORANGE_400,
                        color=ft.Colors.WHITE,
                        on_click=show_add_dialog,
                        expand=True,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6),
                        ),
                    ),
                ],
                spacing=0,
            )
        else:
            # Desktop: Horizontal with adaptive wrapping
            return ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            search_field,
                            ft.ElevatedButton(
                                "Add New Task",
                                bgcolor=ft.Colors.ORANGE_400,
                                color=ft.Colors.WHITE,
                                on_click=show_add_dialog,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[filter_tabs_container],
                        wrap=True,
                        spacing=6,
                        run_spacing=6,
                    ),
                ],
                spacing=0,
            )
    
    # Container for filter row that can be rebuilt
    filter_row_container = ft.Container(content=build_filter_row())

    task_list_view = ft.Container(
        content=ft.Column(
            controls=[task_list_container],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        padding=20,
        expand=True,
    )

    # Initial load
    load_tasks("week")

    # Rebuild task cards for responsive layout
    def rebuild_task_cards():
        """Rebuild all task cards when window resizes"""
        task_list_container.controls.clear()
        if not current_tasks:
            task_list_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No matching tasks found.",
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for task in current_tasks:
                task_list_container.controls.append(create_task_card(task))
        task_list_container.update()
    
    # Handle window resize for responsive layout
    def on_window_resize(e=None):
        try:
            if task_list_container.page is None:
                page.on_resized = None
                return
            filter_row_container.content = build_filter_row()
            rebuild_task_cards()
            update_total_time()
            update_status_message()
        except Exception:
            page.on_resized = None

    page.on_resized = on_window_resize
    
    # Build page
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("My Tasks", size=32, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
                        time_display,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    height=2,
                    bgcolor=ft.Colors.GREY_400,
                    margin=ft.margin.symmetric(vertical=20),
                ),
                
                # Responsive filter row
                filter_row_container,
                ft.Container(height=12),
                
                # Total estimated time section with status message (like "amount due" in accounting)
                ft.Container(
                    content=ft.Row(
                        controls=[
                            status_message_text,
                            ft.Container(expand=True),  # Spacer
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                total_time_label,
                                                total_time_text,
                                            ],
                                            spacing=0,
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                        ),
                                        width=EST_COLUMN_WIDTH,
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                ),
                ft.Container(height=20),
                task_list_view,
            ],
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.GREY_50,
    )