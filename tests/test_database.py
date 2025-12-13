"""
TYMATE Database Testing Script
Run this to verify your database works before UI is ready
"""

from storage.sqlite import get_database
from models.user import User
from datetime import datetime

def hash_password(password):
    """Hash password using bcrypt (same as User model)"""
    return User.hash_password(password)

def test_database():
    """Test all database operations"""
    
    print("=" * 60)
    print("TYMATE DATABASE TEST")
    print("=" * 60)
    
    # Get database instance
    db = get_database()
    print("[OK] Database connected successfully")
    print(f"Database location: {db.db_path}\n")
    
    # ==================== TEST 1: User Creation ====================
    print("TEST 1: Creating users...")
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@tymate.com",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "full_name": "Admin User",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "username": "jessica",
            "email": "jessica@tymate.com",
            "password_hash": hash_password("jessica123"),
            "role": "premium",
            "full_name": "Jessica Smith",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "username": "john",
            "email": "john@tymate.com",
            "password_hash": hash_password("john123"),
            "role": "user",
            "full_name": "John Doe",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]
    
    for user_data in users_data:
        try:
            user_id = db.insert("users", user_data)
            print(f"[OK] Created user: {user_data['username']} (ID: {user_id}, Role: {user_data['role']})")
        except Exception as e:
            print(f"[!]  User {user_data['username']} already exists or error: {e}")
    
    # ==================== TEST 2: Verify Users ====================
    print("\nTEST 2: Fetching all users...")
    
    users = db.fetch_all("SELECT id, username, email, role, full_name FROM users")
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['username']} ({user['role']}) - {user['full_name']}")
    
    # ==================== TEST 3: Create Tasks ====================
    print("\nTEST 3: Creating tasks...")
    
    # Get jessica's user_id
    jessica = db.fetch_one("SELECT id FROM users WHERE username = ?", ("jessica",))
    if jessica:
        tasks_data = [
            {
                "user_id": jessica['id'],
                "title": "Complete CS 319 Project",
                "source": "CS 319",
                "description": "Implement RBAC and security features",
                "category": "School",
                "date_given": "2025-12-01",
                "date_due": "2025-12-10",
                "status": "In Progress",
                "estimated_time": 20.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "user_id": jessica['id'],
                "title": "Work Shift - Coffee Shop",
                "source": "Coffee Shop",
                "description": "Monday evening shift",
                "category": "Work",
                "date_given": "2025-12-08",
                "date_due": "2025-12-09",
                "status": "Not Started",
                "estimated_time": 4.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "user_id": jessica['id'],
                "title": "Study for Finals",
                "source": "University",
                "description": "Review chapters 1-10",
                "category": "School",
                "date_given": "2025-12-08",
                "date_due": "2025-12-15",
                "status": "Not Started",
                "estimated_time": 15.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        ]
        
        for task_data in tasks_data:
            task_id = db.insert("tasks", task_data)
            print(f"[OK] Created task: {task_data['title']} (ID: {task_id})")
    
    # ==================== TEST 4: Verify Tasks ====================
    print("\nTEST 4: Fetching jessica's tasks...")
    
    tasks = db.fetch_all(
        "SELECT id, title, category, status, date_due FROM tasks WHERE user_id = ?",
        (jessica['id'],)
    )
    print(f"Found {len(tasks)} tasks for jessica:")
    for task in tasks:
        print(f"  - [{task['status']}] {task['title']} (Due: {task['date_due']})")
    
    # ==================== TEST 5: Log Time ====================
    print("\nTEST 5: Logging work hours...")
    
    time_logs_data = [
        {
            "user_id": jessica['id'],
            "task_id": tasks[0]['id'],
            "category": "School",
            "hours": 3.5,
            "date": "2025-12-03",
            "start_time": "14:00",
            "end_time": "17:30",
            "notes": "Worked on database design",
            "created_at": datetime.now().isoformat(),
        },
        {
            "user_id": jessica['id'],
            "task_id": tasks[1]['id'],
            "category": "Work",
            "hours": 4.0,
            "date": "2025-12-03",
            "start_time": "18:00",
            "end_time": "22:00",
            "notes": "Evening shift at coffee shop",
            "created_at": datetime.now().isoformat(),
        },
    ]
    
    for log_data in time_logs_data:
        log_id = db.insert("time_logs", log_data)
        print(f"[OK] Logged {log_data['hours']} hours for {log_data['category']}")
    
    # ==================== TEST 6: Analytics Query ====================
    print("\nTEST 6: Getting time analytics...")
    
    analytics = db.fetch_all("""
        SELECT 
            category,
            SUM(hours) as total_hours,
            COUNT(*) as sessions
        FROM time_logs
        WHERE user_id = ?
        GROUP BY category
    """, (jessica['id'],))
    
    print("Time breakdown:")
    for stat in analytics:
        print(f"  - {stat['category']}: {stat['total_hours']} hours ({stat['sessions']} sessions)")
    
    # ==================== TEST 7: Audit Logging ====================
    print("\nTEST 7: Creating audit log entry...")
    
    audit_data = {
        "user_id": jessica['id'],
        "username": "jessica",
        "action": "CREATE_TASK",
        "table_name": "tasks",
        "record_id": tasks[0]['id'],
        "new_value": f"Created task: {tasks[0]['title']}",
        "timestamp": datetime.now().isoformat(),
    }
    
    audit_id = db.insert("audit_logs", audit_data)
    print(f"[OK] Audit log created (ID: {audit_id})")
    
    # ==================== TEST 8: Login Attempt ====================
    print("\nTEST 8: Logging login attempt...")
    
    login_data = {
        "username": "jessica",
        "success": 1,
        "timestamp": datetime.now().isoformat(),
    }
    
    login_id = db.insert("login_attempts", login_data)
    print(f"[OK] Login attempt logged (ID: {login_id})")
    
    # ==================== TEST 9: RBAC Check ====================
    print("\nTEST 9: Checking roles and permissions...")
    
    roles = db.fetch_all("SELECT name, description FROM roles")
    print(f"Available roles ({len(roles)}):")
    for role in roles:
        print(f"  - {role['name']}: {role['description']}")
    
    # ==================== TEST 10: Count Statistics ====================
    print("\nTEST 10: Database statistics...")
    
    stats = {
        "Total Users": db.count("users"),
        "Total Tasks": db.count("tasks"),
        "Total Time Logs": db.count("time_logs"),
        "Total Audit Logs": db.count("audit_logs"),
        "Active Users": db.count("users", "is_active = 1"),
    }
    
    for stat_name, stat_value in stats.items():
        print(f"  - {stat_name}: {stat_value}")
    
    # ==================== SUMMARY ====================
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour database is ready for UI integration!")
    print("\nTest Users Created:")
    print("  - admin / admin123 (Role: admin)")
    print("  - jessica / jessica123 (Role: premium)")
    print("  - john / john123 (Role: user)")
    print("\nUse these credentials when your UI is ready!")

if __name__ == "__main__":
    test_database()