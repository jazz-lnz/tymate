import flet as ft
from components.navbar import create_navbar
from views.dashboard import DashboardPage
from views.login import LoginPage
from views.tasks import TasksPage
from views.log_hours import LogHoursPage
from views.settings import SettingsPage
from views.onboarding import OnboardingPage
from views.admin import AdminPage
from views.analytics import AnalyticsPage
from views.audit_logs import AuditLogsPage
from views.user_activity import UserActivityPage

def main(page: ft.Page):
    """
    TYMATE - Time-Aware School Activity Tracker
    Main application entry point with route-based navigation
    """
    
    # Page configuration
    page.title = "TYMATE - Time Management"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 1150
    page.window.height = 950
    # page.window.resizable = False   # desktop app fixed size
    page.window.center()
    
    
    # Session state to store user data and app state
    session = {
        "user": None,
        "is_online": False,
        "theme": "light",
        "onboarding_completed": False,  # Track if user completed onboarding
    }

    # Persistent container that holds the current page content
    main_content = ft.Container(expand=True)
    
    # Navigation function to switch between pages
    def route_change(route: str):
        """Handle route changes"""
        
        # Special case: If user needs onboarding, redirect
        if not session["onboarding_completed"] and page.route not in ("/onboarding", "/login", "/admin", "/settings"):
            page.route = "/onboarding"
            return route_change("/onboarding")
        
        # Clear and rebuild
        page.controls.clear()
        
        # Don't show navbar on login or onboarding pages
        if page.route not in ("/login", "/onboarding"):
            navbar = create_navbar(page, page.route, session, route_change)
            page.add(navbar)
        
        page.add(main_content)
        
        # Swap content inside main_content without removing navbar
        if page.route in ("/", "/dashboard"):
            main_content.content = DashboardPage(page, session)   # returns a Container
        elif page.route == "/tasks":
            main_content.content = TasksPage(page, session)
        elif page.route == "/log_hours":
            main_content.content = LogHoursPage(page)
        elif page.route == "/settings":
            main_content.content = SettingsPage(page, session)
        elif page.route == "/admin":
            main_content.content = AdminPage(page, session)
        elif page.route == "/audit_logs":
            main_content.content = AuditLogsPage(page, session)
        elif page.route == "/user_activity":
            main_content.content = UserActivityPage(page, session)
        elif page.route == "/analytics":
            main_content.content = AnalyticsPage(page, session)
        elif page.route == "/login":
            main_content.content = LoginPage(page, session)
        elif page.route == "/onboarding":
            def on_onboarding_complete(data, budget):
                """Called when onboarding is finished"""
                # Save to session (in real app, save to database)
                session["onboarding_completed"] = True
                session["time_budget"] = budget
                session["user_data"] = data
                
                # Redirect to dashboard
                page.route = "/dashboard"
                route_change("/dashboard")
            
            main_content.content = OnboardingPage(
                page, 
                on_onboarding_complete,
                session
            )
        else:
            main_content.content = DashboardPage(page, session)

        page.update()
    
    # Set up route change handler
    page.on_route_change = lambda e: route_change(page.route)
    
    # Start with login route
    page.route = "/login"
    route_change("/login")

# Run the app
if __name__ == "__main__":
    ft.app(target=main)