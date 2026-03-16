import flet as ft
from state.auth_manager import AuthManager

def LoginPage(page: ft.Page, session: dict):
    """
    Login and Signup page - Minimalist line-based design
    
    Args:
        page: Flet page
        session: Session dictionary to store user data
    """
    
    auth = AuthManager()
    panel_bg = "#FFFFFF"
    border_color = "#B7C4D8"
    title_color = "#23211E"
    accent_color = "#6E7889"
    soft_panel_bg = "#EDF2FA"
    page_bg_top = "#DDE9FB"
    page_bg_bottom = "#FFFFFF"
    drop_shadow = ft.BoxShadow(
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
        offset=ft.Offset(0, 2),
    )
    window_width = page.window.width or 430
    is_mobile = window_width < 700
    form_width = max(300, min(460, window_width - (32 if is_mobile else 80)))
    
    # Track if we're in login or signup mode
    is_signup_mode = False
    
    # Form fields with underline-only borders
    username_field = ft.TextField(
        hint_text="Username",
        width=form_width,
        border=ft.InputBorder.UNDERLINE,
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        text_size=15,
        border_color=border_color,
        on_submit=lambda e: submit_current_mode(e),
        autofocus=True,
    )
    
    password_field = ft.TextField(
        hint_text="Password",
        password=True,
        can_reveal_password=True,
        width=form_width,
        border=ft.InputBorder.UNDERLINE,
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        text_size=15,
        border_color=border_color,
        on_submit=lambda e: submit_current_mode(e),
    )
    
    email_field = ft.TextField(
        hint_text="Email (optional)",
        width=form_width,
        border=ft.InputBorder.UNDERLINE,
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        text_size=15,
        border_color=border_color,
        visible=False,
        on_submit=lambda e: submit_current_mode(e),
    )
    
    fullname_field = ft.TextField(
        hint_text="Full Name (optional)",
        width=form_width,
        border=ft.InputBorder.UNDERLINE,
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        text_size=15,
        border_color=border_color,
        visible=False,
        on_submit=lambda e: submit_current_mode(e),
    )
    
    error_message = ft.Text("", color=ft.Colors.RED_700, size=13, text_align=ft.TextAlign.CENTER)
    success_message = ft.Text("", color=ft.Colors.GREEN_700, size=13, text_align=ft.TextAlign.CENTER)
    
    submit_button = ft.ElevatedButton(
        "Login",
        width=220 if is_mobile else 240,
        height=42,
        style=ft.ButtonStyle(
            bgcolor=accent_color,
            color=ft.Colors.WHITE,
            side=ft.BorderSide(1, border_color),
            overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
    )
    
    mode_title = ft.Text("Login", size=30 if is_mobile else 34, weight=ft.FontWeight.W_500, color=title_color)
    
    loading_indicator = ft.ProgressRing(visible=False, width=20, height=20, color=ft.Colors.GREY_800)
    
    def handle_login(e):
        """Handle login button click"""
        username = username_field.value
        password = password_field.value
        
        # Clear messages
        error_message.value = ""
        success_message.value = ""
        
        # Validate
        if not username or not password:
            error_message.value = "Please enter username and password"
            page.update()
            return
        
        # Show loading
        loading_indicator.visible = True
        submit_button.disabled = True
        page.update()
        
        # Attempt login
        success, msg, user, token = auth.login(username, password)
        
        # Hide loading
        loading_indicator.visible = False
        submit_button.disabled = False
        
        if success:
            # Save to session
            session["user"] = user
            session["token"] = token
            session["user_id"] = user.id

            # Check if user is admin - admins skip onboarding
            if user.role == "admin":
                session["onboarding_completed"] = True
                success_message.value = "Welcome, admin! Redirecting..."
                page.update()
                
                import time
                time.sleep(1)
                
                page.route = "/admin"
                page.update()
            # Check if regular user has completed onboarding
            elif user.study_goal_hours_per_day > 0:
                session["onboarding_completed"] = True
                success_message.value = "Login successful! Redirecting..."
                page.update()
                
                import time
                time.sleep(1)
                
                page.route = "/dashboard"
                page.update()
            else:
                session["onboarding_completed"] = False
                success_message.value = "Please complete your profile setup..."
                page.update()
                
                import time
                time.sleep(1)
                
                page.route = "/onboarding"
                page.update()
        else:
            error_message.value = msg
            page.update()

    def submit_current_mode(e):
        """Submit the active form when Enter is pressed."""
        if is_signup_mode:
            handle_signup(e)
        else:
            handle_login(e)
    
    def handle_signup(e):
        """Handle signup button click"""
        username = username_field.value
        password = password_field.value
        email = email_field.value if email_field.value else None
        fullname = fullname_field.value if fullname_field.value else None
        
        # Clear messages
        error_message.value = ""
        success_message.value = ""
        
        # Validate
        if not username or not password:
            error_message.value = "Username and password are required"
            page.update()
            return
        
        # Show loading
        loading_indicator.visible = True
        submit_button.disabled = True
        page.update()
        
        # Attempt registration
        success, msg, user = auth.register_user(
            username=username,
            password=password,
            email=email,
            full_name=fullname,
        )
        
        # Hide loading
        loading_indicator.visible = False
        submit_button.disabled = False
        
        if success:
            success_message.value = f"{msg} Now completing your setup..."
            page.update()
            
            # Auto-login after signup
            success_login, msg_login, user_login, token = auth.login(username, password)
            
            if success_login:
                session["user"] = user_login
                session["token"] = token
                session["user_id"] = user_login.id
                session["onboarding_completed"] = False
                
                import time
                time.sleep(1)
                
                page.route = "/onboarding"
                page.update()
        else:
            error_message.value = msg
            page.update()
    
    def toggle_mode(e):
        """Switch between login and signup mode"""
        nonlocal is_signup_mode
        is_signup_mode = not is_signup_mode
        
        # Clear fields and messages
        username_field.value = ""
        password_field.value = ""
        email_field.value = ""
        fullname_field.value = ""
        error_message.value = ""
        success_message.value = ""
        
        if is_signup_mode:
            # Switch to signup mode
            mode_title.value = "Sign Up"
            submit_button.text = "Create Account"
            submit_button.on_click = handle_signup
            email_field.visible = True
            fullname_field.visible = True
        else:
            # Switch to login mode
            mode_title.value = "Login"
            submit_button.text = "Login"
            submit_button.on_click = handle_login
            email_field.visible = False
            fullname_field.visible = False
        
        page.update()
    
    # Set initial button handlers
    submit_button.on_click = handle_login
    
    # Minimalist logo at top
    logo = ft.Row(
        controls=[
            ft.Icon(ft.Icons.TIMER_OUTLINED, size=28, color=accent_color),
            ft.Text("Tymate", size=24, weight=ft.FontWeight.W_500, color=title_color),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )

    # Tagline
    tagline = ft.Text(
        "Loaded with tasks? Time it with Tymate.",
        size=14,
        color=accent_color,
        text_align=ft.TextAlign.CENTER,
        italic=True,
    )

    # Login/Signup form
    login_form = ft.Column(
        controls=[
            logo,
            ft.Container(height=8),
            tagline,
            ft.Container(height=32),
            mode_title,
            ft.Container(height=24),
            username_field,
            ft.Container(height=16),
            password_field,
            ft.Container(height=16),
            email_field,
            ft.Container(height=16, visible=False, data="email_spacer"),
            fullname_field,
            ft.Container(height=24),
            error_message,
            success_message,
            ft.Container(height=8),
            ft.Row(
                controls=[submit_button, loading_indicator],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )

    # Horizontal divider line
    divider = ft.Container(
        width=form_width,
        height=1,
        bgcolor=border_color,
    )

    # Toggle link
    toggle_link = ft.Row(
        controls=[
            ft.Text(
                "Don't have an account?",
                size=13,
                color=accent_color,
            ),
            ft.TextButton(
                "Sign up here",
                on_click=toggle_mode,
                style=ft.ButtonStyle(
                    color=title_color,
                    overlay_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                ),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
    )

    # Update toggle mode to handle visibility
    original_toggle = toggle_mode
    def toggle_mode_enhanced(e):
        original_toggle(e)
        # Update spacer visibility
        for control in login_form.controls:
            if hasattr(control, 'data') and control.data == "email_spacer":
                control.visible = is_signup_mode
        
        # Update toggle link text
        if is_signup_mode:
            toggle_link.controls[0].value = "Already have an account?"
            toggle_link.controls[1].text = "Login here"
        else:
            toggle_link.controls[0].value = "Don't have an account?"
            toggle_link.controls[1].text = "Sign up here"
        
        page.update()
    
    toggle_link.controls[1].on_click = toggle_mode_enhanced

    login_panel = ft.Container(
        content=ft.Column(
            controls=[
                login_form,
                ft.Container(height=24),
                divider,
                ft.Container(height=16),
                toggle_link,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
        ),
        width=max(330, min(520, form_width + 70)),
        padding=ft.padding.symmetric(horizontal=22, vertical=24),
        border=ft.border.all(1.5, border_color),
        border_radius=14,
        bgcolor=panel_bg,
        shadow=drop_shadow,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(height=24),
                login_panel,
                ft.Container(height=20),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(horizontal=16, vertical=22),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[page_bg_top, page_bg_bottom],
        ),
    )