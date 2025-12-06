import flet as ft

def create_navbar(page: ft.Page, current_route: str, session: dict, route_change: callable):
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
