import flet as ft
import os
import shutil
import time
import threading
from pathlib import Path
from state.auth_manager import AuthManager

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
    panel_bg = "#FFFFFF"
    soft_panel_bg = "#EDF2FA"
    border_color = "#B7C4D8"
    title_color = "#23211E"
    accent_color = "#6E7889"
    drop_shadow = ft.BoxShadow(
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
        offset=ft.Offset(0, 2),
    )
    window_width = page.window.width or 430
    is_mobile = window_width < 900
    card_width = max(320, min(760, window_width - 48))
    field_width = max(250, min(420, card_width - 56))
    
    # Individual message fields for each section
    profile_message = ft.Text("", size=12)
    password_message = ft.Text("", size=12)
    photo_message = ft.Text("", size=12)

    status_message = ft.Text(
        "",
        size=14,
        weight=ft.FontWeight.W_500,
        visible=False,
    )
    message_hide_seconds = 6
    message_sequence = {"value": 0}

    def show_message(text: str, msg_type: str = "info"):
        color_map = {
            "success": ft.Colors.GREEN_700,
            "error": ft.Colors.RED_700,
            "warning": ft.Colors.ORANGE_700,
            "info": ft.Colors.BLUE_700,
        }
        message_sequence["value"] += 1
        current_seq = message_sequence["value"]
        status_message.value = text
        status_message.color = color_map.get(msg_type, ft.Colors.BLUE_700)
        status_message.visible = True
        try:
            status_message.update()
        except (AssertionError, AttributeError):
            pass

        def hide_message(seq):
            time.sleep(message_hide_seconds)
            try:
                if message_sequence["value"] != seq:
                    return
                status_message.visible = False
                status_message.update()
            except (AssertionError, AttributeError):
                pass

        threading.Thread(target=hide_message, args=(current_seq,), daemon=True).start()
    
    # Store original values for change detection
    original_values = {
        "username": user.username or "",
        "email": user.email or "",
        "full_name": user.full_name or "",
    }
    
    # Profile fields with cleaner styling
    username_field = ft.TextField(
        label="Username",
        value=user.username or "",
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    fullname_field = ft.TextField(
        label="Full Name",
        value=user.full_name or "",
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    email_field = ft.TextField(
        label="Email",
        value=user.email or "",
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    
    # Password change fields
    current_password = ft.TextField(
        label="Current Password",
        password=True,
        can_reveal_password=True,
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    new_password = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    confirm_password = ft.TextField(
        label="Confirm New Password",
        password=True,
        can_reveal_password=True,
        width=field_width,
        border_radius=12,
        bgcolor=panel_bg,
        border_color=border_color,
    )
    
    def save_profile(e):
        """Save profile changes"""
        profile_message.value = ""
        
        # Check if anything changed
        username_changed = (username_field.value or "") != original_values["username"]
        email_changed = (email_field.value or "") != original_values["email"]
        fullname_changed = (fullname_field.value or "") != original_values["full_name"]
        
        if not username_changed and not email_changed and not fullname_changed:
            profile_message.value = "No changes detected"
            profile_message.color = ft.Colors.GREY_600
            page.update()
            return
        
        success, msg = auth.update_user_profile(
            user.id,
            username=username_field.value or None,
            email=email_field.value or None,
            full_name=fullname_field.value or None,
        )
        
        if success:
            # Update session and original values
            user.username = username_field.value
            user.email = email_field.value
            user.full_name = fullname_field.value
            original_values["username"] = username_field.value or ""
            original_values["email"] = email_field.value or ""
            original_values["full_name"] = fullname_field.value or ""
            
            profile_message.value = "Profile updated successfully!"
            profile_message.color = ft.Colors.GREEN_600
        else:
            profile_message.value = f"{msg}"
            profile_message.color = ft.Colors.RED_400
        
        page.update()
    
    def save_password(e):
        """Change password"""
        password_message.value = ""
        
        # Validate
        if not current_password.value or not new_password.value:
            password_message.value = "All password fields are required"
            password_message.color = ft.Colors.RED_400
            page.update()
            return
        
        if new_password.value != confirm_password.value:
            password_message.value = "New passwords don't match"
            password_message.color = ft.Colors.RED_400
            page.update()
            return
        
        if len(new_password.value) < 6:
            password_message.value = "Password must be at least 6 characters"
            password_message.color = ft.Colors.RED_400
            page.update()
            return
        
        success, msg = auth.change_password(
            user.id,
            current_password.value,
            new_password.value,
        )
        
        if success:
            password_message.value = "Password changed successfully!"
            password_message.color = ft.Colors.GREEN_600
            
            # Clear fields
            current_password.value = ""
            new_password.value = ""
            confirm_password.value = ""
        else:
            password_message.value = f"{msg}"
            password_message.color = ft.Colors.RED_400
        
        page.update()
    
    def validate_image_file(file_path: str) -> tuple[bool, str]:
        """
        Validate uploaded image file
        
        Args:
            file_path: Path to uploaded file
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check if file exists
        if not os.path.exists(file_path):
            return False, "File not found"
        
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        if file_ext not in allowed_extensions:
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        
        # Check file size (max 5MB)
        file_size = os.path.getsize(file_path)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        
        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large ({size_mb:.1f}MB). Max size: 5MB"
        
        return True, ""
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        photo_message.value = ""
        
        if not e.files or len(e.files) == 0:
            return
        
        selected_file = e.files[0]
        file_path = selected_file.path
        
        # Validate the image
        is_valid, error_msg = validate_image_file(file_path)
        
        if not is_valid:
            photo_message.value = error_msg
            photo_message.color = ft.Colors.RED_400
            page.update()
            return
        
        try:
            # Create profile photos directory if it doesn't exist
            photos_dir = Path("data/profile_photos")
            photos_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename: user_id + original extension
            file_ext = Path(file_path).suffix
            new_filename = f"user_{user.id}{file_ext}"
            dest_path = photos_dir / new_filename
            
            # Copy file to destination
            shutil.copy2(file_path, dest_path)
            
            # Update database with relative path
            profile_photo_path = f"data/profile_photos/{new_filename}"
            success, msg = auth.update_user_profile(
                user.id,
                profile_photo=profile_photo_path
            )
            
            if success:
                # Update user object and avatar display
                user.profile_photo = profile_photo_path
                
                # Update avatar to show new image
                if os.path.exists(profile_photo_path):
                    avatar_placeholder.content = ft.Image(
                        src=profile_photo_path,
                        width=96,
                        height=96,
                        fit=ft.ImageFit.COVER,
                        border_radius=48,
                    )
                
                photo_message.value = "Profile picture updated!"
                photo_message.color = ft.Colors.GREEN_600
            else:
                photo_message.value = f"Failed to update: {msg}"
                photo_message.color = ft.Colors.RED_400
                
        except Exception as ex:
            photo_message.value = f"Upload failed: {str(ex)}"
            photo_message.color = ft.Colors.RED_400
        
        page.update()
    
    def remove_profile_photo(e):
        """Remove profile photo"""
        photo_message.value = ""
        
        try:
            # Remove from database
            success, msg = auth.update_user_profile(
                user.id,
                profile_photo=None
            )
            
            if success:
                # Update user object
                old_photo_path = user.profile_photo
                user.profile_photo = None
                
                # Delete file if it exists
                if old_photo_path and os.path.exists(old_photo_path):
                    try:
                        os.remove(old_photo_path)
                    except:
                        pass  # File deletion is optional
                
                # Reset avatar to default icon
                avatar_placeholder.content = ft.Icon(
                    ft.Icons.PERSON, 
                    size=48, 
                    color=ft.Colors.GREY_600
                )
                
                photo_message.value = "Profile picture removed"
                photo_message.color = ft.Colors.GREY_600
            else:
                photo_message.value = f"Failed to remove: {msg}"
                photo_message.color = ft.Colors.RED_400
                
        except Exception as ex:
            photo_message.value = f"Removal failed: {str(ex)}"
            photo_message.color = ft.Colors.RED_400
        
        page.update()
    
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

    def go_to(route: str):
        page.route = route
        route_change = session.get("route_change") if session else None
        if callable(route_change):
            route_change(route)

    def open_onboarding_editor(e):
        if session is not None:
            session["onboarding_edit_mode"] = True
            session["onboarding_return_route"] = "/settings"
        go_to("/onboarding")
    
    # File picker for profile photo
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    
    # Avatar placeholder with profile photo if exists
    avatar_content = ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.GREY_600)
    
    if user.profile_photo and os.path.exists(user.profile_photo):
        avatar_content = ft.Image(
            src=user.profile_photo,
            width=96,
            height=96,
            fit=ft.ImageFit.COVER,
            border_radius=48,
        )
    
    avatar_placeholder = ft.Container(
        width=96,
        height=96,
        bgcolor=soft_panel_bg,
        border=ft.border.all(1.5, border_color),
        border_radius=48,
        alignment=ft.alignment.center,
        content=avatar_content,
    )

    # Top identity block (centered)
    identity_block = ft.Column(
        controls=[
            avatar_placeholder,
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.PHOTO_CAMERA,
                        tooltip="Upload Photo",
                        icon_size=20,
                        on_click=lambda _: file_picker.pick_files(
                            allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"],
                            dialog_title="Select Profile Picture"
                        ),
                        style=ft.ButtonStyle(
                            color=title_color,
                            bgcolor=soft_panel_bg,
                            side=ft.BorderSide(1, border_color),
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Remove Photo",
                        icon_size=20,
                        on_click=remove_profile_photo,
                        style=ft.ButtonStyle(
                            color=ft.Colors.RED_700,
                            bgcolor=ft.Colors.RED_50,
                        ),
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            photo_message,
            ft.Text(user.username, size=20, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_900),
            ft.Container(
                content=ft.Text(
                    user.role.upper(),
                    size=12,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.W_600,
                ),
                bgcolor=accent_color,
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                border_radius=12,
            ),
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Profile card (editable fields) - Now 620px wide to match budget card
    profile_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Profile Information", size=18, weight=ft.FontWeight.W_500, color=title_color),
                ft.Container(width=field_width, height=1, bgcolor=border_color),
                username_field,
                fullname_field,
                email_field,
                profile_message,
                ft.ElevatedButton(
                    "Save Profile",
                    bgcolor=accent_color,
                    color=ft.Colors.WHITE,
                    on_click=save_profile,
                    style=ft.ButtonStyle(
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        side=ft.BorderSide(1, border_color),
                    ),
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=panel_bg,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        padding=24,
        width=card_width,
        shadow=drop_shadow,
        alignment=ft.alignment.center,
    )

    # Password card - Now 620px wide to match budget card
    password_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Change Password", size=18, weight=ft.FontWeight.W_500, color=title_color),
                ft.Container(width=field_width, height=1, bgcolor=border_color),
                current_password,
                new_password,
                confirm_password,
                password_message,
                ft.ElevatedButton(
                    "Change Password",
                    bgcolor=accent_color,
                    color=ft.Colors.WHITE,
                    on_click=save_password,
                    style=ft.ButtonStyle(
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        side=ft.BorderSide(1, border_color),
                    ),
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=panel_bg,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        padding=24,
        width=card_width,
        shadow=drop_shadow,
        alignment=ft.alignment.center,
    )

    current_sleep_hours = getattr(user, "sleep_hours", 8.0) or 8.0
    current_wake_time = getattr(user, "wake_time", "07:00") or "07:00"

    onboarding_preview = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Current setup", size=12, color=accent_color, weight=ft.FontWeight.W_600),
                ft.Row(
                    controls=[
                        ft.Text("Sleep", size=12, color=title_color),
                        ft.Container(expand=True),
                        ft.Text(f"{current_sleep_hours:g} hours", size=12, color=title_color, weight=ft.FontWeight.W_500),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("Wake time", size=12, color=title_color),
                        ft.Container(expand=True),
                        ft.Text(str(current_wake_time), size=12, color=title_color, weight=ft.FontWeight.W_500),
                    ],
                ),
            ],
            spacing=8,
        ),
        width=field_width,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=soft_panel_bg,
        border=ft.border.all(1, border_color),
        border_radius=10,
    )

    onboarding_details_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Onboarding Details", size=18, weight=ft.FontWeight.W_500, color=title_color),
                ft.Container(width=field_width, height=1, bgcolor=border_color),
                ft.Text(
                    "Need to revise your onboarding inputs? Reopen the onboarding flow with your current values prefilled.",
                    size=12,
                    color=accent_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                onboarding_preview,
                ft.ElevatedButton(
                    "Update Onboarding Details",
                    bgcolor=accent_color,
                    color=ft.Colors.WHITE,
                    on_click=open_onboarding_editor,
                    style=ft.ButtonStyle(
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        side=ft.BorderSide(1, border_color),
                    ),
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=panel_bg,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        padding=24,
        width=card_width,
        shadow=drop_shadow,
        alignment=ft.alignment.center,
    )

    settings_flash_message = ""
    if session and session.get("settings_flash_success"):
        settings_flash_message = session.pop("settings_flash_success")

    if settings_flash_message:
        show_message(settings_flash_message, "success")

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=28, color=accent_color),
                        ft.Text("Settings", size=24 if is_mobile else 28, weight=ft.FontWeight.W_500, color=title_color),
                    ],
                    spacing=8,
                ),
                status_message,

                identity_block,

                profile_card,
                password_card,
                onboarding_details_card,

                ft.Container(width=card_width, height=1, bgcolor=border_color),

                ft.TextButton(
                    "Logout",
                    icon=ft.Icons.LOGOUT,
                    style=ft.ButtonStyle(
                        color=title_color,
                        overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    ),
                    on_click=logout,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(left=24, right=24, top=66, bottom=24),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#DDE9FB", "#FFFFFF"],
        ),
        alignment=ft.alignment.top_center,
    )