from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets
from storage.sqlite import get_database
from models.user import User

class AuthManager:
    """
    Manages user authentication and sessions
    
    Features:
    - User registration with validation
    - Secure login with password verification
    - Session management with tokens
    - Failed login attempt tracking
    - Account locking after failed attempts
    """
    
    MAX_FAILED_ATTEMPTS = 5
    SESSION_DURATION_HOURS = 24
    
    def __init__(self):
        self.db = get_database()
    
    def register_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "user"
    ) -> tuple[bool, str, Optional[User]]:
        """
        Register a new user
        
        Args:
            username: Desired username (must be unique)
            password: Plain text password (will be hashed)
            email: User email (optional)
            full_name: User's full name (optional)
            role: User role (default: "user")
            
        Returns:
            Tuple of (success: bool, message: str, user: Optional[User])
        """
        
        # Validate username
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters", None
        
        # Check if username exists
        existing_user = self.db.fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        if existing_user:
            return False, "Username already exists", None
        
        # Validate password
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        # Create user object
        user = User(
            username=username,
            password_hash=User.hash_password(password),
            email=email,
            full_name=full_name,
            role=role,
        )
        
        # Save to database
        try:
            user_data = user.to_dict()
            user_data.pop("id")  # Let database auto-generate ID
            
            user_id = self.db.insert("users", user_data)
            user.id = user_id
            
            # Log the registration
            self._log_audit(user_id, "USER_REGISTERED", "users", user_id, 
                          new_value=f"New user registered: {username}")
            
            return True, "Account created successfully!", user
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
    
    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> tuple[bool, str, Optional[User], Optional[str]]:
        """
        Authenticate user and create session
        
        Args:
            username: Username
            password: Plain text password
            ip_address: User's IP address (for logging)
            
        Returns:
            Tuple of (success: bool, message: str, user: Optional[User], token: Optional[str])
        """
        
        # Get user from database
        user_data = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        
        if not user_data:
            self._log_login_attempt(username, False, "User not found", ip_address)
            return False, "Invalid username or password", None, None
        
        user = User.from_dict(user_data)
        
        # Check if account is locked
        if user.is_locked:
            return False, "Account is locked. Contact administrator.", None, None
        
        # Check if account is active
        if not user.is_active:
            return False, "Account is disabled. Contact administrator.", None, None
        
        # Verify password
        if not user.verify_password(password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failures
            if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                self.db.update(
                    "users",
                    {
                        "failed_login_attempts": user.failed_login_attempts,
                        "is_locked": 1,
                        "updated_at": datetime.now().isoformat()
                    },
                    "id = ?",
                    (user.id,)
                )
                self._log_login_attempt(username, False, "Account locked", ip_address)
                return False, f"Too many failed attempts. Account locked.", None, None
            else:
                self.db.update(
                    "users",
                    {"failed_login_attempts": user.failed_login_attempts},
                    "id = ?",
                    (user.id,)
                )
                self._log_login_attempt(username, False, "Invalid password", ip_address)
                remaining = self.MAX_FAILED_ATTEMPTS - user.failed_login_attempts
                return False, f"Invalid password. {remaining} attempts remaining.", None, None
        
        # Password correct - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.now().isoformat()
        
        self.db.update(
            "users",
            {
                "failed_login_attempts": 0,
                "last_login": user.last_login,
                "updated_at": datetime.now().isoformat()
            },
            "id = ?",
            (user.id,)
        )
        
        # Create session
        session_token = self._create_session(user.id)
        
        # Log successful login
        self._log_login_attempt(username, True, None, ip_address)
        self._log_audit(user.id, "USER_LOGIN", "sessions", None, 
                       new_value=f"User logged in successfully")
        
        return True, "Login successful!", user, session_token
    
    def logout(self, session_token: str) -> bool:
        """
        End user session
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if session ended successfully
        """
        try:
            self.db.update(
                "sessions",
                {"is_active": 0, "last_activity": datetime.now().isoformat()},
                "session_token = ?",
                (session_token,)
            )
            return True
        except:
            return False
    
    def get_user_by_session(self, session_token: str) -> Optional[User]:
        """
        Get user from session token
        
        Args:
            session_token: Session token
            
        Returns:
            User object if session valid, None otherwise
        """
        # Get session
        session = self.db.fetch_one("""
            SELECT * FROM sessions 
            WHERE session_token = ? 
            AND is_active = 1
        """, (session_token,))
        
        if not session:
            return None
        
        # Check if session expired
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            # Expire session
            self.logout(session_token)
            return None
        
        # Get user
        user_data = self.db.get_by_id("users", session["user_id"])
        if not user_data:
            return None
        
        # Update last activity
        self.db.update(
            "sessions",
            {"last_activity": datetime.now().isoformat()},
            "session_token = ?",
            (session_token,)
        )
        
        return User.from_dict(user_data)
    
    def _create_session(self, user_id: int) -> str:
        """
        Create new session for user
        
        Args:
            user_id: User ID
            
        Returns:
            Session token
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiry
        now = datetime.now()
        expires_at = now + timedelta(hours=self.SESSION_DURATION_HOURS)
        
        # Save session
        self.db.insert("sessions", {
            "user_id": user_id,
            "session_token": token,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": now.isoformat(),
            "is_active": 1
        })
        
        return token
    
    def _log_login_attempt(
        self,
        username: str,
        success: bool,
        failure_reason: Optional[str],
        ip_address: Optional[str]
    ):
        """Log login attempt to database"""
        self.db.insert("login_attempts", {
            "username": username,
            "success": 1 if success else 0,
            "failure_reason": failure_reason,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_audit(
        self,
        user_id: int,
        action: str,
        table_name: str,
        record_id: Optional[int],
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ):
        """Log action to audit log"""
        self.db.insert("audit_logs", {
            "user_id": user_id,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_user_profile(
        self,
        user_id: int,
        **updates
    ) -> tuple[bool, str]:
        """
        Update user profile fields
        
        Args:
            user_id: User ID
            **updates: Fields to update (email, full_name, etc.)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Don't allow updating sensitive fields
        forbidden_fields = {"id", "password_hash", "failed_login_attempts", "is_locked"}
        
        for field in forbidden_fields:
            if field in updates:
                return False, f"Cannot update field: {field}"

        # Prevent duplicate usernames and validate length when changing username
        if "username" in updates:
            new_username = updates.get("username")

            if new_username is None or new_username.strip() == "":
                return False, "Username cannot be empty"

            new_username = new_username.strip()

            if len(new_username) < 3:
                return False, "Username must be at least 3 characters"

            existing = self.db.fetch_one(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (new_username, user_id),
            )

            if existing:
                return False, "Username already exists"

            updates["username"] = new_username
        
        # Add updated_at timestamp
        updates["updated_at"] = datetime.now().isoformat()
        
        try:
            self.db.update("users", updates, "id = ?", (user_id,))
            
            self._log_audit(
                user_id, "PROFILE_UPDATE", "users", user_id,
                new_value=f"Updated fields: {', '.join(updates.keys())}"
            )
            
            return True, "Profile updated successfully"
        except Exception as e:
            return False, f"Update failed: {str(e)}"
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> tuple[bool, str]:
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password (for verification)
            new_password: New password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Get user
        user_data = self.db.get_by_id("users", user_id)
        if not user_data:
            return False, "User not found"
        
        user = User.from_dict(user_data)
        
        # Verify old password
        if not user.verify_password(old_password):
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"
        
        # Update password
        new_hash = User.hash_password(new_password)
        
        self.db.update(
            "users",
            {
                "password_hash": new_hash,
                "updated_at": datetime.now().isoformat()
            },
            "id = ?",
            (user_id,)
        )
        
        self._log_audit(user_id, "PASSWORD_CHANGED", "users", user_id,
                       new_value="Password updated")
        
        return True, "Password changed successfully"


# Example usage
if __name__ == "__main__":
    auth = AuthManager()
    
    # Register a new user
    success, msg, user = auth.register_user(
        username="testuser",
        password="test123",
        email="test@example.com",
        full_name="Test User"
    )
    print(f"Registration: {msg}")
    
    if success:
        # Try to login
        success, msg, user, token = auth.login("testuser", "test123")
        print(f"Login: {msg}")
        
        if success:
            print(f"Session token: {token}")
            print(f"User: {user}")
            
            # Get user by session
            retrieved_user = auth.get_user_by_session(token)
            print(f"Retrieved user: {retrieved_user}")
            
            # Logout
            auth.logout(token)
            print("Logged out")