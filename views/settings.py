import flet as ft
from state.auth_manager import AuthManager
from state.onboarding_manager import OnboardingManager

def SettingsPage(page: ft.Page, session: dict = None):
    """ Settings and profile management page """
    
    if not session.get("user"):
        return ft.Container(
            content=ft.Text("Please login first"),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    auth = AuthManager()
    user = session["user"]
    
    def logout(e):
        """Logout user"""
        # Call logout on the server/database
        if session.get("token"):
            try:
                auth.logout(session["token"])
            except Exception:
                pass  # Logout from DB might fail, but we still want to clear local session
        
        # Clear all session data
        session["user"] = None
        session["user_id"] = None
        session["token"] = None
        session["is_online"] = False
        session["onboarding_completed"] = False
        session["time_budget"] = None
        session["user_data"] = None
        
        # Navigate to login page
        page.route = "/login"
        page.update()
    
    # Avatar placeholder (future upload validation)
    avatar_placeholder = ft.Container(
        width=96,
        height=96,
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=48,
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.GREY_600),
    )

    # Top identity block (centered)
    identity_block = ft.Column(
        controls=[
            avatar_placeholder,
            ft.Text(user.username, size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
            ft.Container(
                content=ft.Text(
                    user.role.upper(),
                    size=12,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.W_600,
                ),
                bgcolor=ft.Colors.GREY_800 if user.role == "admin" else ft.Colors.GREY_500,
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                border_radius=12,
            ),
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=28, color=ft.Colors.GREY_800),
                        ft.Text("Settings", size=24, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    spacing=8,
                ),

                identity_block,

                ft.Container(width=320, height=1, bgcolor=ft.Colors.GREY_300),

                ft.TextButton(
                    "Logout",
                    icon=ft.Icons.LOGOUT,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        overlay_color=ft.Colors.GREY_200,
                    ),
                    on_click=logout,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.WHITE,
        alignment=ft.alignment.top_center,
    )