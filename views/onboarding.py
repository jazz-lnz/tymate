"""
TYMATE Onboarding View - SIMPLIFIED
Visual wizard for time budget setup (without work questions)
"""

import flet as ft
from datetime import datetime
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
    
    current_step = ft.Text("Step 1 of 4", size=12, color=ft.Colors.GREY_600)
    
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
                    ft.Text("Let's set up your time budget", size=28, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text("How many hours do you sleep per night?", size=16),
                    ft.Container(height=30),
                    selected_hours,
                    ft.Slider(
                        min=5,
                        max=12,
                        value=8,
                        divisions=7,
                        label="{value} hrs",
                        on_change=on_slider_change,
                        width=400,
                    ),
                    ft.Container(height=10),
                    ft.Text("(Most people need 7-9 hours)", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=40),
                    ft.ElevatedButton(
                        "Next",
                        on_click=lambda e: show_step(2),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_400,
                            color=ft.Colors.WHITE,
                        ),
                        width=200,
                        height=50,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    
    # ==================== STEP 2: Wake Time ====================
    def build_step_2():
        wake_hour = ft.Text("7:00 AM", size=20, weight=ft.FontWeight.BOLD)
        
        def on_hour_change(e):
            hour = int(e.control.value)
            onboarding_data["wake_time"] = f"{hour:02d}:00"
            
            # Format for display
            if hour == 0:
                display = "12:00 AM"
            elif hour < 12:
                display = f"{hour}:00 AM"
            elif hour == 12:
                display = "12:00 PM"
            else:
                display = f"{hour-12}:00 PM"
            
            wake_hour.value = display
            page.update()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("What time do you usually wake up?", size=28, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text("This defines when your 'day' starts", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=30),
                    wake_hour,
                    ft.Slider(
                        min=0,
                        max=23,
                        value=7,
                        divisions=23,
                        label="{value}:00",
                        on_change=on_hour_change,
                        width=400,
                    ),
                    ft.Container(height=10),
                    ft.Text("(Your time budget resets at this time each day)", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: show_step(1)),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Next",
                                on_click=lambda e: show_step(3),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_400,
                                    color=ft.Colors.WHITE,
                                ),
                                width=200,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    
    # ==================== STEP 3: Weekly Schedule ====================
    def build_step_3():
        selected_day = {"value": datetime.now().weekday()}
        day_buttons = {}
        class_list = ft.Column(spacing=8)
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        active_day_text = ft.Text("", size=14, color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_600)

        def refresh_day_buttons():
            for day_index, button in day_buttons.items():
                is_active = day_index == selected_day["value"]
                button.bgcolor = ft.Colors.BLUE_400 if is_active else ft.Colors.GREY_200
                button.color = ft.Colors.WHITE if is_active else ft.Colors.GREY_800
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
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=8,
                            padding=10,
                            bgcolor=ft.Colors.WHITE,
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
            course_name_field = ft.TextField(label="Course Name", width=360, border_color=ft.Colors.GREY_400)
            start_time_field = ft.TextField(
                label="Start Time (24-hour, HH:MM)",
                width=360,
                hint_text="e.g., 13:00 for 1:00 PM",
                border_color=ft.Colors.GREY_400,
            )
            end_time_field = ft.TextField(
                label="End Time (24-hour, HH:MM)",
                width=360,
                hint_text="e.g., 14:30 for 2:30 PM",
                border_color=ft.Colors.GREY_400,
            )
            dialog_error = ft.Text("", color=ft.Colors.RED_600, size=12)

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
                        start_time_field,
                        end_time_field,
                        dialog_error,
                    ],
                    width=380,
                    tight=True,
                    spacing=10,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda event: setattr(dialog, "open", False) or page.update()),
                    ft.ElevatedButton(
                        "Save",
                        bgcolor=ft.Colors.BLUE_400,
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
                    ft.Text("Your Weekly Schedule", size=28, weight=ft.FontWeight.BOLD),
                    ft.Container(height=6),
                    ft.Text("Add your class blocks for each day.", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=16),
                    day_tab_row,
                    ft.Container(height=6),
                    active_day_text,
                    ft.Container(height=12),
                    ft.Container(
                        content=class_list,
                        width=420,
                        padding=12,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8,
                        bgcolor=ft.Colors.GREY_50,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Add Class",
                        on_click=show_add_class_dialog,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_400,
                            color=ft.Colors.WHITE,
                        ),
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
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_400,
                                    color=ft.Colors.WHITE,
                                ),
                                width=200,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
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
        
        # Recommended study goal
        study_goal = budget["free_hours_per_day"] * 0.35
        
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
                    ft.Text("Your Time Budget", size=28, weight=ft.FontWeight.BOLD),
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
                        bgcolor=ft.Colors.BLUE_50,
                        border=ft.border.all(2, ft.Colors.BLUE_200),
                        border_radius=10,
                        padding=20,
                        width=400,
                    ),
                    
                    ft.Container(height=30),
                    
                    # Recommendation
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("💡 Recommended Study Goal", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(height=10),
                                ft.Text(
                                    f"{study_goal:.1f} hours per day",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_600,
                                ),
                                ft.Text(
                                    "(About 35% of your free time)",
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.AMBER_50,
                        border_radius=10,
                        padding=20,
                        width=400,
                    ),
                    
                    ft.Container(height=30),
                    error_msg,
                    ft.Text("You can adjust this later in Settings!", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: show_step(3)),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Start Using TYMATE",
                                on_click=finish_onboarding,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_600,
                                    color=ft.Colors.WHITE,
                                ),
                                width=250,
                                height=50,
                            ),
                        ],
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    
    # ==================== Step Navigation ====================
    step_content = ft.Container()
    
    def show_step(step_num):
        current_step.value = f"Step {step_num} of 4"
        
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
                current_step,
                ft.Container(height=20),
                step_content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )