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
    analytics_engine = AnalyticsEngine()
    
    # Load analytics data with detailed error handling
    try:
        print(f"Loading analytics for user_id: {user_id}")
        analytics = analytics_engine.get_detailed_analytics_data(user_id)
        
        completion = analytics["completion_metrics"]
        procrastination = analytics["procrastination"]
        trends = analytics["productivity_trends"]
        peak_hours = analytics["peak_hours"]
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
    def window_width():
        return page.window.width or 430

    def is_mobile():
        return window_width() < 900

    def content_width():
        return min(1120, max(380, window_width() - 48))

    def overview_card_width():
        width = window_width()
        if width < 560:
            return max(170, width - 72)
        if width < 900:
            return 220
        return 250
    
    # ==================== Overview Cards ====================

    def overview_metric_card(title: str, value: str, subtitle: str, value_color=title_color):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=12, color=accent_color, weight=ft.FontWeight.W_500),
                    ft.Container(height=4),
                    ft.Text(value, size=28, weight=ft.FontWeight.W_400, color=value_color),
                    ft.Text(subtitle, size=11, color=accent_color),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            padding=16,
            bgcolor=panel_bg,
            shadow=drop_shadow,
            expand=True,
        )

    avg_completion_days = completion.get("avg_completion_days")
    avg_completion_value = f"{avg_completion_days}d" if avg_completion_days is not None else ""
    avg_completion_subtitle = "from given to done" if avg_completion_days is not None else "no valid completion data"

    overview_cards = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        overview_metric_card(
                            "Tasks Completed",
                            str(completion["total_completed"]),
                            "Last 30 days",
                        ),
                        ft.Container(width=12),
                        overview_metric_card(
                            "Task Velocity",
                            f"{completion['task_velocity']}",
                            "tasks/week",
                        ),
                    ],
                    spacing=0,
                ),
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        overview_metric_card(
                            "Avg Completion",
                            avg_completion_value,
                            avg_completion_subtitle,
                        ),
                        ft.Container(width=12),
                        overview_metric_card(
                            "On-Time Rate",
                            f"{completion['on_time_percentage']}%",
                            "before deadline",
                            ft.Colors.GREEN_700 if completion['on_time_percentage'] >= 80 else ft.Colors.ORANGE_700,
                        ),
                    ],
                    spacing=0,
                ),
            ],
            spacing=0,
        ),
    )
    
    # ==================== 30-Day Trend Chart ====================
    
    if not chart_data or len(chart_data) == 0:
        print("No chart data available")
        trend_chart = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("30-Day Activity", size=18, weight=ft.FontWeight.W_600, color=title_color),
                    ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
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
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
        )
    else:
        print(f"Creating chart with {len(chart_data)} data points")
        # Find max for scaling
        max_tasks = max([d["tasks"] for d in chart_data])
        max_minutes = max([d["minutes"] for d in chart_data])
        
        max_tasks = max(max_tasks, 1)
        max_minutes = max(max_minutes, 1)
        chart_height = 200
        chart_width = max(content_width() - 48, len(chart_data) * 52)
        
        # Create bars and labels in the same horizontally scrollable strip.
        day_columns = []
        
        for day in chart_data:
            task_height = (day["tasks"] / max_tasks * chart_height) if day["tasks"] > 0 else 2

            full_date = ""
            try:
                full_date = datetime.strptime(day.get("full_date", ""), "%Y-%m-%d").strftime("%b %d")
            except Exception:
                full_date = day.get("full_date", "")
            
            day_columns.append(
                ft.Container(
                    width=44,
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                height=chart_height,
                                alignment=ft.alignment.bottom_center,
                                content=ft.Container(
                                    width=20,
                                    height=task_height,
                                    bgcolor=accent_color,
                                    border_radius=2,
                                    tooltip=f"{day['tasks']} tasks, {format_minutes(day.get('minutes', 0))}",
                                ),
                            ),
                            ft.Container(height=8),
                            ft.Text(day["date"], size=10, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                            ft.Text(full_date, size=9, color=accent_color, text_align=ft.TextAlign.CENTER),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        
        trend_chart = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("30-Day Activity", size=18, weight=ft.FontWeight.W_600, color=title_color),
                            ft.Container(expand=True),
                            ft.Row(
                                controls=[
                                    ft.Container(width=12, height=12, bgcolor=accent_color, border_radius=2),
                                    ft.Text("Tasks Completed", size=11, color=accent_color),
                                ],
                                spacing=4,
                            ),
                        ],
                    ),
                    ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                    
                    # Chart area and labels share one horizontal scroller.
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=chart_width,
                                content=ft.Row(
                                    controls=day_columns,
                                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    ft.Container(height=6),
                    ft.Text(
                        "Swipe sideways to view all 30 days",
                        size=10,
                        color=accent_color,
                        italic=True,
                        visible=is_mobile(),
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
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
                ft.Text("Procrastination Analysis", size=18, weight=ft.FontWeight.W_600, color=title_color),
                ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                
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
                            width=130,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(width=18),
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
                            expand=True,
                            padding=ft.padding.only(left=4),
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
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )
    
    # ==================== Time Estimation Accuracy ====================
    
    accuracy = completion["time_estimation_accuracy"]
    has_time_accuracy_data = completion.get("time_accuracy_status") != "No data"
    accuracy_color = (
        ft.Colors.GREEN_700
        if 90 <= accuracy <= 110
        else ft.Colors.ORANGE_700 if 80 <= accuracy <= 120 else ft.Colors.RED_700
    )
    
    time_accuracy_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Time Estimation", size=18, weight=ft.FontWeight.W_600, color=title_color),
                ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                
                ft.Column(
                    controls=[
                        ft.Text(
                            f"{accuracy}%" if has_time_accuracy_data else "No data",
                            size=36 if has_time_accuracy_data else 24,
                            weight=ft.FontWeight.W_400,
                            color=accuracy_color if has_time_accuracy_data else ft.Colors.GREY_600,
                        ),
                        ft.Text(completion["time_accuracy_status"], size=14, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                        ft.Text(
                            (
                                "Track sessions on estimated tasks to unlock this metric."
                                if not has_time_accuracy_data
                                else "100%--exact and not over- or underestimation--is the goal"
                            ),
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
        padding=ft.padding.only(left=16, top=16, right=16, bottom=20),
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )

    # ==================== Peak Productivity Hours ====================

    peak_hours_list = peak_hours.get("peak_hours", []) if peak_hours else []

    def format_peak_hour_label(value: str) -> str:
        try:
            hour = int(str(value).split(":")[0])
            return datetime.strptime(f"{hour:02d}:00", "%H:%M").strftime("%I:%M %p").lstrip("0")
        except Exception:
            return value

    if not peak_hours_list:
        peak_content = ft.Text(
            "Not enough session data yet to identify your strongest hours.",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True,
        )
    else:
        peak_content = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(format_peak_hour_label(hour), size=13, weight=ft.FontWeight.W_600, color=title_color),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8,
                    bgcolor=soft_panel_bg,
                )
                for hour in peak_hours_list[:3]
            ],
            spacing=8,
            wrap=True,
        )

    peak_productivity_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Peak Productivity Hours", size=18, weight=ft.FontWeight.W_600, color=title_color),
                ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                peak_content,
                ft.Container(height=10),
                ft.Text(
                    "Use these windows for high-focus work and tougher tasks.",
                    size=11,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )

    # ==================== Productivity Trends ====================

    trend_label_map = {
        "improving": "Improving",
        "stable": "Stable",
        "declining": "Declining",
        "insufficient_data": "Not enough data",
        "error": "Unavailable",
    }
    trend_color_map = {
        "improving": ft.Colors.GREEN_700,
        "stable": ft.Colors.BLUE_GREY_700,
        "declining": ft.Colors.ORANGE_700,
        "insufficient_data": ft.Colors.GREY_700,
        "error": ft.Colors.RED_700,
    }
    trend_key = trends.get("trend", "insufficient_data")

    productivity_trends_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Productivity Trends", size=18, weight=ft.FontWeight.W_600, color=title_color),
                ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                ft.Row(
                    controls=[
                        ft.Text(
                            trend_label_map.get(trend_key, "Not enough data"),
                            size=20,
                            weight=ft.FontWeight.W_600,
                            color=trend_color_map.get(trend_key, ft.Colors.GREY_700),
                        ),
                        ft.Container(expand=True),
                        ft.Text("12-week view", size=11, color=accent_color),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=10),
                ft.Text(
                    f"Current weekly avg: {trends.get('current_week_average', 0)} tasks",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                ft.Text(
                    f"Predicted next week: {int(trends.get('predicted_next_week', 0))} tasks",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )
    
    # ==================== Category Performance ====================
    
    if not categories or len(categories) == 0:
        print("No category data")
        category_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Category Performance", size=18, weight=ft.FontWeight.W_600, color=title_color),
                    ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
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
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
            expand=True,
        )
    else:
        print(f"Creating category table for {len(categories)} categories")

        def _ontime_color(rate):
            if rate >= 75:
                return ft.Colors.GREEN_700
            elif rate >= 50:
                return ft.Colors.ORANGE_700
            else:
                return ft.Colors.RED_700

        col_widths = [156, 52, 96, 84]  # category, tasks, completion, on-time
        table_width = sum(col_widths) + 28

        def table_header():
            labels = ["Category", "Tasks", "Completion", "On-Time"]
            cells = []
            for i, label in enumerate(labels):
                cells.append(
                    ft.Container(
                        content=ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=accent_color),
                        width=col_widths[i],
                        alignment=ft.alignment.center_left if i == 0 else ft.alignment.center,
                    )
                )
            return ft.Container(
                content=ft.Row(controls=cells, spacing=4),
                padding=ft.padding.only(left=8, right=8, top=6, bottom=6),
                bgcolor=soft_panel_bg,
                border_radius=ft.border_radius.only(top_left=6, top_right=6),
            )

        table_rows = []
        for i, cat in enumerate(categories[:8]):
            row_bg = panel_bg if i % 2 == 0 else soft_panel_bg
            completion = cat["completion_rate"]
            ontime = cat["on_time_rate"]
            comp_color = ft.Colors.GREEN_700 if completion >= 75 else ft.Colors.ORANGE_700 if completion >= 50 else ft.Colors.RED_700
            table_rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    cat["category"],
                                    size=12,
                                    color=title_color,
                                    weight=ft.FontWeight.W_500,
                                    max_lines=4,
                                ),
                                width=col_widths[0],
                            ),
                            ft.Container(
                                content=ft.Text(str(cat["total_tasks"]), size=12, color=accent_color, text_align=ft.TextAlign.CENTER),
                                width=col_widths[1],
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=ft.Text(f"{completion}%", size=12, weight=ft.FontWeight.W_600, color=comp_color, text_align=ft.TextAlign.CENTER),
                                width=col_widths[2],
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=ft.Text(f"{ontime}%", size=12, weight=ft.FontWeight.W_600, color=_ontime_color(ontime), text_align=ft.TextAlign.CENTER),
                                width=col_widths[3],
                                alignment=ft.alignment.center,
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=row_bg,
                    padding=ft.padding.symmetric(horizontal=8, vertical=10),
                )
            )

        category_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Category Performance", size=18, weight=ft.FontWeight.W_600, color=title_color),
                    ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                    ft.Text(
                        "Scroll sideways to view completion and on-time ratings.",
                        size=10,
                        color=accent_color,
                        italic=True,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=table_width,
                                content=ft.Column(
                                    controls=[table_header()] + table_rows,
                                    spacing=0,
                                ),
                                border=ft.border.all(1, border_color),
                                border_radius=8,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ],
                spacing=0,
            ),
            padding=20,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            bgcolor=panel_bg,
            shadow=drop_shadow,
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
            "No recommendations at this time. Complete more tasks to get personalized insights!", 
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
                                            ft.Column(
                                                controls=[
                                                    ft.Row(
                                                        controls=[
                                                            ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, size=14, color=ft.Colors.GREY_600),
                                                            ft.Text("Suggested action", size=11, color=ft.Colors.GREY_600, italic=True),
                                                        ],
                                                        spacing=4,
                                                    ),
                                                    ft.Container(height=2),
                                                    ft.Text(
                                                        tip["action"],
                                                        size=11,
                                                        color=ft.Colors.GREY_700,
                                                        max_lines=4,
                                                    ),
                                                ],
                                                spacing=0,
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
                    bgcolor=soft_panel_bg,
                    margin=ft.margin.only(bottom=8),
                )
            )
        tip_content = ft.Column(controls=tip_cards, spacing=0)
    
    smart_tips_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Smart Recommendations", size=18, weight=ft.FontWeight.W_600, color=title_color),
                ft.Container(height=1, bgcolor=border_color, margin=ft.margin.only(top=8, bottom=16)),
                tip_content,
            ],
            spacing=0,
        ),
        padding=20,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )
    
    # ==================== Build Layout ====================
    
    def build_content_column():
        """Build the scrollable content column"""
        if is_mobile():
            return ft.Column(
                controls=[
                    time_accuracy_card,
                    ft.Container(height=10),
                    procrastination_card,
                    ft.Container(height=10),
                    peak_productivity_card,
                    ft.Container(height=10),
                    trend_chart,
                    ft.Container(height=16),
                    productivity_trends_card,
                    ft.Container(height=16),
                    category_card,
                    ft.Container(height=16),
                    overview_cards,
                    ft.Container(height=16),
                    smart_tips_section,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        else:
            return ft.Column(
                controls=[
                    time_accuracy_card,
                    ft.Container(height=10),
                    procrastination_card,
                    ft.Container(height=10),
                    peak_productivity_card,
                    ft.Container(height=10),
                    trend_chart,
                    ft.Container(height=16),
                    productivity_trends_card,
                    ft.Container(height=16),
                    category_card,
                    ft.Container(height=16),
                    overview_cards,
                    ft.Container(height=16),
                    smart_tips_section,
                    ft.Container(height=40),  # Bottom padding
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
    
    # Main container - PROPER FIX v2
    analytics_content = ft.Container(
        content=ft.Column(
            controls=[
                # Header (consolidated, no expand)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Analytics & Insights", size=30 if is_mobile() else 32, weight=ft.FontWeight.W_700, color=title_color),
                            ft.Text(f"Last updated: {datetime.now().strftime('%b %d, %Y')}", size=12, color=accent_color),
                            ft.Container(height=2, bgcolor=border_color, margin=ft.margin.symmetric(vertical=20)),
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
            expand=True,
        ),
        width=content_width(),
        padding=ft.padding.only(left=20, right=20, top=66, bottom=24),
    )

    analytics_container = ft.Container(
        content=ft.Row(
            controls=[analytics_content],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#DDE9FB", "#FFFFFF"],
        ),
    )
    
    def on_window_resize(e=None):
        """Rebuild layout on window resize"""
        analytics_content.width = content_width()
        analytics_content.content.controls[1].content = build_content_column()
        page.update()
    
    page.on_resized = on_window_resize
    
    print("Analytics page built successfully")
    return analytics_container