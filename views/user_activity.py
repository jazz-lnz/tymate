import flet as ft
from datetime import datetime, timedelta
from state.auth_manager import AuthManager

def UserActivityPage(page: ft.Page, session: dict):
    """
    User Activity Monitor - Admin page showing:
    - Last login for each user
    - Failed login attempts
    - Account lock status
    - Login history with IP addresses
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
    users_activity_column = ft.Column(spacing=0)
    login_history_column = ft.Column(spacing=0)
    selected_user_username = ft.Text("", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900)
    
    # Filter
    days_filter = ft.Dropdown(
        label="Activity period",
        width=150,
        border=ft.InputBorder.UNDERLINE,
        text_size=13,
        options=[
            ft.dropdown.Option("1", "Last 24 hours"),
            ft.dropdown.Option("7", "Last 7 days"),
            ft.dropdown.Option("30", "Last 30 days"),
            ft.dropdown.Option("90", "Last 90 days"),
        ],
        value="30",
        on_change=lambda e: refresh_activity(),
    )
    
    def get_user_activity():
        """Get activity status for all users"""
        try:
            users = auth.db.fetch_all("""
                SELECT id, username, is_active, is_locked, failed_login_attempts, 
                       last_login, created_at
                FROM users
                ORDER BY last_login DESC NULLS LAST
            """)
            
            return users or []
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
    
    def get_login_history(username: str):
        """Get login attempt history for a specific user"""
        try:
            days = int(days_filter.value)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            history = auth.db.fetch_all("""
                SELECT * FROM login_attempts
                WHERE username = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (username, cutoff_date))
            
            return history or []
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
    
    def format_last_login(last_login_str: str) -> str:
        """Format last login timestamp to human readable"""
        if not last_login_str:
            return "Never"
        
        try:
            last_login = datetime.fromisoformat(last_login_str)
            now = datetime.now()
            diff = now - last_login
            
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    minutes = diff.seconds // 60
                    return f"{minutes}m ago"
                return f"{hours}h ago"
            elif diff.days == 1:
                return "1d ago"
            elif diff.days < 30:
                return f"{diff.days}d ago"
            else:
                return last_login.strftime("%Y-%m-%d")
        except:
            return last_login_str
    
    def show_user_history(username: str, e=None):
        """Show login history for selected user"""
        selected_user_username.value = f"Activity: {username}"
        
        history = get_login_history(username)
        login_history_column.controls.clear()
        
        if not history:
            login_history_column.controls.append(
                ft.Text("No login attempts found", size=13, color=ft.Colors.GREY_600)
            )
        else:
            for attempt in history:
                success = bool(attempt.get("success"))
                reason = attempt.get("failure_reason", "")
                ip = attempt.get("ip_address", "Unknown IP")
                timestamp = attempt.get("timestamp", "")
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
                
                status_color = ft.Colors.GREEN_700 if success else ft.Colors.RED_700
                status_text = "✓ Success" if success else f"✗ Failed: {reason or 'Unknown'}"
                
                login_history_column.controls.extend([
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            time_str,
                                            size=12,
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                    expand=1,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            status_text,
                                            size=12,
                                            color=status_color,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                    ],
                                    expand=1,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            ip,
                                            size=11,
                                            color=ft.Colors.GREY_600,
                                        ),
                                    ],
                                    expand=1,
                                ),
                            ],
                            spacing=16,
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                    ),
                    ft.Container(
                        height=1,
                        bgcolor=ft.Colors.GREY_300,
                    ),
                ])
        
        page.update()
    
    def refresh_activity():
        """Refresh the activity display"""
        users = get_user_activity()
        users_activity_column.controls.clear()
        
        if not users:
            users_activity_column.controls.append(
                ft.Text("No users found", size=13, color=ft.Colors.GREY_600)
            )
        else:
            for user in users:
                username = user.get("username", "Unknown")
                is_active = bool(user.get("is_active"))
                is_locked = bool(user.get("is_locked"))
                failed_attempts = user.get("failed_login_attempts", 0)
                last_login = format_last_login(user.get("last_login"))
                created_at = user.get("created_at", "")
                
                # Status indicators
                if is_locked:
                    status_color = ft.Colors.RED_700
                    status_text = "🔒 Locked"
                elif not is_active:
                    status_color = ft.Colors.ORANGE_700
                    status_text = "🚫 Disabled"
                else:
                    status_color = ft.Colors.GREEN_700
                    status_text = "✓ Active"
                
                # Failed attempts warning (current counter - resets to 0 on successful login)
                # Check recent login history for failed attempts
                recent_failures = auth.db.fetch_one("""
                    SELECT COUNT(*) as count FROM login_attempts
                    WHERE username = ? AND success = 0 
                    AND timestamp >= datetime('now', '-7 days')
                """, (username,))
                
                recent_fail_count = recent_failures.get("count", 0) if recent_failures else 0
                
                if failed_attempts > 0:
                    # Currently failing (before successful login)
                    attempts_color = ft.Colors.RED_700
                    attempts_text = f"🚨 {failed_attempts} consecutive failed"
                elif recent_fail_count > 0:
                    # Had failures in last 7 days but successfully logged in since
                    attempts_color = ft.Colors.ORANGE_700
                    attempts_text = f"⚠ {recent_fail_count} failed (7d)"
                else:
                    attempts_color = ft.Colors.GREEN_700
                    attempts_text = "✓ Clean record"
                
                users_activity_column.controls.extend([
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        # User info
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    username,
                                                    size=14,
                                                    weight=ft.FontWeight.W_500,
                                                    color=ft.Colors.GREY_900,
                                                ),
                                                ft.Text(
                                                    f"Member since {datetime.fromisoformat(created_at).strftime('%Y-%m-%d') if created_at else 'Unknown'}",
                                                    size=11,
                                                    color=ft.Colors.GREY_600,
                                                ),
                                            ],
                                            spacing=2,
                                            expand=2,
                                        ),
                                        # Status
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    status_text,
                                                    size=12,
                                                    color=status_color,
                                                    weight=ft.FontWeight.W_600,
                                                ),
                                            ],
                                            expand=1,
                                        ),
                                        # Last login
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Last Login",
                                                    size=10,
                                                    color=ft.Colors.GREY_600,
                                                    weight=ft.FontWeight.W_500,
                                                ),
                                                ft.Text(
                                                    last_login,
                                                    size=12,
                                                    color=ft.Colors.GREY_800,
                                                ),
                                            ],
                                            expand=1,
                                        ),
                                        # Failed attempts
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "Auth Status",
                                                    size=10,
                                                    color=ft.Colors.GREY_600,
                                                    weight=ft.FontWeight.W_500,
                                                ),
                                                ft.Text(
                                                    attempts_text,
                                                    size=12,
                                                    color=attempts_color,
                                                ),
                                            ],
                                            expand=1,
                                        ),
                                        # View history button
                                        ft.IconButton(
                                            icon=ft.Icons.HISTORY_OUTLINED,
                                            icon_size=18,
                                            icon_color=ft.Colors.GREY_700,
                                            on_click=lambda e, u=username: show_user_history(u),
                                        ),
                                    ],
                                    spacing=16,
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ],
                            spacing=0,
                        ),
                        padding=ft.padding.symmetric(vertical=12, horizontal=0),
                    ),
                    ft.Container(
                        height=1,
                        bgcolor=ft.Colors.GREY_300,
                    ),
                ])
        
        page.update()
    
    # Initial load
    refresh_activity()
    
    # Summary stats
    users = get_user_activity()
    active_count = len([u for u in users if u.get("is_active")])
    locked_count = len([u for u in users if u.get("is_locked")])
    failed_count = len([u for u in users if u.get("failed_login_attempts", 0) > 0])
    
    return ft.Container(
        content=ft.Row(
            controls=[
                # Left panel: User list
                ft.Column(
                    controls=[
                        # Header
                        ft.Row(
                            controls=[
                                ft.Text("User Activity Monitor", size=24, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                            ],
                        ),
                        
                        ft.Container(height=16),
                        
                        # Stats
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Total Users", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                        ft.Container(height=4),
                                        ft.Text(str(len(users)), size=20, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                                    ],
                                    spacing=0,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Active", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                        ft.Container(height=4),
                                        ft.Text(str(active_count), size=20, weight=ft.FontWeight.W_400, color=ft.Colors.GREEN_700),
                                    ],
                                    spacing=0,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Locked", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                        ft.Container(height=4),
                                        ft.Text(str(locked_count), size=20, weight=ft.FontWeight.W_400, color=ft.Colors.RED_700),
                                    ],
                                    spacing=0,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Failed Auth", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                                        ft.Container(height=4),
                                        ft.Text(str(failed_count), size=20, weight=ft.FontWeight.W_400, color=ft.Colors.ORANGE_700),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            spacing=32,
                        ),
                        
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_300,
                            margin=ft.margin.only(top=16, bottom=16),
                        ),
                        
                        # User list
                        ft.Container(
                            content=users_activity_column,
                            expand=True,
                        ),
                    ],
                    expand=1,
                    spacing=0,
                ),
                
                # Divider
                ft.VerticalDivider(color=ft.Colors.GREY_300, width=1),
                
                # Right panel: Login history
                ft.Column(
                    controls=[
                        # Header
                        selected_user_username,
                        
                        ft.Container(height=8),
                        
                        # Time filter
                        days_filter,
                        
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_300,
                            margin=ft.margin.only(top=12, bottom=12),
                        ),
                        
                        # History list header
                        ft.Row(
                            controls=[
                                ft.Text("TIMESTAMP", size=10, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("STATUS", size=10, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("IP ADDRESS", size=10, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                            ],
                            spacing=16,
                        ),
                        
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_300,
                            margin=ft.margin.only(top=8, bottom=8),
                        ),
                        
                        # History list
                        ft.Container(
                            content=login_history_column,
                            expand=True,
                        ),
                    ],
                    expand=1,
                    spacing=0,
                    width=400,
                ),
            ],
            spacing=0,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.WHITE,
    )
