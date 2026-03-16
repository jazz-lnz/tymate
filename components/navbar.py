import flet as ft

def create_navbar(page: ft.Page, current_route: str, session: dict, route_change: callable):
    """Create bottom mobile navigation bar."""
        
    def navigate_to(route):
        """Navigate to a specific route"""
        page.route = route
        route_change(route)
    
    def is_active(route):
        return current_route == route or (route == "/tasks" and current_route.startswith("/tasks/"))

    user = session.get("user")
    is_admin = user and user.role == "admin"

    def nav_item(label: str, badge: str, route: str, center: bool = False):
        active = is_active(route)
        badge_bg = "#C9D8E8" if active else "#E7EAEE"
        badge_text = "#233142" if active else "#7C8794"
        label_color = "#2E3135" if active else "#6D737A"

        if center:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                badge,
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=badge_text,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            width=30,
                            height=24,
                            border_radius=8,
                            bgcolor=badge_bg,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            label,
                            size=11,
                            weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_600,
                            color=label_color,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda e: navigate_to(route),
                ink=True,
                expand=True,
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            badge,
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color=badge_text,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=28,
                        height=22,
                        border_radius=7,
                        bgcolor=badge_bg,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        label,
                        size=10,
                        color=label_color,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=lambda e: navigate_to(route),
            ink=True,
            expand=True,
        )

    if is_admin:
        nav_controls = [
            nav_item("Admin", "AD", "/admin"),
            nav_item("Activity", "AC", "/user_activity"),
            nav_item("Audit", "AU", "/audit_logs"),
            nav_item("Account", "ME", "/settings"),
        ]
    else:
        nav_controls = [
            nav_item("Home", "HM", "/dashboard"),
            nav_item("Tasks", "TK", "/tasks"),
            nav_item("Time It!", "TI", "/time_it", center=True),
            nav_item("Analytics", "AN", "/analytics"),
            nav_item("Account", "ME", "/settings"),
        ]

    navbar = ft.Container(
        content=ft.Row(
            controls=nav_controls,
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#F6F4F1",
        padding=ft.padding.only(left=10, right=10, top=4, bottom=6),
    )
    
    return navbar
