import flet as ft
from datetime import datetime
import time
import threading
from state.task_manager import TaskManager
from models.task import CATEGORIES, STATUSES

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

    # Add database lock to prevent recursive cursor usage
    db_lock = threading.Lock()
    
    search_query = "" # for search button

    # Current filter
    current_filter = "All"
    # Current sort option
    sort_option = "Date"
    
    # Track current tasks for responsive rebuild
    current_tasks = []
    
    # Get current date/time
    now = datetime.now()
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=48, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    date_text = ft.Text(now.strftime("%A, %B %d. %Y"), size=16, color=ft.Colors.GREY_600)

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
    total_time_text = ft.Text("0 h", size=18, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900)
    total_time_label = ft.Text("Total Est. Time (Due/Payable)", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600)
    
    # Status message display
    status_message_text = ft.Text("", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_500)
    
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
            if task.status != "Completed" and task.estimated_time:
                total += task.estimated_time
        return total
    
    def update_total_time():
        """Update the total estimated time display"""
        total = get_total_estimated_time()
        total_time_text.value = f"{total} h"
        if total_time_text.page is not None:
            total_time_text.update()

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
            current_filter = filter_status or "All"

            # Load all tasks from your TaskManager
            tasks = task_manager.get_user_tasks(user_id, include_deleted=False)

        # Apply status filtering
        if current_filter != "All":
            tasks = [t for t in tasks if t.status == current_filter]

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
        
        # Category badge color
        category_colors = {
            "quiz": ft.Colors.BLUE_300,
            "learning task (individual)": ft.Colors.GREEN_400,
            "learning task (group)": ft.Colors.GREEN_500,
            "project (individual)": ft.Colors.ORANGE_400,
            "project (group)": ft.Colors.ORANGE_500,
            "study/review": ft.Colors.PURPLE_400,
            "others": ft.Colors.GREY_500,
        }
        
        # Status badge color
        status_colors = {
            "Not Started": ft.Colors.GREY_400,
            "In Progress": ft.Colors.BLUE_400,
            "Completed": ft.Colors.GREEN_600,
        }
        
        # Check if overdue
        is_overdue = task.is_overdue()
        
        # Responsive: stack on mobile, single row on desktop
        is_mobile = page.window.width < 768
        
        if is_mobile:
            # Mobile: Stacked layout for readability
            return ft.Container(
                content=ft.Column(
                    controls=[
                        # First row: checkbox, source, spacer, edit/delete buttons
                        ft.Row(
                            controls=[
                                ft.Checkbox(
                                    value=(task.status == "Completed"),
                                    on_change=lambda e, t=task: toggle_complete(t, e.control.value),
                                    fill_color={
                                        ft.ControlState.DEFAULT: ft.Colors.GREY_400,
                                        ft.ControlState.SELECTED: ft.Colors.GREY_800,
                                    },
                                ),
                                ft.Text(
                                    task.source,
                                    size=11,
                                    color=ft.Colors.GREY_600,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Container(expand=True),  # Spacer to push buttons to right
                                ft.IconButton(
                                    icon=ft.Icons.PLAY_ARROW,
                                    icon_size=16,
                                    icon_color=ft.Colors.BLUE_600,
                                    on_click=lambda e, t=task: set_in_progress(t),
                                    tooltip="Mark in progress",
                                    visible=not task.is_deleted and task.status not in ("In Progress", "Completed"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    icon_size=16,
                                    icon_color=ft.Colors.GREY_700,
                                    on_click=lambda e, t=task: show_edit_dialog(t),
                                    tooltip="Edit task",
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_size=16,
                                    icon_color=ft.Colors.RED_600,
                                    on_click=lambda e, tid=task.id: confirm_delete(tid),
                                    tooltip="Delete task",
                                ),
                            ],
                            spacing=0,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        
                        # Second row: task title (full width)
                        ft.Text(
                            task.title,
                            size=15,
                            weight=ft.FontWeight.W_600 if task.status != "Completed" else ft.FontWeight.W_400,
                            color=ft.Colors.GREY_900 if task.status != "Completed" else ft.Colors.GREY_600,
                        ),
                        
                        # Third row: category, status, due date, time
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        task.category, 
                                        size=11, 
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=category_colors.get(task.category, ft.Colors.GREY_500),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=4,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        task.status, 
                                        size=11, 
                                        color=ft.Colors.WHITE if task.status != "Not Started" else ft.Colors.GREY_800,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=status_colors.get(task.status, ft.Colors.GREY_300),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=4,
                                ),
                                ft.Text(
                                    f"Due: {task.date_due}",
                                    size=12,
                                    color=ft.Colors.RED_600 if is_overdue else ft.Colors.GREY_600,
                                    weight=ft.FontWeight.W_500 if is_overdue else ft.FontWeight.W_400,
                                ),
                                ft.Text(
                                    f"Completed: {task.completed_at[:10]}" if task.completed_at else "",
                                    size=12,
                                    color=ft.Colors.GREEN_600,
                                    weight=ft.FontWeight.W_500,
                                    visible=task.status == "Completed" and task.completed_at is not None,
                                ),
                                ft.Text(
                                    f"Est: {task.estimated_time}h" if task.estimated_time else "—",
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                ) if task.estimated_time or task.actual_time else ft.Container(),
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
                        # Checkbox
                        ft.Checkbox(
                            value=(task.status == "Completed"),
                            on_change=lambda e, t=task: toggle_complete(t, e.control.value),
                            fill_color={
                                ft.ControlState.DEFAULT: ft.Colors.GREY_400,
                                ft.ControlState.SELECTED: ft.Colors.GREY_800,
                            },
                        ),
                        
                        # Source (before title)
                        ft.Text(
                            task.source,
                            size=12,
                            color=ft.Colors.GREY_700,
                            width=85,
                        ),
                        
                        # Task title
                        ft.Text(
                            task.title,
                            size=14,
                            weight=ft.FontWeight.W_600 if task.status != "Completed" else ft.FontWeight.W_400,
                            color=ft.Colors.GREY_900 if task.status != "Completed" else ft.Colors.GREY_600,
                            expand=True,
                        ),
                        
                        # Category badge
                        ft.Container(
                            content=ft.Text(
                                task.category, 
                                size=11, 
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_500,
                            ),
                            bgcolor=category_colors.get(task.category, ft.Colors.GREY_500),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=5,
                        ),
                        
                        # Due date
                        ft.Text(
                            f"Due: {task.date_due}",
                            size=12,
                            color=ft.Colors.RED_600 if is_overdue else ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500 if is_overdue else ft.FontWeight.W_400,
                            width=100,
                        ),
                        
                        # Status badge
                        ft.Container(
                            content=ft.Text(
                                task.status, 
                                size=11, 
                                color=ft.Colors.WHITE if task.status != "Not Started" else ft.Colors.GREY_800,
                                weight=ft.FontWeight.W_500,
                            ),
                            bgcolor=status_colors.get(task.status, ft.Colors.GREY_300),
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=5,
                        ),

                        # Start button to move to In Progress
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW,
                            icon_size=18,
                            icon_color=ft.Colors.BLUE_600,
                            on_click=lambda e, t=task: set_in_progress(t),
                            tooltip="Mark in progress",
                            visible=not task.is_deleted and task.status not in ("In Progress", "Completed"),
                        ),

                        # Time info
                        ft.Text(
                            f"Est: {task.estimated_time}h" if task.estimated_time else "—",
                            size=12,
                            color=ft.Colors.GREY_600,
                            width=70,
                        ) if task.estimated_time or task.actual_time else ft.Container(),
                        
                        # Completion date
                        ft.Text(
                            f"Done: {task.completed_at[:10]}" if task.completed_at else "",
                            size=12,
                            color=ft.Colors.GREEN_600,
                            weight=ft.FontWeight.W_500,
                            width=100,
                        ) if task.status == "Completed" and task.completed_at else ft.Container(),

                        # Edit button
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_size=18,
                            icon_color=ft.Colors.GREY_700,
                            on_click=lambda e, t=task: show_edit_dialog(t),
                            tooltip="Edit task",
                        ),
                        
                        # Delete button
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=18,
                            icon_color=ft.Colors.RED_600,
                            on_click=lambda e, tid=task.id: confirm_delete(tid),
                            tooltip="Delete task",
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
    
    def toggle_complete(task, is_complete):
        """Toggle task completion status with actual time prompt"""
        if is_complete:
            # Show dialog to enter actual time
            show_complete_dialog(task)
        else:
            # Unmark as complete
            task_manager.update_task(task.id, status="Not Started")
            load_tasks(current_filter)

    def set_in_progress(task):
        """Mark a task as in progress without opening the edit dialog"""
        if task.status == "Completed":
            return
        task_manager.update_task(task.id, status="In Progress")
        load_tasks(current_filter)

    def show_complete_dialog(task):
        """Show dialog to mark task complete and enter actual time"""
        
        actual_time_field = ft.TextField(
            label="Actual Time Spent (hours)",
            width=300,
            value=str(task.estimated_time) if task.estimated_time else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="How many hours did you spend?",
            border_color=ft.Colors.GREY_400,
        )
        
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)
        
        def save_completion(e):
            try:
                actual_time = float(actual_time_field.value) if actual_time_field.value else None
            except:
                error_text.value = "Please enter a valid number"
                page.update()
                return
            
            # Mark as complete
            task_manager.mark_complete(task.id, actual_time=actual_time)
            dialog.open = False
            load_tasks(current_filter)
            page.update()
        
        def skip_time(e):
            # Mark complete without time
            task_manager.mark_complete(task.id)
            dialog.open = False
            load_tasks(current_filter)
            page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Mark Task as Complete", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text(f"Task: {task.title}", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                    ft.Container(
                        height=1,
                        bgcolor=ft.Colors.GREY_300,
                        margin=ft.margin.symmetric(vertical=12),
                    ),
                    ft.Text("How much time did you actually spend?", size=13, color=ft.Colors.GREY_700),
                    ft.Container(height=4),
                    actual_time_field,
                    ft.Text(
                        f"Estimated: {task.estimated_time}h" if task.estimated_time else "",
                        size=12,
                        color=ft.Colors.GREY_600,
                        visible=task.estimated_time is not None,
                    ),
                    error_text,
                ],
                width=350,
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                ft.TextButton("Skip Time", on_click=skip_time),
                ft.ElevatedButton(
                    "Complete",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_completion,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
    def show_add_dialog(e):
        """Show dialog to add new task"""
        
        title_field = ft.TextField(label="Task Title *", width=400, border_color=ft.Colors.GREY_400)
        source_field = ft.TextField(
            label="Source (Course/Workplace/Personal) *",
            width=400,
            hint_text="e.g., CS 319, Starbucks, Personal",
            border_color=ft.Colors.GREY_400,
        )
        description_field = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400,
            border_color=ft.Colors.GREY_400,
        )
        category_dropdown = ft.Dropdown(
            label="Category *",
            width=400,
            options=[ft.dropdown.Option(cat) for cat in CATEGORIES],
            value="others",
            border_color=ft.Colors.GREY_400,
        )
        date_given_field = ft.TextField(
            label="Date Given (YYYY-MM-DD) *",
            width=190,
            value=datetime.now().strftime("%Y-%m-%d"),
            border_color=ft.Colors.GREY_400,
        )
        due_date_field = ft.TextField(
            label="Due Date (YYYY-MM-DD) *",
            width=190,
            hint_text="e.g., 2025-12-31",
            border_color=ft.Colors.GREY_400,
        )
        estimated_time_field = ft.TextField(
            label="Estimated Hours (optional)",
            width=190,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="e.g., 3.5",
            border_color=ft.Colors.GREY_400,
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=190,
            options=[ft.dropdown.Option(stat) for stat in STATUSES],
            value="Not Started",
            border_color=ft.Colors.GREY_400,
        )
        completed_at_field = ft.TextField(
            label="Completion Date (YYYY-MM-DD)",
            width=190,
            hint_text="e.g., 2025-12-09",
            border_color=ft.Colors.GREY_400,
            visible=False,  # Initially hidden
        )

        # Make completion date visible only when status is "Completed"
        def on_status_change(e):
            completed_at_field.visible = (e.control.value == "Completed")
            if e.control.value == "Completed" and not completed_at_field.value:
                completed_at_field.value = datetime.now().strftime("%Y-%m-%d")
            page.update()
        
        status_dropdown.on_change = on_status_change
        
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)
        
        def save_task(e):
            # Validate required fields
            if not title_field.value or not title_field.value.strip():
                error_text.value = "Task title is required"
                page.update()
                return
            
            if not source_field.value or not source_field.value.strip():
                error_text.value = "Source is required"
                page.update()
                return
            
            if not due_date_field.value or not due_date_field.value.strip():
                error_text.value = "Due date is required"
                page.update()
                return
            
            # Parse estimated time
            try:
                est_time = float(estimated_time_field.value) if estimated_time_field.value else None
            except:
                est_time = None

            # Parse completion date if provided
            completed_at = completed_at_field.value if completed_at_field.value else None
       
            
            # Create task
            success, msg, task = task_manager.create_task(
                user_id=user_id,
                title=title_field.value,
                source=source_field.value,
                category=category_dropdown.value,
                date_given=date_given_field.value,
                date_due=due_date_field.value,
                description=description_field.value,
                estimated_time=est_time,
                status=status_dropdown.value,
                completed_at=completed_at,
            )
            
            if success:
                dialog.open = False
                load_tasks(current_filter)
            else:
                error_text.value = msg
                page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Task", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text("* Required fields", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=4),
                    title_field,
                    source_field,
                    ft.Text(
                        "💡 Tip: Use consistent source names",
                        size=11,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    category_dropdown,
                    ft.Row([date_given_field, due_date_field], spacing=10),
                    description_field,
                    ft.Row([estimated_time_field, status_dropdown], spacing=10),
                    ft.Row([completed_at_field, error_text], spacing=10),
                ],
                width=450,
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                ft.ElevatedButton(
                    "Save Task",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_task,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
    def show_edit_dialog(task):
        """Show dialog to edit existing task"""
        
        title_field = ft.TextField(label="Task Title *", width=400, value=task.title, border_color=ft.Colors.GREY_400)
        source_field = ft.TextField(label="Source *", width=400, value=task.source, border_color=ft.Colors.GREY_400)
        description_field = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400,
            value=task.description or "",
            border_color=ft.Colors.GREY_400,
        )
        category_dropdown = ft.Dropdown(
            label="Category *",
            width=400,
            options=[ft.dropdown.Option(cat) for cat in CATEGORIES],
            value=task.category,
            border_color=ft.Colors.GREY_400,
        )
        date_given_field = ft.TextField(
            label="Date Given *",
            width=190,
            value=task.date_given,
            border_color=ft.Colors.GREY_400,
        )
        due_date_field = ft.TextField(
            label="Due Date *",
            width=190,
            value=task.date_due,
            border_color=ft.Colors.GREY_400,
        )
        estimated_time_field = ft.TextField(
            label="Estimated Hours",
            width=190,
            value=str(task.estimated_time) if task.estimated_time else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.Colors.GREY_400,
        )
        actual_time_field = ft.TextField(
            label="Actual Hours",
            width=190,
            value=str(task.actual_time) if task.actual_time else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.Colors.GREY_400,
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            width=190,
            options=[ft.dropdown.Option(stat) for stat in STATUSES],
            value=task.status,
            border_color=ft.Colors.GREY_400,
        )
        completed_at_field = ft.TextField(
            label="Completion Date (YYYY-MM-DD)",
            width=190,
            value=task.completed_at[:10] if task.completed_at else "",
            border_color=ft.Colors.GREY_400,
            visible=(task.status == "Completed")
        )
        
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)
        
        def save_changes(e):
            if not title_field.value or not title_field.value.strip():
                error_text.value = "Task title is required"
                page.update()
                return
            
            # Parse times
            try:
                est_time = float(estimated_time_field.value) if estimated_time_field.value else None
            except:
                est_time = None
            
            try:
                act_time = float(actual_time_field.value) if actual_time_field.value else None
            except:
                act_time = None
            
            # Parse completion date
            completed_at = completed_at_field.value if completed_at_field.value else None
        
            # Update task
            success, msg = task_manager.update_task(
                task.id,
                title=title_field.value,
                source=source_field.value,
                category=category_dropdown.value,
                date_given=date_given_field.value,
                date_due=due_date_field.value,
                description=description_field.value,
                estimated_time=est_time,
                actual_time=act_time,
                status=status_dropdown.value,
                completed_at=completed_at,
            )
            
            if success:
                dialog.open = False
                load_tasks(current_filter)
            else:
                error_text.value = msg
                page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Edit Task", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    title_field,
                    source_field,
                    category_dropdown,
                    ft.Row([date_given_field, due_date_field], spacing=10),
                    description_field,
                    ft.Row([estimated_time_field, actual_time_field], spacing=10),
                    ft.Row([status_dropdown, completed_at_field], spacing=10),
                    error_text,
                ],
                width=450,
                tight=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                ft.ElevatedButton(
                    "Save Changes",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_changes,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
    def confirm_delete(task_id):
        """Show confirmation dialog before deleting"""
        
        def delete_confirmed(e):
            success, msg = task_manager.delete_task(task_id)
            dialog.open = False
            load_tasks(current_filter)
            page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete", weight=ft.FontWeight.W_600),
            content=ft.Text("Are you sure you want to delete this task?", size=14),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    on_click=delete_confirmed,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
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
            create_filter_tab("All", "All"),
            create_filter_tab("Not Started", "Not Started"),
            create_filter_tab("In Progress", "In Progress"),
            create_filter_tab("Completed", "Completed"),
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
    load_tasks("All")
    
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
        filter_row_container.content = build_filter_row()
        rebuild_task_cards()
        update_total_time()
        update_status_message()
    
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
                            ft.Column(
                                controls=[
                                    total_time_label,
                                    total_time_text,
                                ],
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
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