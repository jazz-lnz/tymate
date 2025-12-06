import flet as ft
from components.navbar import create_navbar
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
    page.window.width = 1200
    page.window.height = 800
    
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
        navbar = create_navbar(page, page.route, session, route_change)

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
    
    # Set up route change handler
    page.on_route_change = route_change
    
    # Start with dashboard route
    page.route = "/dashboard"
    route_change("/dashboard")

# Run the app
if __name__ == "__main__":
    ft.app(target=main)