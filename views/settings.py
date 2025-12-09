import flet as ft
import os
import shutil
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
    
    # Individual message fields for each section
    profile_message = ft.Text("", size=12)
    password_message = ft.Text("", size=12)
    photo_message = ft.Text("", size=12)
    
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
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_400,
    )
    fullname_field = ft.TextField(
        label="Full Name",
        value=user.full_name or "",
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_400,
    )
    email_field = ft.TextField(
        label="Email",
        value=user.email or "",
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_400,
    )
    
    # Password change fields
    current_password = ft.TextField(
        label="Current Password",
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_300,
    )
    new_password = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_300,
    )
    confirm_password = ft.TextField(
        label="Confirm New Password",
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=12,
        bgcolor=ft.Colors.GREY_50,
        border_color=ft.Colors.GREY_300,
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
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(1, ft.Colors.GREY_300),
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
                            color=ft.Colors.GREY_700,
                            bgcolor=ft.Colors.GREY_200,
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
                bgcolor=ft.Colors.GREY_800 if user.role == "admin" else ft.Colors.GREY_500,
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
                ft.Text("Profile Information", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900),
                ft.Container(width=320, height=1, bgcolor=ft.Colors.GREY_600),
                username_field,
                fullname_field,
                email_field,
                profile_message,
                ft.ElevatedButton(
                    "Save Profile",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_profile,
                    style=ft.ButtonStyle(overlay_color=ft.Colors.GREY_700),
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_600),
        border_radius=12,
        padding=24,
        width=620,
        alignment=ft.alignment.center,
    )

    # Password card - Now 620px wide to match budget card
    password_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Change Password", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_900),
                ft.Container(width=320, height=1, bgcolor=ft.Colors.GREY_600),
                current_password,
                new_password,
                confirm_password,
                password_message,
                ft.ElevatedButton(
                    "Change Password",
                    bgcolor=ft.Colors.GREY_800,
                    color=ft.Colors.WHITE,
                    on_click=save_password,
                    style=ft.ButtonStyle(overlay_color=ft.Colors.GREY_700),
                ),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_600),
        border_radius=12,
        padding=24,
        width=620,
        alignment=ft.alignment.center,
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

                profile_card,
                password_card,

                ft.Container(width=896, height=1, bgcolor=ft.Colors.GREY_300),

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