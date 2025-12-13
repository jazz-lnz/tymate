"""
TYMATE Sample Database Generator
Creates realistic sample data for testing the UI
"""

from storage.sqlite import get_database
from models.user import User
from datetime import datetime, timedelta
import random

def hash_password(password):
    """Hash password using bcrypt (same as User model)"""
    return User.hash_password(password)

def generate_sample_database():
    """Generate a database with realistic sample tasks"""
    
    print("=" * 60)
    print("TYMATE SAMPLE DATABASE GENERATOR")
    print("=" * 60)
    
    # Get database instance
    db = get_database()
    print("[OK] Database connected successfully")
    print(f">> Database location: {db.db_path}\n")
    
    # ==================== Create Users ====================
    print("Creating users...")
    
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
            "full_name": "Jessica Lanuzo",
            "sleep_hours": 7.5,
            "wake_time": "06:30",
            "has_work": 1,
            "work_hours_per_week": 20.0,
            "work_days_per_week": 4,
            "study_goal_hours_per_day": 6.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "username": "john",
            "email": "john@tymate.com",
            "password_hash": hash_password("john123"),
            "role": "user",
            "full_name": "John Dawn",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]
    
    for user_data in users_data:
        try:
            user_id = db.insert("users", user_data)
            print(f"[OK] Created user: {user_data['username']} (ID: {user_id})")
        except Exception as e:
            print(f"[ ! ]  User {user_data['username']} already exists")
    
    # Get Jessica's ID
    jessica = db.fetch_one("SELECT id FROM users WHERE username = ?", ("jessica",))
    if not jessica:
        print("[ ! ] Error: Jessica user not found!")
        return
    
    jessica_id = jessica['id']
    
    # ==================== Create Realistic Tasks ====================
    print("\nCreating realistic sample tasks for Jessica...")
    
    today = datetime.now().date()
    
    # Define realistic tasks using your actual courses
    sample_tasks = [
        # COMPLETED TASKS (to show analytics data)
        {
            "title": "Quiz 1: Research Methodologies",
            "source": "CSAC 3211 - Methods of Research",
            "category": "quiz",
            "date_given": (today - timedelta(days=14)).isoformat(),
            "date_due": (today - timedelta(days=7)).isoformat(),
            "description": "Qualitative vs Quantitative Research",
            "estimated_time": 2.0,
            "actual_time": 1.5,
            "status": "Completed",
            "completed_at": (datetime.now() - timedelta(days=7, hours=3)).isoformat(),
        },
        {
            "title": "Learning Task: SDLC Models",
            "source": "CS 3110 - Software Engineering 1",
            "category": "learning task (individual)",
            "date_given": (today - timedelta(days=10)).isoformat(),
            "date_due": (today - timedelta(days=3)).isoformat(),
            "description": "Study Agile, Waterfall, and DevOps methodologies",
            "estimated_time": 5.0,
            "actual_time": 6.5,
            "status": "Completed",
            "completed_at": (datetime.now() - timedelta(days=3, hours=2)).isoformat(),
        },
        {
            "title": "Coffee Shop - Morning Shift",
            "source": "Starbucks",
            "category": "others",
            "date_given": (today - timedelta(days=5)).isoformat(),
            "date_due": (today - timedelta(days=5)).isoformat(),
            "description": "6am-10am shift",
            "estimated_time": 4.0,
            "actual_time": 4.0,
            "status": "Completed",
            "completed_at": (datetime.now() - timedelta(days=5, hours=14)).isoformat(),
        },
        {
            "title": "Study Session: Digital Forensics",
            "source": "Personal",
            "category": "study/review",
            "date_given": (today - timedelta(days=8)).isoformat(),
            "date_due": (today - timedelta(days=6)).isoformat(),
            "description": "Review evidence collection and chain of custody",
            "estimated_time": 8.0,
            "actual_time": 9.5,
            "status": "Completed",
            "completed_at": (datetime.now() - timedelta(days=6, hours=5)).isoformat(),
        },
        
        # IN PROGRESS TASKS
        {
            "title": "TYMATE App Development",
            "source": "CS 3110 - Software Engineering 1",
            "category": "project (group)",
            "date_given": (today - timedelta(days=20)).isoformat(),
            "date_due": (today + timedelta(days=5)).isoformat(),
            "description": "Develop time management app with RBAC and analytics",
            "estimated_time": 25.0,
            "actual_time": None,
            "status": "In Progress",
        },
        {
            "title": "Learning Task: Regular Expressions",
            "source": "CS 317 - Automata Theory and Formal Languages",
            "category": "learning task (individual)",
            "date_given": (today - timedelta(days=5)).isoformat(),
            "date_due": (today + timedelta(days=2)).isoformat(),
            "description": "Practice converting regex to DFA and NFA",
            "estimated_time": 4.0,
            "actual_time": None,
            "status": "In Progress",
        },
        {
            "title": "Mobile App Prototype",
            "source": "CCCS 106 - Application Development and Emerging Tech",
            "category": "project (individual)",
            "date_given": (today - timedelta(days=15)).isoformat(),
            "date_due": (today + timedelta(days=10)).isoformat(),
            "description": "Create Flutter prototype for mobile learning app",
            "estimated_time": 15.0,
            "actual_time": None,
            "status": "In Progress",
        },
        
        # NOT STARTED TASKS
        {
            "title": "Quiz 2: Context-Free Grammars",
            "source": "CS 317 - Automata Theory and Formal Languages",
            "category": "quiz",
            "date_given": today.isoformat(),
            "date_due": (today + timedelta(days=7)).isoformat(),
            "description": "CFG, PDA, and Turing Machines",
            "estimated_time": 2.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Research Paper: IA Best Practices",
            "source": "CS 319 - Information Assurance and Security",
            "category": "project (individual)",
            "date_given": (today - timedelta(days=30)).isoformat(),
            "date_due": (today + timedelta(days=14)).isoformat(),
            "description": "5-page paper on security frameworks and compliance",
            "estimated_time": 12.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Group Presentation Prep",
            "source": "CSAC 3211 - Methods of Research",
            "category": "learning task (group)",
            "date_given": today.isoformat(),
            "date_due": (today + timedelta(days=5)).isoformat(),
            "description": "Prepare slides for research methodology presentation",
            "estimated_time": 6.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Coffee Shop - Evening Shift",
            "source": "Starbucks",
            "category": "others",
            "date_given": today.isoformat(),
            "date_due": (today + timedelta(days=1)).isoformat(),
            "description": "4pm-8pm shift",
            "estimated_time": 4.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Study for Finals",
            "source": "Personal",
            "category": "study/review",
            "date_given": today.isoformat(),
            "date_due": (today + timedelta(days=21)).isoformat(),
            "description": "Comprehensive review for all courses",
            "estimated_time": 30.0,
            "actual_time": None,
            "status": "Not Started",
        },
        
        # OVERDUE TASK (to test overdue badge)
        {
            "title": "Lab Report: Network Security",
            "source": "CS 319 - Information Assurance and Security",
            "category": "learning task (individual)",
            "date_given": (today - timedelta(days=14)).isoformat(),
            "date_due": (today - timedelta(days=2)).isoformat(),
            "description": "Write report on penetration testing exercise",
            "estimated_time": 3.0,
            "actual_time": None,
            "status": "Not Started",
        },
        
        # UPCOMING TASKS (different sources)
        {
            "title": "Midterm Exam",
            "source": "CS 3110 - Software Engineering 1",
            "category": "quiz",
            "date_given": (today - timedelta(days=7)).isoformat(),
            "date_due": (today + timedelta(days=3)).isoformat(),
            "description": "Covers design patterns and testing methodologies",
            "estimated_time": 3.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Team Meeting: Project Sync",
            "source": "CS 3110 - Software Engineering 1",
            "category": "learning task (group)",
            "date_given": today.isoformat(),
            "date_due": today.isoformat(),
            "description": "Weekly team standup for TYMATE project",
            "estimated_time": 1.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "English Essay: Persuasive Writing",
            "source": "CSAC 3210 - English Proficiency Program",
            "category": "learning task (individual)",
            "date_given": (today - timedelta(days=5)).isoformat(),
            "date_due": (today + timedelta(days=3)).isoformat(),
            "description": "Write 500-word persuasive essay",
            "estimated_time": 2.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Workout Session",
            "source": "Personal",
            "category": "others",
            "date_given": today.isoformat(),
            "date_due": today.isoformat(),
            "description": "Gym session - leg day",
            "estimated_time": 1.5,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Architecture Design Document",
            "source": "CS 318 - Architecture and Organization",
            "category": "learning task (individual)",
            "date_given": (today - timedelta(days=3)).isoformat(),
            "date_due": (today + timedelta(days=4)).isoformat(),
            "description": "Design CPU architecture with pipelining",
            "estimated_time": 8.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Communication Skills Workshop",
            "source": "GE 5 - Purposive Communication",
            "category": "others",
            "date_given": (today - timedelta(days=2)).isoformat(),
            "date_due": (today + timedelta(days=1)).isoformat(),
            "description": "Attend workshop on effective business communication",
            "estimated_time": 2.0,
            "actual_time": None,
            "status": "Not Started",
        },
        {
            "title": "Forensics Lab: Evidence Analysis",
            "source": "CSAC 317 - Digital Forensics",
            "category": "project (group)",
            "date_given": (today - timedelta(days=10)).isoformat(),
            "date_due": (today + timedelta(days=8)).isoformat(),
            "description": "Analyze digital evidence using forensic tools",
            "estimated_time": 10.0,
            "actual_time": None,
            "status": "Not Started",
        },
    ]
    
    # Insert all tasks
    task_count = 0
    for task_data in sample_tasks:
        task_data["user_id"] = jessica_id
        task_data["created_at"] = datetime.now().isoformat()
        task_data["updated_at"] = datetime.now().isoformat()
        
        try:
            task_id = db.insert("tasks", task_data)
            task_count += 1
            
            # Status emoji
            if task_data["status"] == "Completed":
                emoji = "[OK]"
            elif task_data["status"] == "In Progress":
                emoji = "[...]"
            else:
                emoji = "[ ? ]"
            
            # Overdue check
            overdue = ""
            if task_data["status"] != "Completed":
                due_date = datetime.fromisoformat(task_data["date_due"]).date()
                if due_date < today:
                    overdue = " [ ! ] OVERDUE"
            
            print(f"{emoji} {task_data['title']}{overdue}")
            print(f"   Source: {task_data['source']} | Category: {task_data['category']}")
            
        except Exception as e:
            print(f"[ ! ] Error creating task: {e}")
    
    # ==================== Create Time Logs ====================
    print(f"\n{'='*60}")
    print("Creating time logs for completed tasks...")
    print(f"{'='*60}\n")
    
    # Get completed tasks
    completed_tasks = db.fetch_all(
        "SELECT * FROM tasks WHERE user_id = ? AND status = 'Completed'",
        (jessica_id,)
    )
    
    time_log_count = 0
    for task in completed_tasks:
        if task['actual_time']:
            time_log_data = {
                "user_id": jessica_id,
                "task_id": task['id'],
                "category": task['category'],
                "hours": task['actual_time'],
                "date": task['completed_at'][:10] if task['completed_at'] else today.isoformat(),
                "start_time": None,
                "end_time": None,
                "notes": f"Completed: {task['title']}",
                "created_at": task['completed_at'] if task['completed_at'] else datetime.now().isoformat(),
            }
            
            db.insert("time_logs", time_log_data)
            time_log_count += 1
            print(f">> Logged {task['actual_time']}h for {task['title']}")
    
    # ==================== Statistics ====================
    print(f"\n{'='*60}")
    print("DATABASE STATISTICS")
    print(f"{'='*60}\n")
    
    total_tasks = db.count("tasks", f"user_id = {jessica_id}")
    completed = db.count("tasks", f"user_id = {jessica_id} AND status = 'Completed'")
    in_progress = db.count("tasks", f"user_id = {jessica_id} AND status = 'In Progress'")
    not_started = db.count("tasks", f"user_id = {jessica_id} AND status = 'Not Started'")
    
    print(f"Total Tasks: {total_tasks}")
    print(f"  [OK] Completed: {completed}")
    print(f"  [...] In Progress: {in_progress}")
    print(f"  [ ? ] Not Started: {not_started}")
    print(f"\nTime Logs: {time_log_count}")
    
    # Source breakdown
    print(f"\n{'='*60}")
    print("TASKS BY SOURCE")
    print(f"{'='*60}\n")
    
    sources = db.fetch_all("""
        SELECT source, COUNT(*) as count
        FROM tasks
        WHERE user_id = ?
        GROUP BY source
        ORDER BY count DESC
    """, (jessica_id,))
    
    for source in sources:
        print(f">> {source['source']}: {source['count']} tasks")
    
    # Category breakdown
    print(f"\n{'='*60}")
    print("TASKS BY CATEGORY (Implicit Priority)")
    print(f"{'='*60}\n")
    
    categories = db.fetch_all("""
        SELECT category, COUNT(*) as count
        FROM tasks
        WHERE user_id = ?
        GROUP BY category
        ORDER BY 
            CASE 
                WHEN category LIKE '%project%' THEN 1
                WHEN category LIKE '%learning task%' THEN 2
                WHEN category LIKE '%quiz%' THEN 3
                ELSE 4
            END
    """, (jessica_id,))
    
    for cat in categories:
        # Determine implicit priority
        cat_lower = cat['category'].lower()
        if 'project' in cat_lower:
            priority = "High"
        elif 'learning task' in cat_lower:
            priority = "Medium"
        elif 'quiz' in cat_lower:
            priority = "Low"
        else:
            priority = "N/A"
        
        print(f"{cat['category']} (Priority: {priority}): {cat['count']} tasks")
    
    # ==================== Success Message ====================
    print(f"\n{'='*60}")
    print("[OK] SAMPLE DATABASE CREATED SUCCESSFULLY!")
    print(f"{'='*60}\n")
    
    print("Test Credentials:")
    print("  Username: jessica")
    print("  Password: jessica123")
    print(f"\n>> Created {total_tasks} realistic tasks with various:")
    print("  • Sources (courses, workplace, personal)")
    print("  • Categories (quiz, learning tasks, projects, etc.)")
    print("  • Statuses (completed, in progress, not started)")
    print("  • Time estimates vs actuals (for analytics)")
    print("  • Overdue tasks (to test alerts)")
    print("\n>> Now run your app and login as Jessica to see the data!")

if __name__ == "__main__":
    generate_sample_database()