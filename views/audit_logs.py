import flet as ft
from datetime import datetime, timedelta
from state.auth_manager import AuthManager

def AuditLogsPage(page: ft.Page, session: dict):
    """
    Audit Log Viewer - Admin only page to view and filter audit logs
    Allows filtering by: actor (username), date range, action type
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
    logs_column = ft.Column(spacing=0)
    
    # Filter controls
    username_filter = ft.TextField(
        label="Filter by username",
        width=200,
        border=ft.InputBorder.UNDERLINE,
        text_size=13,
        on_change=lambda e: refresh_logs(),
    )
    
    action_filter = ft.Dropdown(
        label="Filter by action",
        width=200,
        border=ft.InputBorder.UNDERLINE,
        text_size=13,
        options=[
            ft.dropdown.Option("ALL", "All Actions"),
            ft.dropdown.Option("USER_LOGIN", "User Login"),
            ft.dropdown.Option("USER_REGISTERED", "User Registered"),
            ft.dropdown.Option("USER_CREATED", "User Created (Admin)"),
            ft.dropdown.Option("PROFILE_UPDATE", "Profile Updated"),
            ft.dropdown.Option("PASSWORD_CHANGED", "Password Changed"),
            ft.dropdown.Option("FORCE_PASSWORD_RESET", "Force Password Reset"),
            ft.dropdown.Option("ROLE_CHANGED", "Role Changed"),
            ft.dropdown.Option("USER_DELETED", "User Deleted"),
            ft.dropdown.Option("ACCOUNT_LOCKED", "Account Locked"),
            ft.dropdown.Option("ACCOUNT_UNLOCKED", "Account Unlocked"),
        ],
        value="ALL",
        on_change=lambda e: refresh_logs(),
    )
    
    # Date range filters
    days_back = ft.Dropdown(
        label="Time range",
        width=150,
        border=ft.InputBorder.UNDERLINE,
        text_size=13,
        options=[
            ft.dropdown.Option("1", "Last 24 hours"),
            ft.dropdown.Option("7", "Last 7 days"),
            ft.dropdown.Option("30", "Last 30 days"),
            ft.dropdown.Option("90", "Last 90 days"),
            ft.dropdown.Option("0", "All time"),
        ],
        value="7",
        on_change=lambda e: refresh_logs(),
    )
    
    def get_audit_logs():
        """Fetch and filter audit logs from database"""
        try:
            # Calculate date range
            days = int(days_back.value) if days_back.value != "0" else 999999
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat() if days < 999999 else "1970-01-01T00:00:00"
            
            # Get all audit logs
            all_logs = auth.db.fetch_all("""
                SELECT * FROM audit_logs
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 500
            """, (cutoff_date,))
            
            if not all_logs:
                return []
            
            # Apply filters
            filtered_logs = []
            for log in all_logs:
                # Username filter
                if username_filter.value:
                    log_user = log.get("username") or ""
                    if username_filter.value.lower() not in log_user.lower():
                        continue
                
                # Action filter
                if action_filter.value != "ALL":
                    if log.get("action") != action_filter.value:
                        continue
                
                filtered_logs.append(log)
            
            return filtered_logs
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def format_log_entry(log):
        """Format a log entry for display"""
        try:
            timestamp = datetime.fromisoformat(log.get("timestamp", ""))
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = log.get("timestamp", "Unknown")
        
        username = log.get("username") or "System"
        action = log.get("action", "Unknown")
        table_name = log.get("table_name", "")
        record_id = log.get("record_id")
        new_value = log.get("new_value", "")
        
        # Color code actions
        action_colors = {
            "USER_LOGIN": ft.Colors.BLUE_700,
            "USER_REGISTERED": ft.Colors.GREEN_700,
            "USER_CREATED": ft.Colors.GREEN_700,
            "PASSWORD_CHANGED": ft.Colors.ORANGE_700,
            "FORCE_PASSWORD_RESET": ft.Colors.RED_700,
            "USER_DELETED": ft.Colors.RED_700,
            "ACCOUNT_LOCKED": ft.Colors.RED_700,
            "ACCOUNT_UNLOCKED": ft.Colors.GREEN_700,
            "ROLE_CHANGED": ft.Colors.ORANGE_700,
            "PROFILE_UPDATE": ft.Colors.BLUE_700,
        }
        action_color = action_colors.get(action, ft.Colors.GREY_700)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            # Timestamp
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        time_str,
                                        size=12,
                                        color=ft.Colors.GREY_700,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                expand=1,
                            ),
                            # Username
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        username,
                                        size=12,
                                        color=ft.Colors.GREY_800,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                expand=1,
                            ),
                            # Action
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        action,
                                        size=12,
                                        color=action_color,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                ],
                                expand=1,
                            ),
                            # Details (truncated)
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"{table_name} #{record_id}" if record_id else table_name or "-",
                                        size=11,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                expand=1,
                            ),
                        ],
                        spacing=16,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Details row
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Details: {new_value[:80]}..." if len(new_value or "") > 80 else f"Details: {new_value or 'N/A'}",
                                size=11,
                                color=ft.Colors.GREY_600,
                                italic=True,
                            ),
                        ],
                        spacing=16,
                    ),
                    ft.Container(
                        height=1,
                        bgcolor=ft.Colors.GREY_300,
                        margin=ft.margin.only(top=8, bottom=8),
                    ),
                ],
                spacing=2,
            ),
            padding=ft.padding.symmetric(vertical=8, horizontal=0),
        )
    
    def refresh_logs():
        """Refresh the log display"""
        logs = get_audit_logs()
        logs_column.controls.clear()
        
        if not logs:
            logs_column.controls.append(
                ft.Text("No audit logs found", size=13, color=ft.Colors.GREY_600)
            )
        else:
            for log in logs:
                logs_column.controls.append(format_log_entry(log))
        
        page.update()
    
    def export_logs(e):
        """Export logs as CSV file"""
        logs = get_audit_logs()
        
        # Build CSV content
        csv_content = "Timestamp,Username,Action,Table,Record ID,Details\n"
        for log in logs:
            csv_content += f'"{log.get("timestamp", "")}","{log.get("username", "")}","{log.get("action", "")}","{log.get("table_name", "")}",{log.get("record_id", "")},"{log.get("new_value", "").replace(chr(34), chr(34) + chr(34))}"\n'
        
        # Save to file
        import os
        from datetime import datetime
        
        # Create exports directory
        export_dir = os.path.join(os.getcwd(), "storage", "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename with timestamp
        filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(export_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            status_message.value = f"✓ Exported {len(logs)} logs to: storage/exports/{filename}"
            status_message.color = ft.Colors.GREEN_700
        except Exception as ex:
            status_message.value = f"✗ Export failed: {str(ex)}"
            status_message.color = ft.Colors.RED_700
        
        page.update()
    
    # Initial load
    refresh_logs()
    
    # Stats section
    total_logs = len(get_audit_logs())
    stats_section = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Total Logs (filtered)", size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            ft.Text(str(total_logs), size=24, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=40,
            ),
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
                        ft.Text("Audit Log Viewer", size=24, weight=ft.FontWeight.W_400, color=ft.Colors.GREY_900),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                
                ft.Container(height=24),
                
                # Filters
                ft.Column(
                    controls=[
                        ft.Text("Filters", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
                        ft.Container(height=8),
                        ft.Row(
                            controls=[
                                username_filter,
                                action_filter,
                                days_back,
                                ft.OutlinedButton(
                                    "Export CSV",
                                    icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.GREY_700,
                                        side=ft.BorderSide(1, ft.Colors.GREY_700),
                                    ),
                                    on_click=export_logs,
                                ),
                            ],
                            spacing=16,
                            wrap=True,
                        ),
                    ],
                    spacing=0,
                ),
                
                ft.Container(height=16),
                
                # Stats
                stats_section,
                
                # Status message
                status_message,
                ft.Container(height=8),
                
                # Log list with header
                ft.Column(
                    controls=[
                        # List header
                        ft.Row(
                            controls=[
                                ft.Text("TIMESTAMP", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("USERNAME", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("ACTION", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                                ft.Text("RESOURCE", size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_600, expand=1),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.GREY_400,
                            margin=ft.margin.only(top=8, bottom=8),
                        ),
                        # Logs
                        ft.Container(
                            content=logs_column,
                            expand=True,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        ),
        padding=24,
        expand=True,
        bgcolor=ft.Colors.WHITE,
    )
