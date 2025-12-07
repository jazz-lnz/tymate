"""
TYMATE Onboarding View
Visual wizard for time budget setup - SEE IT WORKING!
"""

import flet as ft
from state.onboarding_manager import OnboardingManager

def OnboardingPage(page: ft.Page, on_complete):
    """
    Onboarding wizard with multiple steps
    
    Args:
        page: Flet page
        on_complete: Callback function when onboarding is done
    """
    
    manager = OnboardingManager()
    
    # Store user's answers
    onboarding_data = {
        "sleep_hours": 8.0,
        "wake_time": "07:00",  # Default 7:00 AM
        "has_work": False,
        "work_hours_per_week": 0.0,
        "work_days_per_week": 0,
    }
    
    current_step = ft.Text("Step 1 of 5", size=12, color=ft.Colors.GREY_600)
    
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
    
    # ==================== STEP 3: Work Status ====================
    def build_step_3():
        def select_yes(e):
            onboarding_data["has_work"] = True
            show_step(4)
        
        def select_no(e):
            onboarding_data["has_work"] = False
            show_step(5)  # Skip step 4, go to summary
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Are you a working student?", size=28, weight=ft.FontWeight.BOLD),
                    ft.Container(height=50),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.WORK, size=50, color=ft.Colors.BLUE_400),
                                        ft.Container(height=10),
                                        ft.Text("YES", size=20, weight=ft.FontWeight.BOLD),
                                        ft.Text("I have a job", size=14, color=ft.Colors.GREY_600),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.BLUE_50,
                                border=ft.border.all(2, ft.Colors.BLUE_400),
                                border_radius=10,
                                padding=40,
                                width=200,
                                height=200,
                                on_click=select_yes,
                                ink=True,
                            ),
                            ft.Container(width=40),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.SCHOOL, size=50, color=ft.Colors.GREEN_400),
                                        ft.Container(height=10),
                                        ft.Text("NO", size=20, weight=ft.FontWeight.BOLD),
                                        ft.Text("Student only", size=14, color=ft.Colors.GREY_600),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.GREEN_50,
                                border=ft.border.all(2, ft.Colors.GREEN_400),
                                border_radius=10,
                                padding=40,
                                width=200,
                                height=200,
                                on_click=select_no,
                                ink=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=40),
                    ft.TextButton("← Back", on_click=lambda e: show_step(2)),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    
    # ==================== STEP 4: Work Details ====================
    def build_step_4():
        work_hours_field = ft.TextField(
            label="Hours per week",
            value="20",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        work_days_field = ft.TextField(
            label="Days per week",
            value="4",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        def save_work_info(e):
            onboarding_data["work_hours_per_week"] = float(work_hours_field.value or 0)
            onboarding_data["work_days_per_week"] = int(work_days_field.value or 0)
            show_step(5)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Tell us about your work", size=28, weight=ft.FontWeight.BOLD),
                    ft.Container(height=30),
                    ft.Text("This helps us calculate your available time", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=40),
                    work_hours_field,
                    ft.Container(height=20),
                    work_days_field,
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: show_step(3)),
                            ft.Container(width=20),
                            ft.ElevatedButton(
                                "Next",
                                on_click=save_work_info,
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
    
    # ==================== STEP 5: Summary ====================
    def build_step_5():
        # Calculate budget
        budget = manager.calculate_time_budget(
            sleep_hours=onboarding_data["sleep_hours"],
            has_work=onboarding_data["has_work"],
            work_hours_per_week=onboarding_data["work_hours_per_week"],
            work_days_per_week=onboarding_data["work_days_per_week"],
        )
        
        # Recommended study goal
        study_goal = budget["free_hours_per_day"] * 0.35
        
        def finish_onboarding(e):
            # Save to database (user_id would come from session in real app)
            # For now, just show success and call callback
            on_complete(onboarding_data, budget)
        
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
                                ft.Row(
                                    controls=[
                                        ft.Text("Work (avg):", size=14),
                                        ft.Text(f"{budget['work_hours_per_day']:.1f} hours", size=14),
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
                    ft.Text("You can adjust this later in Settings!", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    
                    ft.Row(
                        controls=[
                            ft.TextButton("← Back", on_click=lambda e: show_step(4 if onboarding_data["has_work"] else 3)),
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
        current_step.value = f"Step {step_num} of 5"
        
        if step_num == 1:
            step_content.content = build_step_1()
        elif step_num == 2:
            step_content.content = build_step_2()
        elif step_num == 3:
            step_content.content = build_step_3()
        elif step_num == 4:
            step_content.content = build_step_4()
        elif step_num == 5:
            step_content.content = build_step_5()
        
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