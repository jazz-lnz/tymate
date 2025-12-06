import flet as ft
from views.dashboard import DashboardPage
from views.login import LoginPage
from views.tasks import TasksPage
from views.log_hours import LogHoursPage
from views.settings import SettingsPage

def main(page: ft.Page):
    """
    TYMATE - Time-Aware School Activity Tracker
    Main application entry point with route-based navigation
    """
    
    # Page configuration
    page.title = "TYMATE - Time Management"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    
    # Session state to store user data and app state
    session = {
        "user": None,
        "is_online": False,
        "theme": "light"
    }

    # Persistent container that holds the current page content
    main_content = ft.Container(expand=True)
    
    # Navigation function to switch between pages
    def route_change(route: str):
        # Build navbar once per route call, but persist it
        navbar = create_navbar(page.route)

        # Mount navbar + main content only once (no full clear-add cycle on every route)
        page.controls.clear()
        page.add(navbar, main_content)

        # Swap content inside main_content without removing navbar
        if page.route in ("/", "/dashboard"):
            main_content.content = DashboardPage(page)   # returns a Container
        elif page.route == "/tasks":
            main_content.content = TasksPage(page)
        elif page.route == "/log_hours":
            main_content.content = LogHoursPage(page)
        elif page.route == "/settings":
            main_content.content = SettingsPage(page)
        elif page.route == "/login":
            main_content.content = LoginPage(page)
        else:
            main_content.content = DashboardPage(page)

        page.update()

    
    def create_navbar(current_route):
        """Create navigation bar with active route highlighting"""
        
        def navigate_to(route):
            """Navigate to a specific route"""
            page.route = route
            route_change(route)
        
        def toggle_sync(e):
            """Toggle online/offline status"""
            session["is_online"] = not session["is_online"]
            page.update()
        
        # Determine active tab styling
        def is_active(route):
            return current_route == route
        
        # Online/Offline status indicator
        status_text = "Online" if session["is_online"] else "Offline"
        status_color = ft.Colors.GREEN_400 if session["is_online"] else ft.Colors.RED_400
        
        navbar = ft.Container(
            content=ft.Row(
                controls=[
                    # Hamburger menu button
                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Menu",
                    ),
                    
                    # Navigation tabs
                    ft.TextButton(
                        "Dashboard",
                        style=ft.ButtonStyle(
                            color=ft.Colors.ORANGE_400 if is_active("/dashboard") else ft.Colors.WHITE,
                        ),
                        on_click=lambda _: navigate_to("/dashboard"),
                    ),
                    ft.TextButton(
                        "Tasks",
                        style=ft.ButtonStyle(
                            color=ft.Colors.ORANGE_400 if is_active("/tasks") else ft.Colors.WHITE,
                        ),
                        on_click=lambda _: navigate_to("/tasks"),
                    ),
                    ft.TextButton(
                        "Log Hours",
                        style=ft.ButtonStyle(
                            color=ft.Colors.ORANGE_400 if is_active("/log_hours") else ft.Colors.WHITE,
                        ),
                        on_click=lambda _: navigate_to("/log_hours"),
                    ),
                    
                    # Spacer to push right-side items to the end
                    ft.Container(expand=True),
                    
                    # Online/Offline status
                    ft.Container(
                        content=ft.Text(
                            status_text,
                            color=ft.Colors.WHITE,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=status_color,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                    ),
                    
                    # Toggle Sync button
                    ft.OutlinedButton(
                        "Toggle Sync",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            side=ft.BorderSide(1, ft.Colors.WHITE),
                        ),
                        on_click=toggle_sync,
                    ),
                    
                    # Settings icon
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Settings",
                        on_click=lambda _: navigate_to("/settings"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ft.Colors.GREY_800,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
        )
        
        return navbar
    
    # Set up route change handler
    page.on_route_change = route_change
    
    # Start with dashboard route
    page.route = "/dashboard"
    route_change("/dashboard")

# Run the app
if __name__ == "__main__":
    ft.app(target=main)