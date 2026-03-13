import flet as ft
from datetime import datetime
from models.task import CATEGORIES, STATUSES
from state.task_manager import TaskManager
from state.session_manager import SessionManager
from utils.time_helpers import format_minutes, parse_time_input


def TaskDetailsPage(page: ft.Page, session: dict = None):
    """Dedicated task details view with richer layout and navigation back to tasks."""

    if not session or not session.get("user"):
        return ft.Container(
            content=ft.Text("Please login first", size=20),
            alignment=ft.alignment.center,
            expand=True,
        )

    user_id = session["user"].id
    create_mode = bool(session.get("task_details_create_mode", False))
    task_id = session.get("selected_task_id")
    task_manager = TaskManager()
    session_manager = SessionManager()
    edit_mode = create_mode or bool(session.get("task_details_edit_mode", False))

    def go_to(route: str):
        page.route = route
        route_change = session.get("route_change")
        if callable(route_change):
            route_change(route)

    def go_back(e=None):
        session["task_details_edit_mode"] = False
        session["task_details_create_mode"] = False
        go_to("/tasks")

    def rerender_current_page():
        route_change = session.get("route_change")
        if callable(route_change):
            route_change(page.route)
        else:
            page.update()

    def set_edit_mode(value: bool):
        session["task_details_edit_mode"] = value
        rerender_current_page()

    def show_notice(message: str, color: str = ft.Colors.GREEN_50, text_color: str = ft.Colors.GREEN_900):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=text_color),
            bgcolor=color,
        )
        page.snack_bar.open = True
        page.update()

    def format_timestamp(value: str | None) -> str:
        if not value:
            return "-"
        try:
            return datetime.fromisoformat(value).strftime("%b %d, %Y %I:%M %p")
        except ValueError:
            return value.replace("T", " ")[:16]

    def info_row(label: str, value: str):
        return ft.Row(
            controls=[
                ft.Text(label, size=12, color=ft.Colors.GREY_600, width=130),
                ft.Text(value, size=13, color=ft.Colors.GREY_900, weight=ft.FontWeight.W_600, expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def stat_card(label: str, value: str, accent: str, subtitle: str = ""):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                    ft.Text(value, size=24, color=ft.Colors.GREY_900, weight=ft.FontWeight.W_700),
                    ft.Text(subtitle, size=11, color=accent, visible=bool(subtitle)),
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=12,
            padding=16,
            expand=True,
        )

    def section_card(title: str, content, expand: bool = False):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=14, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_800),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_200),
                    content,
                ],
                spacing=12,
                expand=expand,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=14,
            padding=18,
            expand=expand,
        )

    def labeled_field(label: str, control: ft.Control):
        return ft.Column(
            controls=[
                ft.Text(label, size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                control,
            ],
            spacing=6,
        )

    def build_readonly_field(value: str):
        return ft.TextField(
            value=value,
            read_only=True,
            dense=True,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=14),
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

    task = None
    if not create_mode and not task_id:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("No task selected", size=26, weight=ft.FontWeight.W_700),
                    ft.Text("Choose a task from My Tasks to open its details page.", color=ft.Colors.GREY_700),
                    ft.ElevatedButton("Back to Tasks", on_click=go_back),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    if not create_mode:
        task = task_manager.get_task(task_id, include_deleted=True)

    if not create_mode and not task:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Task not found", size=26, weight=ft.FontWeight.W_700),
                    ft.Text("The selected task may have been removed.", color=ft.Colors.GREY_700),
                    ft.ElevatedButton("Back to Tasks", on_click=go_back),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    sessions = session_manager.get_sessions_for_task(task.id) if task and task.id else []
    events = task_manager.get_task_events(task.id) if task and task.id else []
    actual_minutes = task.compute_actual_minutes(sessions) if task else 0
    estimated_minutes = (task.estimated_time or 0) if task else 0
    variance_minutes = actual_minutes - estimated_minutes if task and task.estimated_time is not None and actual_minutes else None
    due_summary = "No due date"
    due_color = ft.Colors.GREY_700
    if task and task.date_due:
        due_days = task.days_until_due()
        if task.status == "Completed":
            due_summary = "Completed"
            due_color = ft.Colors.GREEN_700
        elif due_days is not None and due_days < 0:
            due_summary = f"Overdue by {abs(due_days)} day(s)"
            due_color = ft.Colors.RED_700
        elif due_days == 0:
            due_summary = "Due today"
            due_color = ft.Colors.ORANGE_700
        elif due_days is not None:
            due_summary = f"Due in {due_days} day(s)"
            due_color = ft.Colors.BLUE_700

    recurrence_summary = "Does not repeat"
    if task and task.is_recurring and task.recurrence_type:
        recurrence_summary = f"Every {task.recurrence_interval} {task.recurrence_type}"
        if task.recurrence_interval == 1:
            recurrence_summary = f"Every {task.recurrence_type}"
        if task.recurrence_until:
            recurrence_summary += f" until {task.recurrence_until}"

    status_colors = {
        "Not Started": ft.Colors.GREY_700,
        "In Progress": ft.Colors.BLUE_700,
        "Completed": ft.Colors.GREEN_700,
    }

    title_field = ft.TextField(
        value=task.title if task else "",
        label="Task Name *",
        border_color=ft.Colors.GREY_400,
        text_size=20,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=16),
    )
    source_field = ft.TextField(value=task.source if task else "", border_color=ft.Colors.GREY_400, dense=True)
    category_dropdown = ft.Dropdown(
        value=task.category if task else "others",
        options=[ft.dropdown.Option(category) for category in CATEGORIES],
        border_color=ft.Colors.GREY_400,
        dense=True,
    )
    status_dropdown = ft.Dropdown(
        value=task.status if task else "Not Started",
        options=[ft.dropdown.Option(status) for status in STATUSES],
        border_color=ft.Colors.GREY_400,
        dense=True,
    )
    date_given_field = ft.TextField(value=task.date_given if task else datetime.now().strftime("%Y-%m-%d"), border_color=ft.Colors.GREY_400, dense=True)
    due_date_field = ft.TextField(value=(task.date_due or "") if task else "", border_color=ft.Colors.GREY_400, dense=True, hint_text="YYYY-MM-DD")
    estimated_time_field = ft.TextField(
        value=str(task.estimated_time) if task and task.estimated_time is not None else "",
        border_color=ft.Colors.GREY_400,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="Minutes",
    )
    recurrence_dropdown = ft.Dropdown(
        value=task.recurrence_type if task and task.is_recurring and task.recurrence_type else "none",
        options=[
            ft.dropdown.Option("none", "No repeat"),
            ft.dropdown.Option("daily", "Daily"),
            ft.dropdown.Option("weekly", "Weekly"),
            ft.dropdown.Option("monthly", "Monthly"),
        ],
        border_color=ft.Colors.GREY_400,
        dense=True,
    )
    recurrence_interval_field = ft.TextField(
        value=str(task.recurrence_interval or 1) if task else "1",
        border_color=ft.Colors.GREY_400,
        dense=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="1",
        visible=task.is_recurring if task else False,
    )
    recurrence_until_field = ft.TextField(
        value=(task.recurrence_until or "") if task else "",
        border_color=ft.Colors.GREY_400,
        dense=True,
        hint_text="YYYY-MM-DD",
        visible=task.is_recurring if task else False,
    )
    description_field = ft.TextField(
        value=(task.description or "") if task else "",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_color=ft.Colors.GREY_400,
    )
    form_error_text = ft.Text("", color=ft.Colors.RED_700, size=12)

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

    def on_repeat_change(e):
        is_repeating = e.control.value != "none"
        recurrence_interval_field.visible = is_repeating
        recurrence_until_field.visible = is_repeating
        if not is_repeating:
            recurrence_interval_field.value = "1"
            recurrence_until_field.value = ""
        page.update()

    recurrence_dropdown.on_change = on_repeat_change

    def save_inline_changes(e=None):
        title = (title_field.value or "").strip()
        source = (source_field.value or "").strip()
        date_given = (date_given_field.value or "").strip()
        due_date = (due_date_field.value or "").strip() or None
        description = (description_field.value or "").strip() or None

        if not title:
            form_error_text.value = "Task title is required"
            page.update()
            return
        if not source:
            form_error_text.value = "Source is required"
            page.update()
            return
        if not date_given:
            form_error_text.value = "Date Given is required"
            page.update()
            return

        try:
            estimated_time = int(estimated_time_field.value) if (estimated_time_field.value or "").strip() else None
        except ValueError:
            form_error_text.value = "Estimated minutes must be a whole number"
            page.update()
            return

        try:
            recurrence_interval = int((recurrence_interval_field.value or "1").strip())
        except ValueError:
            form_error_text.value = "Repeat interval must be a whole number"
            page.update()
            return

        if create_mode:
            success, message, created_task = task_manager.create_task(
                user_id=user_id,
                title=title,
                source=source,
                category=category_dropdown.value,
                status=status_dropdown.value,
                date_given=date_given,
                date_due=due_date,
                description=description,
                estimated_time=estimated_time,
                is_recurring=recurrence_dropdown.value != "none",
                recurrence_type=recurrence_dropdown.value if recurrence_dropdown.value != "none" else None,
                recurrence_interval=recurrence_interval,
                recurrence_until=(recurrence_until_field.value or "").strip() or None,
                completed_at=None,
            )
            if not success:
                form_error_text.value = message
                page.update()
                return

            form_error_text.value = ""
            session["task_details_create_mode"] = False
            session["task_details_edit_mode"] = False
            if created_task and created_task.id is not None:
                session["selected_task_id"] = created_task.id
                go_to(f"/tasks/{created_task.id}")
            else:
                go_to("/tasks")
            show_notice(message or "Task created successfully")
            return

        success, message = task_manager.update_task(
            task.id,
            title=title,
            source=source,
            category=category_dropdown.value,
            status=status_dropdown.value,
            date_given=date_given,
            date_due=due_date,
            description=description,
            estimated_time=estimated_time,
            is_recurring=recurrence_dropdown.value != "none",
            recurrence_type=recurrence_dropdown.value if recurrence_dropdown.value != "none" else None,
            recurrence_interval=recurrence_interval,
            recurrence_until=(recurrence_until_field.value or "").strip() or None,
        )
        if not success:
            form_error_text.value = message
            page.update()
            return

        form_error_text.value = ""
        session["task_details_edit_mode"] = False
        rerender_current_page()
        show_notice(message or "Task updated successfully")

    def mark_in_progress(e=None):
        if create_mode or not task or task.status == "Completed":
            return

        date_field = ft.TextField(
            value=datetime.now().strftime("%Y-%m-%d"),
            border_color=ft.Colors.GREY_400,
            dense=True,
        )

        def confirm_start(_):
            event_date = (date_field.value or "").strip() or None
            dialog.open = False
            page.update()
            success, message = task_manager.update_task(task.id, status="In Progress", event_date=event_date)
            if success:
                session["task_details_edit_mode"] = False
                session["task_details_create_mode"] = False
                go_to(f"/tasks/{task.id}")
                show_notice(message or "Task moved to In Progress")
            else:
                show_notice(message, color=ft.Colors.RED_50, text_color=ft.Colors.RED_900)

        dialog = ft.AlertDialog(
            title=ft.Text("Start Task", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text("When did you start this task?", size=13, color=ft.Colors.GREY_700),
                    build_date_input(date_field, "Date Started"),
                ],
                width=320,
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(
                    "Start Task",
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    on_click=confirm_start,
                ),
            ],
        )
        page.open(dialog)
        page.update()

    def mark_not_started(e=None):
        if create_mode or not task:
            return

        date_field = ft.TextField(
            value=datetime.now().strftime("%Y-%m-%d"),
            border_color=ft.Colors.GREY_400,
            dense=True,
        )

        def confirm_reset(_):
            event_date = (date_field.value or "").strip() or None
            dialog.open = False
            page.update()
            success, message = task_manager.update_task(task.id, status="Not Started", completed_at=None, event_date=event_date)
            if success:
                session["task_details_edit_mode"] = False
                session["task_details_create_mode"] = False
                go_to(f"/tasks/{task.id}")
                show_notice(message or "Task moved back to Not Started")
            else:
                show_notice(message, color=ft.Colors.RED_50, text_color=ft.Colors.RED_900)

        dialog = ft.AlertDialog(
            title=ft.Text("Reset to Not Started", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text("When are you recording this status change?", size=13, color=ft.Colors.GREY_700),
                    build_date_input(date_field, "Date"),
                ],
                width=320,
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(
                    "Reset Status",
                    bgcolor=ft.Colors.GREY_700,
                    color=ft.Colors.WHITE,
                    on_click=confirm_reset,
                ),
            ],
        )
        page.open(dialog)
        page.update()

    def confirm_delete(e=None):
        if create_mode or not task:
            return

        def delete_confirmed(_):
            success, message = task_manager.delete_task(task.id)
            dialog.open = False
            if success:
                session["task_details_edit_mode"] = False
                go_to("/tasks")
                show_notice(message or "Task deleted")
            else:
                show_notice(message, color=ft.Colors.RED_50, text_color=ft.Colors.RED_900)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete", weight=ft.FontWeight.W_600),
            content=ft.Text("Are you sure you want to delete this task?", size=14),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
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

    def show_complete_dialog(e=None):
        if create_mode or not task:
            return

        existing_minutes = session_manager.get_total_minutes_for_task(task.id) if task.id is not None else 0
        completed_at_field = ft.TextField(
            value=datetime.now().strftime("%Y-%m-%d"),
            border_color=ft.Colors.GREY_400,
            dense=True,
        )
        time_spent_field = ft.TextField(
            label="Additional time spent (optional)",
            width=300,
            hint_text="e.g., 90m, 2h 30m, 1.5h",
            border_color=ft.Colors.GREY_400,
        )
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def complete_task(duration_minutes=None):
            event_date = (completed_at_field.value or "").strip() or None
            success, message = task_manager.mark_complete(task.id, duration_minutes=duration_minutes, event_date=event_date)
            if success:
                dialog.open = False
                session["task_details_edit_mode"] = False
                session["task_details_create_mode"] = False
                go_to(f"/tasks/{task.id}")
                show_notice(message or "Task marked complete")
            else:
                error_text.value = message
                page.update()

        def save_completion(_):
            raw_input = (time_spent_field.value or "").strip()
            actual_minutes = parse_time_input(raw_input) if raw_input else None
            if raw_input and actual_minutes is None:
                error_text.value = "Please enter a valid time (e.g., 90m, 2h 30m, 1.5h)"
                page.update()
                return
            complete_task(actual_minutes)

        dialog = ft.AlertDialog(
            title=ft.Text("Mark Task as Complete", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    ft.Text(f"Task: {task.title}", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.symmetric(vertical=12)),
                    ft.Text("When did you complete this task?", size=13, color=ft.Colors.GREY_700),
                    build_date_input(completed_at_field, "Date Completed"),
                    ft.Container(height=4),
                    ft.Text("How much time did you actually spend?", size=13, color=ft.Colors.GREY_700),
                    ft.Text(
                        f"Already logged from sessions: {format_minutes(existing_minutes)}",
                        size=12,
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Text(
                        "Enter only additional time not yet logged (optional).",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                    time_spent_field,
                    ft.Text(
                        f"Estimated: {format_minutes(task.estimated_time)}" if task.estimated_time is not None else "",
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
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.TextButton("Skip Time", on_click=lambda e: complete_task()),
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

    session_cards = []
    if sessions:
        for logged_session in reversed(sessions):
            session_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        format_minutes(logged_session.duration_minutes),
                                        size=15,
                                        weight=ft.FontWeight.W_700,
                                        color=ft.Colors.GREY_900,
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        format_timestamp(logged_session.logged_at),
                                        size=11,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                            ),
                            ft.Text(
                                logged_session.notes or "No session notes.",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        spacing=6,
                    ),
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    border_radius=10,
                    padding=14,
                )
            )
    else:
        session_cards.append(ft.Text("No sessions logged yet.", size=13, color=ft.Colors.GREY_600))

    timeline_items = []
    if events:
        for event in events:
            timeline_items.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=12,
                            height=12,
                            border_radius=6,
                            bgcolor=ft.Colors.ORANGE_400,
                            margin=ft.margin.only(top=5),
                        ),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            event.get("message") or event.get("event_type", "Update"),
                                            size=13,
                                            weight=ft.FontWeight.W_700,
                                            color=ft.Colors.GREY_900,
                                            expand=True,
                                        ),
                                        ft.Text(
                                            format_timestamp(event.get("created_at")),
                                            size=11,
                                            color=ft.Colors.GREY_600,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(
                                    event.get("event_type", "EVENT").replace("_", " ").title(),
                                    size=11,
                                    color=ft.Colors.BLUE_GREY_600,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            )
    else:
        timeline_items.append(ft.Text("No lifecycle events yet.", size=13, color=ft.Colors.GREY_600))

    overview_card = section_card(
        "Task Overview",
        ft.Column(
            controls=[
                labeled_field("Source", source_field) if edit_mode else labeled_field("Source", build_readonly_field(task.source if task else "-")),
                labeled_field("Category", category_dropdown) if edit_mode else labeled_field("Category", build_readonly_field(task.category.title() if task else "-")),
                labeled_field("Status", status_dropdown) if edit_mode else labeled_field("Status", build_readonly_field(task.status if task else "Not Started")),
                labeled_field(
                    "Date Given",
                    build_date_input(date_given_field, "Date Given"),
                ) if edit_mode else labeled_field("Date Given", build_readonly_field(task.date_given if task else date_given_field.value)),
                labeled_field(
                    "Due Date",
                    build_date_input(due_date_field, "Due Date"),
                ) if edit_mode else labeled_field("Due Date", build_readonly_field((task.date_due or "No due date") if task else "No due date")),
                labeled_field("Completed At", build_readonly_field(format_timestamp(task.completed_at if task else None))),
            ],
            spacing=10,
        ),
    )

    planning_card = section_card(
        "Planning",
        ft.Column(
            controls=[
                labeled_field("Estimated Minutes", estimated_time_field) if edit_mode else labeled_field("Estimated Minutes", build_readonly_field(format_minutes(task.estimated_time) if task and task.estimated_time else "Not set")),
                labeled_field("Actual Time", build_readonly_field(format_minutes(actual_minutes) if actual_minutes else "No time logged")),
                ft.Column(
                    controls=[
                        labeled_field("Repeat", recurrence_dropdown),
                        ft.Row(
                            controls=[
                                labeled_field("Every", recurrence_interval_field),
                                labeled_field("Repeat Until", recurrence_until_field),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                    ],
                    spacing=10,
                ) if edit_mode else labeled_field("Recurring", build_readonly_field(recurrence_summary)),
                labeled_field("Created", build_readonly_field(format_timestamp(task.created_at if task else None))),
                labeled_field("Last Updated", build_readonly_field(format_timestamp(task.updated_at if task else None))),
            ],
            spacing=10,
        ),
    )

    notes_card = section_card(
        "Notes",
        ft.Column(
            controls=[
                description_field if edit_mode else ft.Text(task.description or "No task notes added yet.", size=14, color=ft.Colors.GREY_700),
            ],
            spacing=10,
        ),
    )

    if page.window.width < 980:
        overview_layout = ft.Column(
            controls=[overview_card, planning_card, notes_card],
            spacing=16,
        )
    else:
        overview_layout = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(content=overview_card, expand=True),
                        ft.Container(content=planning_card, expand=True),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                notes_card,
            ],
            spacing=16,
        )

    details_sections = [section_card("Overview", overview_layout)]
    if not create_mode:
        details_sections.append(
            section_card(
                f"Sessions ({len(sessions)})",
                ft.Column(controls=session_cards, spacing=10),
            )
        )
        details_sections.append(
            section_card(
                f"Timeline ({len(events)})",
                ft.Column(controls=timeline_items, spacing=14),
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.TextButton("Back to Tasks", icon=ft.Icons.ARROW_BACK, on_click=go_back),
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "Delete",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=confirm_delete,
                            visible=not edit_mode and not create_mode,
                            style=ft.ButtonStyle(color=ft.Colors.RED_700),
                        ),
                        ft.OutlinedButton(
                            "Mark Not Started",
                            on_click=mark_not_started,
                            visible=not edit_mode and not create_mode and task is not None and task.status == "Completed",
                        ),
                        ft.OutlinedButton(
                            "Start Task",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=mark_in_progress,
                            visible=not edit_mode and not create_mode and task is not None and task.status not in ("In Progress", "Completed"),
                        ),
                        ft.ElevatedButton(
                            "Complete Task",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            on_click=show_complete_dialog,
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                            visible=not edit_mode and not create_mode and task is not None and task.status != "Completed",
                        ),
                        ft.TextButton(
                            "Cancel Create" if create_mode else "Cancel Edit",
                            visible=edit_mode,
                            on_click=go_back if create_mode else (lambda e: set_edit_mode(False)),
                        ),
                        ft.ElevatedButton(
                            "Apply Changes",
                            icon=ft.Icons.CHECK,
                            on_click=save_inline_changes,
                            bgcolor=ft.Colors.ORANGE_400,
                            color=ft.Colors.WHITE,
                            visible=edit_mode and not create_mode,
                        ),
                        ft.ElevatedButton(
                            "Create Task",
                            icon=ft.Icons.ADD_TASK,
                            on_click=save_inline_changes,
                            bgcolor=ft.Colors.ORANGE_400,
                            color=ft.Colors.WHITE,
                            visible=create_mode,
                        ),
                        ft.OutlinedButton(
                            "Edit Task",
                            icon=ft.Icons.EDIT_OUTLINED,
                            on_click=lambda e: set_edit_mode(True),
                            visible=not edit_mode and not create_mode,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=6),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Column(
                                    controls=[
                                        title_field,
                                        form_error_text,
                                    ],
                                    spacing=4,
                                ) if edit_mode else ft.Text(task.title if task else "New Task", size=30, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(task.source if task else "Draft", size=12, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_600),
                                            bgcolor=ft.Colors.GREY_100,
                                            border_radius=999,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                            border=ft.border.all(1, ft.Colors.GREY_300),
                                            visible=not edit_mode and not create_mode,
                                        ),
                                        ft.Container(
                                            content=ft.Text(task.category if task else "others", size=12, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_600),
                                            bgcolor=ft.Colors.GREY_100,
                                            border_radius=999,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                            border=ft.border.all(1, ft.Colors.GREY_300),
                                            visible=not edit_mode and not create_mode,
                                        ),
                                        ft.Container(
                                            content=ft.Text(task.status if task else "Not Started", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                            bgcolor=status_colors.get(task.status if task else "Not Started", ft.Colors.GREY_700),
                                            border_radius=999,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                            visible=not edit_mode and not create_mode,
                                        ),
                                    ],
                                    wrap=True,
                                    spacing=8,
                                ),
                            ],
                            spacing=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Due Status", size=10, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                                    ft.Text(due_summary, size=14, color=due_color, weight=ft.FontWeight.W_700),
                                    ft.Text((task.date_due if task else due_date_field.value) or "", size=11, color=ft.Colors.GREY_700),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                            padding=12,
                            border_radius=10,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        stat_card("Estimated", format_minutes(task.estimated_time) if task and task.estimated_time else "Not set", ft.Colors.BLUE_700),
                        stat_card("Actual", format_minutes(actual_minutes) if actual_minutes else "No logs", ft.Colors.GREEN_700),
                        stat_card(
                            "Variance",
                            format_minutes(abs(variance_minutes)) if variance_minutes is not None else "-",
                            ft.Colors.ORANGE_700,
                            "Over estimate" if variance_minutes is not None and variance_minutes < 0 else "Over actual" if variance_minutes is not None and variance_minutes > 0 else "",
                        ),
                        stat_card("Sessions", str(len(sessions)), ft.Colors.BLUE_GREY_700),
                    ],
                    spacing=14,
                    wrap=page.window.width < 980,
                    visible=not create_mode,
                ),
                ft.Container(height=10),
                ft.Column(controls=details_sections, spacing=14),
            ],
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.GREY_50,
    )