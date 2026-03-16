"""
TYMATE Onboarding View - SIMPLIFIED
Visual wizard for time budget setup (without work questions)
"""

import flet as ft
from datetime import datetime, timedelta
from state.onboarding_manager import OnboardingManager
from managers.schedule_manager import ScheduleManager

def OnboardingPage(page: ft.Page, on_complete, session: dict):
    """
    Simplified onboarding wizard
    
    Args:
        page: Flet page
        on_complete: Callback function when onboarding is done
        session: Session data with user info
    """
    
    manager = OnboardingManager()
    schedule_manager = ScheduleManager()
    panel_bg = "#FFFFFF"
    soft_panel_bg = "#EDF2FA"
    border_color = "#B7C4D8"
    title_color = "#23211E"
    accent_color = "#6E7889"
    drop_shadow = ft.BoxShadow(
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
        offset=ft.Offset(0, 2),
    )
    window_width = page.window.width or 430
    content_width = max(320, min(760, window_width - 44))
    form_width = max(280, min(420, content_width - 40))

    user_id = session.get("user_id") if session else None
    if not user_id and session and session.get("user"):
        user_id = session["user"].id
    
    # Store user's answers
    onboarding_data = {
        "sleep_hours": 8.0,
        "wake_time": "07:00",  # Default 7:00 AM
        "has_work": False,
        "work_hours_per_week": 0.0,
        "work_days_per_week": 0,
    }
    
    current_step = ft.Container(
        content=ft.Text("Step 1 of 4", size=12, color=accent_color, weight=ft.FontWeight.W_700),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=soft_panel_bg,
        border=ft.border.all(1, border_color),
        border_radius=999,
    )

    primary_btn_style = ft.ButtonStyle(
        bgcolor=accent_color,
        color=ft.Colors.WHITE,
        side=ft.BorderSide(1, border_color),
    )
    
    # ==================== STEP 1: Sleep Hours ====================
    def build_step_1():
        selected_hours = ft.Text("8 hours", size=20, weight=ft.FontWeight.BOLD)
        
        def on_slider_change(e):
            hours = int(e.control.value)
            onboarding_data["sleep_hours"] = hours
            selected_hours.value = f"{hours} hours"
            page.update()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Let's set up your time budget", size=28, weight=ft.FontWeight.BOLD, color=title_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=10),
                    ft.Text("How many hours do you sleep per night?", size=16, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30),
                    selected_hours,
                    ft.Slider(
                        min=5,
                        max=12,
                        value=8,
                        divisions=7,
                        label="{value} hrs",
                        on_change=on_slider_change,
                        width=form_width,
                    ),
                    ft.Container(height=10),
                    ft.Text("(Most people need 7-9 hours)", size=12, color=accent_color),
                    ft.Container(height=40),
                    ft.ElevatedButton(
                        "Next",
                        on_click=lambda e: show_step(2),
                        style=primary_btn_style,
                        width=200,
                        height=50,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
            width=content_width,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
        )
    
    # ==================== STEP 2: Wake Time ====================
    def build_step_2():
        wake_hour = ft.Text("7:00 AM", size=20, weight=ft.FontWeight.BOLD)
        wake_time_field = ft.TextField(
            value="07:00",
            label="Wake Time",
            read_only=True,
            width=min(260, form_width - 30),
            border_color=border_color,
            bgcolor=panel_bg,
        )

        def format_12h(hour: int, minute: int):
            if hour == 0:
                return f"12:{minute:02d} AM"
            if hour < 12:
                return f"{hour}:{minute:02d} AM"
            if hour == 12:
                return f"12:{minute:02d} PM"
            return f"{hour - 12}:{minute:02d} PM"

        def apply_wake_time(hour: int, minute: int):
            onboarding_data["wake_time"] = f"{hour:02d}:{minute:02d}"
            wake_time_field.value = onboarding_data["wake_time"]
            wake_hour.value = format_12h(hour, minute)

        def open_wake_time_picker(_):
            current_text = (wake_time_field.value or "07:00").strip()
            init_hour = 7
            init_minute = 0
            try:
                current = datetime.strptime(current_text, "%H:%M")
                init_hour = current.hour
                init_minute = current.minute
            except ValueError:
                pass

            def on_change(e):
                if e.control.value is not None:
                    picked = e.control.value
                    apply_wake_time(picked.hour, picked.minute)
                    page.update()

            picker = ft.TimePicker(
                value=datetime(2000, 1, 1, init_hour, init_minute),
                on_change=on_change,
            )
            page.open(picker)

        apply_wake_time(7, 0)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("What time do you usually wake up?", size=28, weight=ft.FontWeight.BOLD, color=title_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=10),
                    ft.Text("This defines when your 'day' starts", size=14, color=accent_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30),
                    wake_hour,
                    ft.Row(
                        controls=[
                            wake_time_field,
                            ft.IconButton(
                                icon=ft.Icons.ACCESS_TIME,
                                tooltip="Pick wake time",
                                icon_color=ft.Colors.BLUE_GREY_600,
                                on_click=open_wake_time_picker,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Container(height=10),
                    ft.Text("(Your time budget resets at this time each day)", size=12, color=accent_color),
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                "← Back",
                                on_click=lambda e: show_step(1),
                                style=ft.ButtonStyle(color=title_color),
                            ),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Next",
                                on_click=lambda e: show_step(3),
                                style=primary_btn_style,
                                width=200,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
            width=content_width,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
        )
    
    # ==================== STEP 3: Weekly Schedule ====================
    def build_step_3():
        selected_day = {"value": datetime.now().weekday()}
        day_buttons = {}
        class_list = ft.Column(spacing=8)
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        active_day_text = ft.Text("", size=14, color=accent_color, weight=ft.FontWeight.W_600)

        def refresh_day_buttons():
            for day_index, button in day_buttons.items():
                is_active = day_index == selected_day["value"]
                button.bgcolor = accent_color if is_active else soft_panel_bg
                button.color = ft.Colors.WHITE if is_active else title_color
            active_day_text.value = f"Editing schedule for: {day_names[selected_day['value']]}"
            if active_day_text.page is not None:
                active_day_text.update()

        def load_classes():
            class_list.controls.clear()
            error_text.value = ""

            if not user_id:
                class_list.controls.append(
                    ft.Text("No user context available.", color=ft.Colors.RED_600, size=12)
                )
                page.update()
                return

            blocks = schedule_manager.get_classes_for_day(user_id, selected_day["value"])
            if not blocks:
                class_list.controls.append(
                    ft.Text("No class blocks for this day yet.", color=ft.Colors.GREY_600, size=12)
                )
            else:
                for block in blocks:
                    class_list.controls.append(
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                block.get("course_name") or "(No course name)",
                                                size=14,
                                                weight=ft.FontWeight.W_600,
                                                color=ft.Colors.GREY_900,
                                            ),
                                            ft.Text(
                                                f"{block['start_time']} - {block['end_time']}",
                                                size=12,
                                                color=ft.Colors.GREY_700,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_color=ft.Colors.RED_600,
                                        tooltip="Delete class block",
                                        on_click=lambda e, block_id=block["id"]: delete_block(block_id),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            border=ft.border.all(1, border_color),
                            border_radius=10,
                            padding=10,
                            bgcolor=panel_bg,
                        )
                    )

            page.update()

        def change_day(day_index: int):
            selected_day["value"] = day_index
            refresh_day_buttons()
            load_classes()

        def delete_block(block_id: int):
            ok, msg = schedule_manager.delete_class_block(block_id)
            if not ok:
                error_text.value = msg
            load_classes()

        def show_add_class_dialog(e):
            course_name_field = ft.TextField(label="Course Name", width=min(360, form_width), border_color=border_color, bgcolor=panel_bg)
            start_time_field = ft.TextField(
                label="Start Time (24-hour, HH:MM)",
                width=min(360, form_width),
                hint_text="e.g., 13:00 for 1:00 PM",
                read_only=True,
                border_color=border_color,
                bgcolor=panel_bg,
            )
            end_time_field = ft.TextField(
                label="End Time (24-hour, HH:MM)",
                width=min(360, form_width),
                hint_text="e.g., 14:30 for 2:30 PM",
                read_only=True,
                border_color=border_color,
                bgcolor=panel_bg,
            )
            dialog_error = ft.Text("", color=ft.Colors.RED_600, size=12)

            def open_time_picker_for(target_field: ft.TextField, fallback: str):
                init_hour = 0
                init_minute = 0
                try:
                    parsed = datetime.strptime((target_field.value or fallback).strip(), "%H:%M")
                    init_hour = parsed.hour
                    init_minute = parsed.minute
                except ValueError:
                    pass

                def on_change(change_event):
                    if change_event.control.value is not None:
                        picked = change_event.control.value
                        target_field.value = f"{picked.hour:02d}:{picked.minute:02d}"
                        page.update()

                picker = ft.TimePicker(
                    value=datetime(2000, 1, 1, init_hour, init_minute),
                    on_change=on_change,
                )
                page.open(picker)

            def save_class(event):
                if not user_id:
                    dialog_error.value = "No user context available"
                    page.update()
                    return

                try:
                    ok, msg, _ = schedule_manager.add_class_block(
                        user_id=user_id,
                        day_of_week=selected_day["value"],
                        start_time=start_time_field.value.strip(),
                        end_time=end_time_field.value.strip(),
                        course_name=course_name_field.value.strip() or None,
                    )
                except ValueError as exc:
                    dialog_error.value = str(exc)
                    page.update()
                    return

                if not ok:
                    dialog_error.value = msg
                    page.update()
                    return

                dialog.open = False
                load_classes()
                page.update()

            dialog = ft.AlertDialog(
                title=ft.Text(f"Add Class - {day_names[selected_day['value']]}", weight=ft.FontWeight.W_600),
                content=ft.Column(
                    controls=[
                        ft.Text("Use 24-hour time format (HH:MM)", size=12, color=ft.Colors.GREY_600),
                        course_name_field,
                        ft.Row(
                            controls=[
                                ft.Container(content=start_time_field, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.ACCESS_TIME,
                                    tooltip="Pick start time",
                                    icon_color=ft.Colors.BLUE_GREY_600,
                                    on_click=lambda event: open_time_picker_for(start_time_field, "08:00"),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            controls=[
                                ft.Container(content=end_time_field, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.ACCESS_TIME,
                                    tooltip="Pick end time",
                                    icon_color=ft.Colors.BLUE_GREY_600,
                                    on_click=lambda event: open_time_picker_for(end_time_field, "09:00"),
                                ),
                            ],
                            spacing=8,
                        ),
                        dialog_error,
                    ],
                    width=380,
                    tight=True,
                    spacing=10,
                ),
                actions=[
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda event: setattr(dialog, "open", False) or page.update(),
                        style=ft.ButtonStyle(color=title_color),
                    ),
                    ft.ElevatedButton(
                        "Save",
                        bgcolor=accent_color,
                        color=ft.Colors.WHITE,
                        on_click=save_class,
                    ),
                ],
            )

            page.open(dialog)
            page.update()

        day_tab_row = ft.Row(
            controls=[
                ft.TextButton(
                    day_labels[idx],
                    on_click=lambda e, day_index=idx: change_day(day_index),
                )
                for idx in range(7)
            ],
            spacing=6,
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        for idx, button in enumerate(day_tab_row.controls):
            day_buttons[idx] = button

        refresh_day_buttons()
        load_classes()

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Your Weekly Schedule", size=28, weight=ft.FontWeight.BOLD, color=title_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=6),
                    ft.Text("Add your class blocks for each day.", size=14, color=accent_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=16),
                    day_tab_row,
                    ft.Container(height=6),
                    active_day_text,
                    ft.Container(height=12),
                    ft.Container(
                        content=class_list,
                        width=form_width,
                        padding=12,
                        border=ft.border.all(1.5, border_color),
                        border_radius=10,
                        bgcolor=soft_panel_bg,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add Class",
                        on_click=show_add_class_dialog,
                        style=primary_btn_style,
                        width=180,
                        height=44,
                    ),
                    ft.Container(height=8),
                    error_text,
                    ft.Container(height=20),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: show_step(2)),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Next",
                                on_click=lambda e: show_step(4),
                                style=primary_btn_style,
                                width=200,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
            width=content_width,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
        )

    # ==================== STEP 4: Summary ====================
    def build_step_4():
        # Calculate budget
        budget = manager.calculate_time_budget(
            sleep_hours=onboarding_data["sleep_hours"],
            has_work=False,
            work_hours_per_week=0,
            work_days_per_week=0,
            wake_time=onboarding_data["wake_time"],
        )
        
        # Add error message display
        error_msg = ft.Text("", color=ft.Colors.RED_600, size=14)

        def finish_onboarding(e):
            # Get user_id from session
            user_id = session.get("user_id")
            
            if not user_id:
                error_msg.value = "Error: No user logged in"
                page.update()
                return
            
            # Calculate the study goal
            study_goal = budget["free_hours_per_day"] * 0.35
            
            # ACTUALLY SAVE TO DATABASE
            success = manager.save_user_profile(
                user_id=user_id,
                sleep_hours=onboarding_data["sleep_hours"],
                wake_time=onboarding_data["wake_time"],
                has_work=False,
                work_hours_per_week=0,
                work_days_per_week=0,
                study_goal_hours_per_day=study_goal
            )
            
            if success:
                # Mark as completed in session
                session["onboarding_completed"] = True
                # Call the callback to redirect
                on_complete(onboarding_data, budget)
            else:
                error_msg.value = "Error saving profile. Please try again."
                page.update()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Your Time Budget", size=28, weight=ft.FontWeight.BOLD, color=title_color, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=30),
                    
                    # Budget breakdown card
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("📊 Daily Breakdown", size=18, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                ft.Row(
                                    controls=[
                                        ft.Text("Total:", size=14),
                                        ft.Text(f"24 hours", size=14, weight=ft.FontWeight.BOLD),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text("Sleep:", size=14),
                                        ft.Text(f"{budget['sleep_hours_per_day']} hours", size=14),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Divider(),
                                ft.Row(
                                    controls=[
                                        ft.Text("Free Time:", size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            f"{budget['free_hours_per_day']:.1f} hours",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN_600,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                        ),
                        bgcolor=soft_panel_bg,
                        border=ft.border.all(1.5, border_color),
                        border_radius=10,
                        padding=20,
                        width=form_width,
                    ),
                    
                    ft.Container(height=20),
                    error_msg,
                    ft.Text("You can adjust this later in Settings!", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                "← Back",
                                on_click=lambda e: show_step(3),
                                style=ft.ButtonStyle(color=title_color),
                            ),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Start Using TYMATE",
                                on_click=finish_onboarding,
                                style=ft.ButtonStyle(
                                    bgcolor=accent_color,
                                    color=ft.Colors.WHITE,
                                    side=ft.BorderSide(1, border_color),
                                ),
                                width=250,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
            width=content_width,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
        )
    
    # ==================== Step Navigation ====================
    step_content = ft.Container()
    
    def show_step(step_num):
        current_step.content.value = f"Step {step_num} of 4"
        
        if step_num == 1:
            step_content.content = build_step_1()
        elif step_num == 2:
            step_content.content = build_step_2()
        elif step_num == 3:
            step_content.content = build_step_3()
        elif step_num == 4:
            step_content.content = build_step_4()
        
        page.update()
    
    # Start with step 1
    show_step(1)
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(height=16),
                current_step,
                ft.Container(height=20),
                step_content,
                ft.Container(height=24),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(horizontal=16),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#DDE9FB", "#FFFFFF"],
        ),
    )