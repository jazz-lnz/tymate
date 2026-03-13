import os
from dotenv import load_dotenv
import flet as ft
from components.navbar import create_navbar
from views.dashboard import DashboardPage
from views.login import LoginPage
from views.tasks import TasksPage
from views.task_details import TaskDetailsPage
from views.time_it import TimeItPage
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
    def route_change(route: str, bypass_time_it_guard: bool = False):
        """Handle route changes"""
        current_route = session.get("current_route", page.route)
        target_route = route

        leaving_time_it = current_route == "/time_it" and target_route != "/time_it"
        timer_actively_running = (
            callable(session.get("time_it_is_timer_running"))
            and session["time_it_is_timer_running"]()
        )
        has_active_progress = (
            callable(session.get("time_it_has_active_progress"))
            and session["time_it_has_active_progress"]()
        )

        if (
            not bypass_time_it_guard
            and leaving_time_it
            and not session.get("time_it_navigation_guard_open", False)
            and timer_actively_running
        ):
            session["time_it_navigation_guard_open"] = True

            def confirm_leave(e):
                if callable(session.get("time_it_discard_current_session")):
                    session["time_it_discard_current_session"]()
                if callable(session.get("time_it_cleanup")):
                    session["time_it_cleanup"](preserve_progress=False)
                session["time_it_navigation_guard_open"] = False
                dialog.open = False
                page.route = target_route
                route_change(target_route, bypass_time_it_guard=True)

            def cancel_leave(e):
                session["time_it_navigation_guard_open"] = False
                dialog.open = False
                page.route = current_route
                route_change(current_route, bypass_time_it_guard=True)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Timer Running"),
                content=ft.Text(
                    "Timer is running. Navigating away will stop and discard the current session. Continue?"
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_leave),
                    ft.ElevatedButton("Yes", on_click=confirm_leave),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            return

        if not bypass_time_it_guard and leaving_time_it and has_active_progress:
            if callable(session.get("time_it_cleanup")):
                session["time_it_cleanup"](preserve_progress=True)
        
        # Special case: If user needs onboarding, redirect
        if not session["onboarding_completed"] and page.route not in ("/onboarding", "/login", "/admin", "/settings"):
            page.route = "/onboarding"
            return route_change("/onboarding")
        
        # Clear and rebuild
        page.controls.clear()
        session["route_change"] = route_change
        
        # Don't show navbar on login or onboarding pages
        if page.route not in ("/login", "/onboarding"):
            navbar = create_navbar(page, page.route, session, route_change)
            page.add(navbar)
        
        page.add(main_content)
        
        # Swap content inside main_content without removing navbar
        if page.route in ("/", "/dashboard"):
            main_content.content = DashboardPage(page, session)   # returns a Container
        elif page.route == "/tasks":
            session["task_details_create_mode"] = False
            main_content.content = TasksPage(page, session)
        elif page.route == "/tasks/new":
            session["task_details_create_mode"] = True
            session["selected_task_id"] = None
            main_content.content = TaskDetailsPage(page, session)
        elif page.route.startswith("/tasks/"):
            session["task_details_create_mode"] = False
            try:
                session["selected_task_id"] = int(page.route.split("/")[-1])
                main_content.content = TaskDetailsPage(page, session)
            except (TypeError, ValueError):
                main_content.content = TasksPage(page, session)
        elif page.route == "/time_it":
            main_content.content = TimeItPage(page, session)
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

        session["current_route"] = page.route
        page.update()
    
    # Set up route change handler
    page.on_route_change = lambda e: route_change(page.route)
    
    # Start with login route
    page.route = "/login"
    route_change("/login")

# Run the app
if __name__ == "__main__":
    # Load environment (for FLET_SECRET_KEY, DB path, etc.)
    load_dotenv()

    view_mode = os.getenv("FLET_APP_VIEW", "web").lower()
    app_view = ft.AppView.WEB_BROWSER if view_mode == "web" else ft.AppView.FLET_APP
    ft.app(target=main, view=app_view, assets_dir="assets")