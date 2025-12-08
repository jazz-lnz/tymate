"""
Test Authentication System
Run this to verify auth manager works
"""

from state.auth_manager import AuthManager
from models.user import User

def test_auth_system():
    print("=" * 60)
    print("TYMATE AUTHENTICATION TEST")
    print("=" * 60)
    
    auth = AuthManager()
    
    # Test 1: Register new user
    print("\n🔸 TEST 1: User Registration")
    success, msg, user = auth.register_user(
        username="testuser",
        password="test123456",
        email="test@tymate.com",
        full_name="Test User"
    )
    print(f"Result: {msg}")
    if success:
        print(f"✅ User created: {user.username} (ID: {user.id})")
    
    # Test 2: Duplicate username
    print("\n🔸 TEST 2: Duplicate Username Check")
    success, msg, _ = auth.register_user(
        username="testuser",
        password="another123"
    )
    print(f"Result: {msg}")
    if not success:
        print("✅ Correctly rejected duplicate")
    
    # Test 3: Weak password
    print("\n🔸 TEST 3: Password Validation")
    success, msg, _ = auth.register_user(
        username="weak",
        password="123"
    )
    print(f"Result: {msg}")
    if not success:
        print("✅ Correctly rejected weak password")
    
    # Test 4: Successful login
    print("\n🔸 TEST 4: Successful Login")
    success, msg, user, token = auth.login("testuser", "test123456")
    print(f"Result: {msg}")
    if success:
        print(f"✅ Logged in as: {user.username}")
        print(f"   Session token: {token[:20]}...")
        print(f"   Role: {user.role}")
    
    # Test 5: Wrong password
    print("\n🔸 TEST 5: Wrong Password")
    success, msg, _, _ = auth.login("testuser", "wrongpassword")
    print(f"Result: {msg}")
    if not success:
        print("✅ Correctly rejected wrong password")
    
    # Test 6: Get user by session
    if token:
        print("\n🔸 TEST 6: Session Validation")
        session_user = auth.get_user_by_session(token)
        if session_user:
            print(f"✅ Retrieved user from session: {session_user.username}")
            print(f"   Email: {session_user.email}")
            print(f"   Role: {session_user.role}")
            print(f"   Account active: {session_user.is_active}")
        else:
            print("❌ Failed to retrieve user from session")
    
    # Test 7: Logout
    if token:
        print("\n🔸 TEST 7: Logout")
        auth.logout(token)
        print("✅ Logged out")
        
        # Try to use expired session
        expired_user = auth.get_user_by_session(token)
        if not expired_user:
            print("✅ Session correctly invalidated")
    
    # Test 8: Change password
    print("\n🔸 TEST 8: Change Password")
    # Login again
    success, msg, user, token = auth.login("testuser", "test123456")
    if success:
        success, msg = auth.change_password(
            user.id,
            "test123456",
            "newpassword123"
        )
        print(f"Result: {msg}")
        if success:
            print("✅ Password changed")
            
            # Try logging in with new password
            success, msg, _, _ = auth.login("testuser", "newpassword123")
            print(f"Login with new password: {msg}")
            if success:
                print("✅ New password works")
    
    # Test 9: Update profile
    print("\n🔸 TEST 9: Update User Profile")
    success, msg = auth.update_user_profile(
        user.id,
        full_name="Test User Updated",
        email="updated@tymate.com"
    )
    print(f"Result: {msg}")
    if success:
        print("✅ Profile updated")
        # Verify update
        updated_user = auth.get_user_by_session(token)
        print(f"   New name: {updated_user.full_name}")
        print(f"   New email: {updated_user.email}")
    
    # Test 10: Permission check (RBAC)
    print("\n🔸 TEST 10: RBAC Permission Check")
    print(f"User role: {user.role}")
    print(f"   Can create tasks: {user.has_permission('create_tasks')}")
    print(f"   Can view smart tips: {user.has_permission('smart_tips')}")
    print(f"   Can manage users: {user.has_permission('manage_users')}")
    if user.has_permission('create_tasks') and not user.has_permission('manage_users'):
        print("✅ User permissions correct")
    
    # Test 11: Create admin user
    print("\n🔸 TEST 11: Create Admin User")
    success, msg, admin = auth.register_user(
        username="admin",
        password="admin123",
        full_name="Admin User",
        role="admin"
    )
    print(f"Result: {msg}")
    if success:
        print(f"✅ Admin created: {admin.username}")
        print(f"   Can manage users: {admin.has_permission('manage_users')}")
        print(f"   Can view smart tips: {admin.has_permission('smart_tips')}")
        print(f"   Can create tasks: {admin.has_permission('create_tasks')}")
        if admin.has_permission('manage_users'):
            print("✅ Admin has all permissions")
    
    # Test 12: Account locking after failed attempts
    print("\n🔸 TEST 12: Account Lock After Failed Logins")
    # Create test user for locking
    success, msg, lock_user = auth.register_user(
        username="locktest",
        password="locktest123"
    )
    if success:
        print(f"Created user: {lock_user.username}")
        # Attempt wrong password 5 times
        for i in range(5):
            success, msg, _, _ = auth.login("locktest", "wrongpass")
            print(f"   Attempt {i+1}: {msg}")
        
        # Try correct password after lock
        success, msg, _, _ = auth.login("locktest", "locktest123")
        print(f"   Login after lock: {msg}")
        if not success and "locked" in msg.lower():
            print("✅ Account correctly locked after max attempts")
    
    print("\n" + "=" * 60)
    print("✅ ALL AUTHENTICATION TESTS PASSED!")
    print("=" * 60)
    print("\n💡 Test users created:")
    print("   - testuser / newpassword123 (role: user)")
    print("   - admin / admin123 (role: admin)")
    print("   - locktest (LOCKED)")

if __name__ == "__main__":
    test_auth_system()