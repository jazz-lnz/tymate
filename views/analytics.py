import flet as ft
from datetime import datetime
from services.analytics_engine import AnalyticsEngine
from utils.time_helpers import format_minutes


def AnalyticsPage(page: ft.Page, session: dict = None):
    """
    Comprehensive Analytics Page - Fixed version with better error handling
    """
    
    if not session or not session.get("user"):
        return ft.Container(
            content=ft.Text("Please login first", size=20),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    user_id = session["user"].id
    analytics_engine = AnalyticsEngine()
    
    # Load analytics data with detailed error handling
    try:
        print(f"Loading analytics for user_id: {user_id}")
        analytics = analytics_engine.get_detailed_analytics_data(user_id)
        
        completion = analytics["completion_metrics"]
        procrastination = analytics["procrastination"]
        trends = analytics["productivity_trends"]
        categories = analytics["category_insights"]
        tips = analytics["smart_tips"]
        chart_data = analytics["chart_data"]["daily_data"]
        
        print(f"Loaded data - Completed tasks: {completion['total_completed']}")
        print(f"Chart data points: {len(chart_data)}")
        print(f"Categories: {len(categories)}")
        print(f"Tips: {len(tips)}")
        
    except Exception as e:
        print(f"ERROR loading analytics: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error to user
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
                    ft.Text("Error Loading Analytics", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(str(e), size=14, color=ft.Colors.RED_700),
                    ft.Text("Check console for details", size=12, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.alignment.center,
            expand=True,
            padding=40,
        )
    
    # Helper function
    def is_mobile():
        return page.window.width < 768
    
    # ==================== Overview Cards ====================
    
    overview_cards = ft.Container(
        content=ft.Row(
            controls=[
                # Tasks Completed
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Tasks Completed", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Text(str(completion["total_completed"]), size=28, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                            ft.Text("Last 30 days", size=11, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=16,
                    width=200,
                    bgcolor=ft.Colors.WHITE,
                ),
                # Task Velocity
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Task Velocity", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Text(f"{completion['task_velocity']}", size=28, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                            ft.Text("tasks/week", size=11, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=16,
                    width=200,
                    bgcolor=ft.Colors.WHITE,
                ),
                # Average Completion
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Avg Completion", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Text(f"{completion['avg_completion_days']}d", size=28, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                            ft.Text("from given to done", size=11, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=16,
                    width=200,
                    bgcolor=ft.Colors.WHITE,
                ),
                # On-Time Rate
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("On-Time Rate", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Text(f"{completion['on_time_percentage']}%", size=28, weight=ft.FontWeight.W_400, 
                                   color=ft.Colors.GREEN_700 if completion['on_time_percentage'] >= 80 else ft.Colors.ORANGE_700),
                            ft.Text("before deadline", size=11, color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    padding=16,
                    width=200,
                    bgcolor=ft.Colors.WHITE,
                ),
            ],
            spacing=12,
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
        ),
    )
    
    # ==================== 30-Day Trend Chart ====================
    
    if not chart_data or len(chart_data) == 0:
        print("No chart data available")
        trend_chart = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("30-Day Activity", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.SHOW_CHART, size=48, color=ft.Colors.GREY_400),
                                ft.Container(height=12),
                                ft.Text("No activity data yet", size=16, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                ft.Container(height=4),
                                ft.Text("Complete some tasks to see your analytics here!", size=13, color=ft.Colors.GREY_500),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        height=200,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )
    else:
        print(f"Creating chart with {len(chart_data)} data points")
        # Find max for scaling
        max_tasks = max([d["tasks"] for d in chart_data])
        max_minutes = max([d["minutes"] for d in chart_data])
        
        max_tasks = max(max_tasks, 1)
        max_minutes = max(max_minutes, 1)
        chart_height = 200
        
        # Create bars
        bar_containers = []
        labels = []
        
        for day in chart_data:
            task_height = (day["tasks"] / max_tasks * chart_height) if day["tasks"] > 0 else 2
            
            bar_containers.append(
                ft.Container(
                    content=ft.Container(
                        width=20,
                        height=task_height,
                        bgcolor=ft.Colors.GREY_700,
                        border_radius=2,
                    ),
                    tooltip=f"{day['tasks']} tasks, {format_minutes(day.get('minutes', 0))}",
                    alignment=ft.alignment.bottom_center,
                )
            )
            
            labels.append(
                ft.Text(day["date"], size=10, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            )
        
        trend_chart = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("30-Day Activity", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                            ft.Container(expand=True),
                            ft.Row(
                                controls=[
                                    ft.Container(width=12, height=12, bgcolor=ft.Colors.GREY_700, border_radius=2),
                                    ft.Text("Tasks Completed", size=11, color=ft.Colors.GREY_600),
                                ],
                                spacing=4,
                            ),
                        ],
                    ),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                    
                    # Chart area
                    ft.Row(
                        controls=bar_containers,
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        height=chart_height,
                    ),
                    
                    # X-axis labels
                    ft.Container(height=8),
                    ft.Row(
                        controls=labels,
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
        )
    
    # ==================== Procrastination Score ====================
    
    proc_color_map = {
        "green": ft.Colors.GREEN_700,
        "yellow": ft.Colors.AMBER_700,
        "orange": ft.Colors.ORANGE_700,
        "red": ft.Colors.RED_700,
    }
    
    procrastination_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Procrastination Analysis", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                
                # Score display
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(str(procrastination["score"]), size=48, weight=ft.FontWeight.W_300, 
                                           color=proc_color_map.get(procrastination["color"], ft.Colors.GREY_700)),
                                    ft.Text("/ 100", size=16, color=ft.Colors.GREY_600),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0,
                            ),
                            expand=1,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(procrastination["level"], size=20, weight=ft.FontWeight.W_600, 
                                           color=proc_color_map.get(procrastination["color"], ft.Colors.GREY_700)),
                                    ft.Container(height=8),
                                    ft.Text(f"Last-minute: {procrastination['last_minute_percentage']}%", size=13, color=ft.Colors.GREY_700),
                                    ft.Text(f"Overdue: {procrastination['overdue_percentage']}%", size=13, color=ft.Colors.GREY_700),
                                ],
                                spacing=4,
                            ),
                            expand=2,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                
                # Insights
                ft.Container(height=16),
                ft.Column(
                    controls=[
                        ft.Text(insight, size=12, color=ft.Colors.GREY_700, italic=True)
                        for insight in procrastination["insights"]
                    ],
                    spacing=4,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
    )
    
    # ==================== Time Estimation Accuracy ====================
    
    accuracy = completion["time_estimation_accuracy"]
    accuracy_color = ft.Colors.GREEN_700 if 90 <= accuracy <= 110 else ft.Colors.ORANGE_700 if 80 <= accuracy <= 120 else ft.Colors.RED_700
    
    time_accuracy_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Time Estimation", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                
                ft.Column(
                    controls=[
                        ft.Text(f"{accuracy}%", size=36, weight=ft.FontWeight.W_400, color=accuracy_color),
                        ft.Text(completion["time_accuracy_status"], size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                        ft.Container(height=8),
                        ft.Text("Accuracy Score", size=12, color=ft.Colors.GREY_600),
                        ft.Container(height=12),
                        ft.ProgressBar(
                            value=min(accuracy / 100, 1.5) / 1.5,
                            color=accuracy_color,
                            bgcolor=ft.Colors.GREY_300,
                            height=8,
                        ),
                        ft.Container(height=8),
                        ft.Text(
                            "Target: 90-110%" if accuracy < 90 or accuracy > 110 else "Perfect range!",
                            size=11,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
    )
    
    # ==================== Category Performance ====================
    
    if not categories or len(categories) == 0:
        print("No category data")
        category_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Category Performance", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=48, color=ft.Colors.GREY_400),
                                ft.Container(height=12),
                                ft.Text("No category data", size=14, color=ft.Colors.GREY_600),
                                ft.Container(height=4),
                                ft.Text("Add tasks with categories to see performance", size=12, color=ft.Colors.GREY_500),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        height=465,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )
    else:
        print(f"Creating category cards for {len(categories)} categories")
        category_rows = []
        for cat in categories[:5]:  # Top 5 categories
            category_rows.append(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(cat["category"], size=13, color=ft.Colors.GREY_900, weight=ft.FontWeight.W_500, expand=True),
                                ft.Text(f"{cat['completion_rate']}%", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=4),
                        ft.ProgressBar(
                            value=cat["completion_rate"] / 100,
                            color=ft.Colors.GREY_800,
                            bgcolor=ft.Colors.GREY_300,
                            height=6,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(f"{cat['total_tasks']} tasks", size=11, color=ft.Colors.GREY_600),
                                ft.Text(f"On-time: {cat['on_time_rate']}%", size=11, color=ft.Colors.GREY_600),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=1, bgcolor=ft.Colors.GREY_200, margin=ft.margin.symmetric(vertical=8)),
                    ],
                    spacing=0,
                )
            )
        
        category_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Category Performance", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                    ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                    ft.Column(
                        controls=category_rows,
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                        height=465,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )
    
    # ==================== Smart Tips ====================
    
    tip_priority_colors = {
        "high": ft.Colors.RED_700,
        "medium": ft.Colors.ORANGE_700,
        "low": ft.Colors.BLUE_700,
    }
    
    if not tips or len(tips) == 0:
        print("No tips generated")
        tip_content = ft.Text(
            "Great job! No recommendations at this time. Complete more tasks to get personalized insights!", 
            size=13, 
            color=ft.Colors.GREY_600, 
            italic=True
        )
    else:
        print(f"Creating {len(tips)} tip cards")
        tip_cards = []
        for tip in tips[:4]:  # Show top 4 tips
            tip_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        width=4,
                                        height=40,
                                        bgcolor=tip_priority_colors.get(tip["priority"], ft.Colors.GREY_600),
                                        border_radius=2,
                                    ),
                                    ft.Container(width=12),
                                    ft.Column(
                                        controls=[
                                            ft.Text(tip["title"], size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                                            ft.Container(height=4),
                                            ft.Text(tip["message"], size=12, color=ft.Colors.GREY_700),
                                            ft.Container(height=8),
                                            ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14, color=ft.Colors.GREY_600),
                                                    ft.Text(tip["action"], size=11, color=ft.Colors.GREY_600, italic=True),
                                                ],
                                                spacing=4,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=16,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_50,
                    margin=ft.margin.only(bottom=8),
                )
            )
        tip_content = ft.Column(controls=tip_cards, spacing=0)
    
    smart_tips_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Smart Recommendations", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                ft.Container(height=1, bgcolor=ft.Colors.GREY_300, margin=ft.margin.only(top=8, bottom=16)),
                tip_content,
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(2, ft.Colors.GREY_300),
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
    )
    
    # ==================== Build Layout ====================
    
    def build_content_column():
        """Build the scrollable content column"""
        if is_mobile():
            return ft.Column(
                controls=[
                    overview_cards,
                    ft.Container(height=16),
                    trend_chart,
                    ft.Container(height=16),
                    procrastination_card,
                    ft.Container(height=16),
                    time_accuracy_card,
                    ft.Container(height=16),
                    category_card,
                    ft.Container(height=16),
                    smart_tips_section,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            )
        else:
            return ft.Column(
                controls=[
                    overview_cards,
                    ft.Container(height=16),
                    trend_chart,
                    ft.Container(height=16),
                    
                    # Two columns
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    procrastination_card,
                                    ft.Container(height=16),
                                    time_accuracy_card,
                                ],
                                expand=1,
                            ),
                            ft.Container(width=16),
                            category_card,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    
                    ft.Container(height=16),
                    smart_tips_section,
                    ft.Container(height=40),  # Bottom padding
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            )
    
    # Main container - PROPER FIX v2
    analytics_container = ft.Container(
        content=ft.Column(
            controls=[
                # Header (consolidated, no expand)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Analytics & Insights", size=32, weight=ft.FontWeight.W_700, color=ft.Colors.GREY_900),
                            ft.Text(f"Last updated: {datetime.now().strftime('%b %d, %Y')}", size=12, color=ft.Colors.GREY_600),
                            ft.Container(height=2, bgcolor=ft.Colors.GREY_400, margin=ft.margin.symmetric(vertical=20)),
                        ],
                        spacing=4,
                    ),
                ),
                
                # Content (scrollable, fills remaining space)
                ft.Container(
                    content=build_content_column(),
                    expand=True,  # This makes it fill available space
                ),
            ],
            spacing=0,
            expand=True,  # Column expands to fill container
        ),
        padding=24,
        expand=True,  # Container expands to fill page
        bgcolor=ft.Colors.GREY_50,
    )
    
    def on_window_resize(e=None):
        """Rebuild layout on window resize"""
        # Rebuild the content inside the expanding container (2nd control, index 1)
        analytics_container.content.controls[1].content = build_content_column()
        page.update()
    
    page.on_resized = on_window_resize
    
    print("Analytics page built successfully")
    return analytics_container