import flet as ft
from state.auth_manager import AuthManager
from datetime import datetime

def AdminPage(page: ft.Page, session: dict):
    """
    Admin user management page - Minimalist line-based design
    Only accessible by admin role users
    """
    
    # Check if user is admin
    if not session.get("user") or session["user"].role != "admin":
        return ft.Container(
            content=ft.Text(
                "Access Denied - Admin Only",
                size=20,
                color=ft.Colors.RED_700,
            ),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.WHITE,
        )
    
    auth = AuthManager()
    
    # State
    status_message = ft.Text("", size=13, color=ft.Colors.GREEN_700)
    
    # Create Text widgets for stats that we can update
    total_users_text = ft.Text("0", size=28, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900)
    active_users_text = ft.Text("0", size=28, weight=ft.FontWeight.W_400, color=ft.Colors.GREEN_700)
    admin_count_text = ft.Text("0", size=28, weight=ft.FontWeight.W_400, color=ft.Colors.ORANGE_700)
    
    # User list column
    user_list_column = ft.Column(spacing=0)
    
    def load_users():
        """Load all users from database"""
        return auth.db.fetch_all("SELECT * FROM users ORDER BY created_at DESC")
    
    def update_stats(users):
        """Update the statistics displays"""
        total_users_text.value = str(len(users))
        active_users_text.value = str(len([u for u in users if u["is_active"]]))
        admin_count_text.value = str(len([u for u in users if u["role"] == "admin"]))
    
    def refresh_user_list():
        """Refresh the user list display"""
        users = load_users()
        user_rows = []
        
        for i, user in enumerate(users):
            # Role text color
            role_colors = {
                "admin": ft.Colors.ORANGE_700,
                "premium": ft.Colors.BLUE_700,
                "user": ft.Colors.GREY_700,
            }
            
            # Status indicator
            status_color = ft.Colors.GREEN_700 if user["is_active"] else ft.Colors.RED_700
            status_text = "Active" if user["is_active"] else "Disabled"
            
            if user["is_locked"]:
                status_color = ft.Colors.ORANGE_700
                status_text = "Locked"
            
            user_rows.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    # User info
                                    ft.Column(
                                        controls=[
                                            ft.Text(user["username"], size=15, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900),
                                            ft.Text(
                                                user.get("email", "No email") or "No email",
                                                size=12,
                                                color=ft.Colors.GREY_600,
                                            ),
                                        ],
                                        spacing=2,
                                        expand=2,
                                    ),
                                    
                                    # Role
                                    ft.Text(
                                        user["role"].upper(),
                                        size=12,
                                        color=role_colors.get(user["role"], ft.Colors.GREY_700),
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    
                                    # Status
                                    ft.Text(
                                        status_text,
                                        size=12,
                                        color=status_color,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    
                                    # Created date
                                    ft.Text(
                                        f"Joined {user['created_at'][:10]}",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                        expand=1,
                                    ),
                                    
                                    # Action buttons
                                    ft.Row(
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.LOCK_OUTLINE if user["is_active"] else ft.Icons.LOCK_OPEN_OUTLINED,
                                                icon_color=ft.Colors.GREY_700,
                                                icon_size=20,
                                                tooltip="Disable" if user["is_active"] else "Enable",
                                                on_click=lambda e, uid=user["id"]: toggle_user_status(uid),
                                                disabled=(user["id"] == session.get("user_id")),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE_OUTLINE,
                                                icon_color=ft.Colors.RED_700,
                                                icon_size=20,
                                                tooltip="Delete User",
                                                on_click=lambda e, uid=user["id"], uname=user["username"]: confirm_delete_user(uid, uname),
                                                disabled=(user["id"] == session.get("user_id")),
                                            ),
                                        ],
                                        spacing=4,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            # Bottom border line
                            ft.Container(
                                height=1,
                                bgcolor=ft.Colors.GREY_300,
                                margin=ft.margin.only(top=12),
                            ) if i < len(users) - 1 else ft.Container(),
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(vertical=12, horizontal=0),
                )
            )
        
        user_list_column.controls = user_rows
        update_stats(users)
        page.update()
    
    def toggle_user_status(user_id):
        """Enable/disable user account"""
        user = auth.db.get_by_id("users", user_id)
        if not user:
            return
        
        new_status = 0 if user["is_active"] else 1
        
        auth.db.update(
            "users",
            {
                "is_active": new_status,
                "updated_at": datetime.now().isoformat()
            },
            "id = ?",
            (user_id,)
        )
        
        # Log action
        auth._log_audit(
            session.get("user_id"),
            "USER_STATUS_CHANGED",
            "users",
            user_id,
            old_value=str(user["is_active"]),
            new_value=str(new_status)
        )
        
        status_message.value = f"User {'enabled' if new_status else 'disabled'} successfully"
        status_message.color = ft.Colors.GREEN_700
        refresh_user_list()
    
    def confirm_delete_user(user_id, username):
        """Show confirmation dialog before deleting user"""
        def delete_confirmed(e):
            # Delete user
            auth.db.delete("users", "id = ?", (user_id,))
            
            # Log action
            auth._log_audit(
                session.get("user_id"),
                "USER_DELETED",
                "users",
                user_id,
                old_value=username
            )
            
            dialog.open = False
            page.update()
            
            status_message.value = f"User '{username}' deleted successfully"
            status_message.color = ft.Colors.GREEN_700
            refresh_user_list()
        
        def cancel_delete(e):
            dialog.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete", weight=ft.FontWeight.W_500, size=18),
            content=ft.Text(
                f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.",
                size=14,
                color=ft.Colors.GREY_700,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_delete,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_700),
                ),
                ft.OutlinedButton(
                    "Delete",
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED_700,
                        side=ft.BorderSide(1, ft.Colors.RED_700),
                    ),
                    on_click=delete_confirmed,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
    def show_create_user_dialog(e):
        """Show dialog to create new user"""
        username_field = ft.TextField(
            label="Username",
            width=320,
            border=ft.InputBorder.UNDERLINE,
            text_size=14,
        )
        password_field = ft.TextField(
            label="Password",
            password=True,
            width=320,
            border=ft.InputBorder.UNDERLINE,
            text_size=14,
        )
        email_field = ft.TextField(
            label="Email (optional)",
            width=320,
            border=ft.InputBorder.UNDERLINE,
            text_size=14,
        )
        role_dropdown = ft.Dropdown(
            label="Role",
            width=320,
            border=ft.InputBorder.UNDERLINE,
            text_size=14,
            options=[
                ft.dropdown.Option("user", "Regular User"),
                ft.dropdown.Option("premium", "Premium User"),
                ft.dropdown.Option("admin", "Administrator"),
            ],
            value="user",
        )
        error_text = ft.Text("", color=ft.Colors.RED_700, size=12)
        
        def create_user_confirmed(e):
            error_text.value = ""
            
            if not username_field.value or not password_field.value:
                error_text.value = "Username and password are required"
                page.update()
                return
            
            success, msg, user = auth.register_user(
                username=username_field.value,
                password=password_field.value,
                email=email_field.value or None,
                role=role_dropdown.value,
            )
            
            if success:
                auth._log_audit(
                    session.get("user_id"),
                    "USER_CREATED",
                    "users",
                    user.id,
                    new_value=f"Created user: {username_field.value} with role: {role_dropdown.value}"
                )
                
                dialog.open = False
                page.update()
                
                status_message.value = msg
                status_message.color = ft.Colors.GREEN_700
                refresh_user_list()
            else:
                error_text.value = msg
                page.update()
        
        def cancel_create(e):
            dialog.open = False
            page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Create New User", weight=ft.FontWeight.W_500, size=18),
            content=ft.Column(
                controls=[
                    username_field,
                    ft.Container(height=8),
                    password_field,
                    ft.Container(height=8),
                    email_field,
                    ft.Container(height=8),
                    role_dropdown,
                    ft.Container(height=12),
                    error_text,
                ],
                tight=True,
                spacing=0,
                width=320,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_create,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_700),
                ),
                ft.OutlinedButton(
                    "Create User",
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_900,
                        side=ft.BorderSide(1, ft.Colors.GREY_900),
                    ),
                    on_click=create_user_confirmed,
                ),
            ],
        )
        
        page.open(dialog)
        page.update()
    
    # Initial load
    refresh_user_list()
    
    # Stats section with underlines
    stats_section = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    # Total Users
                    ft.Column(
                        controls=[
                            ft.Text("Total Users", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            total_users_text,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    # Active Users
                    ft.Column(
                        controls=[
                            ft.Text("Active", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            active_users_text,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    # Admins
                    ft.Column(
                        controls=[
                            ft.Text("Admins", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            admin_count_text,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=40,
            ),
            # Underline
            ft.Container(
                height=1,
                bgcolor=ft.Colors.GREY_300,
                margin=ft.margin.only(top=16, bottom=16),
            ),
        ],
        spacing=0,
    )
    
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.Text("User Management", size=24, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                        ft.OutlinedButton(
                            "Create User",
                            icon=ft.Icons.PERSON_ADD_OUTLINED,
                            style=ft.ButtonStyle(
                                color=ft.Colors.GREY_900,
                                side=ft.BorderSide(1, ft.Colors.GREY_800),
                            ),
                            on_click=show_create_user_dialog,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                
                ft.Container(height=24),
                
                # Stats cards
                stats_section,
                
                # Status message
                status_message,
                
                ft.Container(height=8),
                
                # User list with header
                ft.Column(
                    controls=[
                        # List header
                        ft.Row(
                            controls=[
                                ft.Text("USERNAME", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=2),
                                ft.Text("ROLE", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                                ft.Text("STATUS", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                                ft.Text("JOINED", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("ACTIONS", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_400,
                            margin=ft.margin.only(top=8, bottom=8),
                        ),
                        # User list
                        ft.Container(
                            content=ft.Column(
                                controls=[user_list_column],
                                scroll=ft.ScrollMode.AUTO,
                            ),
                            expand=True,
                        ),
                    ],
                    spacing=0,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.WHITE,
    )