import flet as ft
from datetime import datetime
import time
import threading

def DashboardPage(page: ft.Page):
    """
    TYMATE Dashboard Page
    Shows current time, upcoming tasks, analytics preview, and time budget
    """
    
    # Get current date and time
    now = datetime.now()
    
    # Create time display with real-time updates
    time_text = ft.Text(now.strftime("%I:%M:%S %p"), size=36, weight=ft.FontWeight.BOLD)
    date_text = ft.Text(now.strftime("%A, %B %d. %Y"), size=14, color=ft.Colors.GREY_700)
    
    # Function to update time every second
    def update_time():
        while True:
            now = datetime.now()
            time_text.value = now.strftime("%I:%M:%S %p")
            date_text.value = now.strftime("%A, %B %d. %Y")
            page.update()
            time.sleep(1)
    
    # Start time update thread
    thread = threading.Thread(target=update_time, daemon=True)
    thread.start()
    
    # Sample upcoming tasks data
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
        ],
        spacing=5,
    )
    
    # Create upcoming tasks list
    task_items = []
    for task in upcoming_tasks:
        task_items.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Checkbox(value=False),
                        ft.Text(task["title"], size=14, expand=True),
                        ft.Text(task["due_date"], size=12, color=ft.Colors.RED_400),
                    ],
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                padding=12,
                margin=ft.margin.only(bottom=8),
            )
        )
    
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
    
    # Create time budget section
    time_budget_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Today's Time Budget", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                ft.Text("Study Time", size=12, color=ft.Colors.GREY_700),
                ft.ProgressBar(value=0.2, width=300, color=ft.Colors.BLUE_400, height=10),
                ft.Container(height=15),
                ft.Text("WorkTime", size=12, color=ft.Colors.GREY_700),
                ft.ProgressBar(value=0.1, width=300, color=ft.Colors.ORANGE_400, height=10),
                ft.Container(height=15),
                ft.Text(
                    "Four (4) hours remaining to meet your study goal.",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.GREY_100,
        border_radius=12,
        padding=20,
    )
    
    # Create summary cards (moved to bottom as third section)
    summary_cards = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("Total Tasks", size=14, text_align=ft.TextAlign.CENTER),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=60,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text("Completed Today", size=14, text_align=ft.TextAlign.CENTER),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=60,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text("Hours This Week", size=14, text_align=ft.TextAlign.CENTER),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=60,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text("Completion Rate", size=14, text_align=ft.TextAlign.CENTER),
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=10,
                        padding=20,
                        expand=True,
                        height=60,
                        alignment=ft.alignment.center,
                    ),
                ],
                spacing=10,
            ),
        ],
    )
    
    # Build the complete dashboard layout with 3 sections
    dashboard_content = ft.Column(
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
    
    return ft.Container(
        content=dashboard_content,
        padding=20,
        expand=True,
    )