"""
TYMATE - Test Onboarding Wizard
RUN THIS FILE to see the onboarding wizard in action!

Usage: python test_onboarding.py
"""

import flet as ft
from views.onboarding import OnboardingPage
from state.onboarding_manager import OnboardingManager
from datetime import datetime

def main(page: ft.Page):
    page.title = "TYMATE - Onboarding Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1150
    page.window.height = 950
    page.window.center()
    page.padding = 0
    
    manager = OnboardingManager()
    
    # Variables to capture last-computed status for printing
    last_time_status = {"time_status": None, "time_status_color": None,
                        "study_status": None, "study_status_color": None,
                        "hours_until_bed": None, "hours_since_wake": None,
                        "study_remaining_realistic": None, "study_hours_spent": None}
    
    def on_onboarding_complete(data, budget):
        """Called when user finishes onboarding"""
        
        # Calculate additional metrics for display
        wake_time_obj = manager.parse_wake_time(data['wake_time'])
        bedtime_obj = manager.calculate_bedtime(wake_time_obj, data['sleep_hours'])
        
        # Format wake time for display
        wake_hour = int(data['wake_time'].split(':')[0])
        if wake_hour == 0:
            wake_display = "12:00 AM"
        elif wake_hour < 12:
            wake_display = f"{wake_hour}:00 AM"
        elif wake_hour == 12:
            wake_display = "12:00 PM"
        else:
            wake_display = f"{wake_hour-12}:00 PM"
        
        # Format bedtime for display
        bed_hour = bedtime_obj.hour
        bed_minute = bedtime_obj.minute
        if bed_hour == 0:
            bed_display = f"12:{bed_minute:02d} AM"
        elif bed_hour < 12:
            bed_display = f"{bed_hour}:{bed_minute:02d} AM"
        elif bed_hour == 12:
            bed_display = f"12:{bed_minute:02d} PM"
        else:
            bed_display = f"{bed_hour-12}:{bed_minute:02d} PM"
        
        # Calculate recommended study goal
        study_goal = budget['free_hours_per_day'] * 0.35
        
        # --------------------------
        # REAL-TIME STATUS TESTING
        # --------------------------
        # We'll compute real-time status using the manager helpers (same behavior as get_remaining_budget)
        current_time = datetime.now()
        hours_until_bed = manager.get_hours_until_bedtime(current_time, wake_time_obj, data['sleep_hours'])
        hours_since_wake = manager.get_hours_since_wake(current_time, wake_time_obj)
        
        # For testing we assume no study time logged yet (spent = 0). If you want to test with logs,
        # insert records into the DB or call manager.get_time_spent_today(user_id) if a user exists.
        spent_study = 0.0
        spent_total = 0.0
        
        study_remaining_absolute = max(0, study_goal - spent_study)
        study_remaining_realistic = min(study_remaining_absolute, max(0, hours_until_bed))
        
        # Time status messages (mirrors logic in OnboardingManager.get_remaining_budget)
        if hours_until_bed <= 0:
            time_status = "Past bedtime! Time to sleep."
            time_status_color = "red"
        elif hours_until_bed < 2:
            time_status = f"Only {hours_until_bed:.1f} hours until bedtime!"
            time_status_color = "orange"
        elif hours_until_bed < 4:
            time_status = f"{hours_until_bed:.1f} hours remaining today"
            time_status_color = "yellow"
        else:
            time_status = f"{hours_until_bed:.1f} hours remaining today"
            time_status_color = "green"
        
        # Study status messages
        if study_remaining_realistic <= 0:
            study_status = "Study goal completed!" if spent_study >= study_goal else "No time left today"
            study_status_color = "green" if spent_study >= study_goal else "red"
        elif study_remaining_realistic < study_remaining_absolute:
            study_status = f"{study_remaining_realistic:.1f}h left (limited by bedtime)"
            study_status_color = "orange"
        else:
            study_status = f"{study_remaining_realistic:.1f}h remaining for study goal"
            study_status_color = "blue"
        
        # Save last status for print_summary closure
        last_time_status.update({
            "time_status": time_status,
            "time_status_color": time_status_color,
            "study_status": study_status,
            "study_status_color": study_status_color,
            "hours_until_bed": round(hours_until_bed, 1),
            "hours_since_wake": round(hours_since_wake, 1),
            "study_remaining_realistic": round(study_remaining_realistic, 1),
            "study_hours_spent": spent_study,
        })
        
        # Show success message with comprehensive budget info
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=100, color=ft.Colors.GREEN_600),
                        ft.Container(height=20),
                        ft.Text("Onboarding Complete!", size=32, weight=ft.FontWeight.BOLD),
                        
                        ft.Container(height=30),
                        ft.Divider(),
                        ft.Container(height=10),
                        
                        # Your Settings Section
                        ft.Text("Your Settings:", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text("Sleep:", size=14, width=150),
                                            ft.Text(f"{data['sleep_hours']} hours/day", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Wake Time:", size=14, width=150),
                                            ft.Text(wake_display, size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Bedtime:", size=14, width=150),
                                            ft.Text(bed_display, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_600),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Working Student:", size=14, width=150),
                                            ft.Text('Yes' if data['has_work'] else 'No', size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Work Hours:", size=14, width=150),
                                            ft.Text(f"{data['work_hours_per_week']:.1f} hours/week", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                        visible=data['has_work'],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Work Days:", size=14, width=150),
                                            ft.Text(f"{data['work_days_per_week']} days/week", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                        visible=data['has_work'],
                                    ),
                                ],
                                spacing=5,
                            ),
                            bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_200),
                            border_radius=10,
                            padding=15,
                            width=400,
                        ),
                        
                        ft.Container(height=20),
                        
                        # Calculated Budget Section
                        ft.Text("Calculated Budget:", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Daily Breakdown:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                    ft.Container(height=5),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Total Hours:", size=14, width=180),
                                            ft.Text(f"{budget['total_hours_per_day']:.1f} hours", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Waking Hours:", size=14, width=180),
                                            ft.Text(f"{budget['waking_hours_per_day']:.1f} hours", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Work (avg/day):", size=14, width=180),
                                            ft.Text(f"{budget['work_hours_per_day']:.2f} hours", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_600),
                                        ],
                                        visible=data['has_work'],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Free Time:", size=14, width=180),
                                            ft.Text(f"{budget['free_hours_per_day']:.1f} hours", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                                        ],
                                    ),
                                    ft.Divider(),
                                    ft.Text("Weekly Breakdown:", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                                    ft.Container(height=5),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Waking Hours/Week:", size=14, width=180),
                                            ft.Text(f"{budget['waking_hours_per_week']:.1f} hours", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Work Hours/Week:", size=14, width=180),
                                            ft.Text(f"{budget['work_hours_per_week']:.1f} hours", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_600),
                                        ],
                                        visible=data['has_work'],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Free Time/Week:", size=14, width=180),
                                            ft.Text(f"{budget['free_hours_per_week']:.1f} hours", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                                        ],
                                    ),
                                ],
                                spacing=5,
                            ),
                            bgcolor=ft.Colors.GREEN_50,
                            border=ft.border.all(1, ft.Colors.GREEN_200),
                            border_radius=10,
                            padding=15,
                            width=400,
                        ),
                        
                        ft.Container(height=20),
                        
                        # REAL-TIME STATUS DISPLAY (TEST)
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("⏱ Real-time Status (test):", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Container(height=8),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Now:", size=14, width=150),
                                            ft.Text(current_time.strftime("%I:%M %p"), size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Time Status:", size=14, width=150),
                                            ft.Text(time_status, size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Study Status:", size=14, width=150),
                                            ft.Text(study_status, size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Hours since wake:", size=14, width=150),
                                            ft.Text(f"{hours_since_wake:.1f} h", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Hours until bedtime:", size=14, width=150),
                                            ft.Text(f"{hours_until_bed:.1f} h", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Study remaining (realistic):", size=14, width=150),
                                            ft.Text(f"{study_remaining_realistic:.1f} h", size=14, weight=ft.FontWeight.BOLD),
                                        ],
                                    ),
                                ],
                                spacing=5,
                            ),
                            bgcolor=ft.Colors.YELLOW_50,
                            border=ft.border.all(1, ft.Colors.AMBER_200),
                            border_radius=10,
                            padding=12,
                            width=400,
                        ),
                        
                        ft.Container(height=20),
                        
                        # Study Goal Recommendation
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Recommended Study Goal:", size=16, weight=ft.FontWeight.BOLD),
                                    ft.Container(height=5),
                                    ft.Text(
                                        f"{study_goal:.1f} hours/day",
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.PURPLE_600,
                                    ),
                                    ft.Text(
                                        f"({study_goal * 7:.1f} hours/week)",
                                        size=14,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Text(
                                        "≈ 35% of your free time",
                                        size=12,
                                        italic=True,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            bgcolor=ft.Colors.AMBER_50,
                            border=ft.border.all(1, ft.Colors.AMBER_300),
                            border_radius=10,
                            padding=15,
                            width=400,
                        ),
                        
                        ft.Container(height=30),
                        
                        # Action buttons
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Restart Onboarding",
                                    icon=ft.Icons.REFRESH,
                                    on_click=lambda e: show_onboarding(),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.BLUE_400,
                                        color=ft.Colors.WHITE,
                                    ),
                                ),
                                ft.ElevatedButton(
                                    "Print Summary",
                                    icon=ft.Icons.PRINT,
                                    on_click=lambda e: print_summary(data, budget, study_goal, wake_display, bed_display),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREEN_400,
                                        color=ft.Colors.WHITE,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                alignment=ft.alignment.center,
                padding=20,
            )
        )
        page.update()
    
    def print_summary(data, budget, study_goal, wake_display, bed_display):
        """Print a detailed summary to console"""
        print("\n" + "=" * 60)
        print("TYMATE ONBOARDING SUMMARY")
        print("=" * 60)
        print("\nYOUR SETTINGS:")
        print(f"   Sleep: {data['sleep_hours']} hours/day")
        print(f"   Wake Time: {wake_display}")
        print(f"   Bedtime: {bed_display}")
        print(f"   Working Student: {'Yes' if data['has_work'] else 'No'}")
        if data['has_work']:
            print(f"   Work Hours: {data['work_hours_per_week']:.1f} hours/week")
            print(f"   Work Days: {data['work_days_per_week']} days/week")
        
        print("\nCALCULATED BUDGET:")
        print("   Daily:")
        print(f"      Total: {budget['total_hours_per_day']:.1f} hours")
        print(f"      Waking: {budget['waking_hours_per_day']:.1f} hours")
        if data['has_work']:
            print(f"      Work (avg): {budget['work_hours_per_day']:.2f} hours")
        print(f"      Free Time: {budget['free_hours_per_day']:.1f} hours")
        
        print("   Weekly:")
        print(f"      Waking: {budget['waking_hours_per_week']:.1f} hours")
        if data['has_work']:
            print(f"      Work: {budget['work_hours_per_week']:.1f} hours")
        print(f"      Free Time: {budget['free_hours_per_week']:.1f} hours")
        
        print(f"\nRECOMMENDED STUDY GOAL:")
        print(f"   {study_goal:.1f} hours/day ({study_goal * 7:.1f} hours/week)")
        print(f"   ≈ 35% of your free time")
        
        # Print the real-time status we computed earlier (if present)
        if last_time_status["time_status"] is not None:
            print("\nREAL-TIME STATUS (test):")
            print(f"   Now: {datetime.now().strftime('%I:%M %p')}")
            print(f"   Time status: {last_time_status['time_status']} (color {last_time_status['time_status_color']})")
            print(f"   Study status: {last_time_status['study_status']} (color {last_time_status['study_status_color']})")
            print(f"   Hours since wake: {last_time_status['hours_since_wake']} h")
            print(f"   Hours until bedtime: {last_time_status['hours_until_bed']} h")
            print(f"   Study remaining (realistic): {last_time_status['study_remaining_realistic']} h")
            print(f"   Study hours spent today (mocked): {last_time_status['study_hours_spent']} h")
        
        print("\n" + "=" * 60)
        print("Summary printed to console!")
        print("=" * 60 + "\n")
    
    def show_onboarding():
        """Show onboarding wizard"""
        page.controls.clear()
        page.add(OnboardingPage(page, on_onboarding_complete))
        page.update()
    
    # Start with onboarding
    show_onboarding()

if __name__ == "__main__":
    ft.app(target=main)
