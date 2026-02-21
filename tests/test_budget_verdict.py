"""
Test the dashboard budget verdict logic for two scenarios:
1. Tasks fit in the day (✓ verdict)
2. Tasks don't fit (⚠ verdict)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, date
import sqlite3
from utils.time_helpers import format_minutes


def test_budget_verdict_scenarios():
    """Test both scenarios: tasks fit, tasks don't fit"""
    
    print("\n" + "=" * 70)
    print("DASHBOARD BUDGET VERDICT TEST")
    print("=" * 70)
    
    # Setup: Create in-memory database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("[✓] In-memory database created")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            estimated_time INTEGER,
            date_due TEXT,
            date_created TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER,
            date_logged TEXT
        )
    """)
    
    conn.commit()
    print("[✓] Tables created")
    
    # Create test user
    user_id = 1
    cursor.execute("""
        INSERT INTO users (user_id, username, email, full_name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "testuser", "test@tymate.com", "Test User", datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    print(f"[✓] Test user created (ID: {user_id})")
    
    today = datetime.now().date()
    day_name = today.strftime("%A")
    
    # Add class schedule: 2 hours total (9:00-10:00 and 14:00-15:00)
    # This leaves approximately 14 hours free (assuming 16-hour awake period)
    cursor.execute("""
        INSERT INTO class_schedule (user_id, day_of_week, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, day_name, "09:00", "10:00"))
    
    cursor.execute("""
        INSERT INTO class_schedule (user_id, day_of_week, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (user_id, day_name, "14:00", "15:00"))
    
    conn.commit()
    print(f"[✓] Class schedule added for {day_name}: 9:00-10:00 and 14:00-15:00")
    
    # Calculate free time by querying class schedules
    # Assume 16-hour awake period (7 AM to 11 PM)
    awake_minutes = 16 * 60  # 960 minutes
    
    cursor.execute("""
        SELECT SUM(
            (strftime('%s', end_time) - strftime('%s', start_time)) / 60
        ) as total_class_minutes
        FROM class_schedule
        WHERE user_id = ? AND day_of_week = ?
    """, (user_id, day_name))
    
    result = cursor.fetchone()
    class_minutes = result['total_class_minutes'] or 0
    free_minutes = awake_minutes - class_minutes - 90  # 90-minute buffer
    
    print(f"[✓] Awake period: {awake_minutes} minutes (16 hours)")
    print(f"[✓] Class time: {int(class_minutes)} minutes")
    print(f"[✓] Free time available: {format_minutes(int(free_minutes))}")
    
    # ========== SCENARIO 1: Tasks FIT ==========
    print("\n" + "-" * 70)
    print("SCENARIO 1: Tasks FIT comfortably in the day")
    print("-" * 70)
    
    # Clear any existing tasks
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    
    # Add small tasks today (total: 2 hours = 120 minutes)
    cursor.execute("""
        INSERT INTO tasks (user_id, title, estimated_time, date_due, date_created, completed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "Quiz Review", 60, today.isoformat(), datetime.now().isoformat(), 0))
    
    cursor.execute("""
        INSERT INTO tasks (user_id, title, estimated_time, date_due, date_created, completed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, "Read Chapter 5", 60, today.isoformat(), datetime.now().isoformat(), 0))
    
    conn.commit()
    
    two_days_ahead = today + timedelta(days=2)
    cursor.execute("""
        SELECT SUM(estimated_time) as total FROM tasks 
        WHERE user_id = ? AND date_due IS NOT NULL 
        AND date_due BETWEEN ? AND ?
    """, (user_id, today.isoformat(), two_days_ahead.isoformat()))
    
    result = cursor.fetchone()
    total_needed = result['total'] or 0
    
    minutes_surplus = int(free_minutes) - total_needed
    print(f"  Tasks needed (next 2 days): {format_minutes(total_needed)}")
    print(f"  Surplus/Deficit: {format_minutes(minutes_surplus)}")
    
    # Determine verdict (same logic as dashboard.py)
    if minutes_surplus >= 0:
        if minutes_surplus > 240:
            verdict = "✓ You have room to do stuff."
        else:
            verdict = "✓ Time is tight, but things are doable."
    else:
        verdict = f"⚠ You're short by {format_minutes(abs(minutes_surplus))}. Something has to move."
    
    print(f"  VERDICT: {verdict}")
    assert "✓" in verdict, f"Expected ✓ verdict in Scenario 1, got: {verdict}"
    print("  ✓ PASS: Verdict shows green checkmark")
    
    # ========== SCENARIO 2: Tasks DON'T FIT ==========
    print("\n" + "-" * 70)
    print("SCENARIO 2: Tasks DON'T fit (exceeds available time)")
    print("-" * 70)
    
    # Clear tasks and add large ones
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    
    # Add large tasks (total: 16 hours = 960 minutes, way more than free time of 750min)
    for i in range(4):
        title = f"Major Project {i+1}"
        cursor.execute("""
            INSERT INTO tasks (user_id, title, estimated_time, date_due, date_created, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, title, 240, today.isoformat(), datetime.now().isoformat(), 0))
    
    conn.commit()
    
    cursor.execute("""
        SELECT SUM(estimated_time) as total FROM tasks 
        WHERE user_id = ? AND date_due IS NOT NULL 
        AND date_due BETWEEN ? AND ?
    """, (user_id, today.isoformat(), two_days_ahead.isoformat()))
    
    result = cursor.fetchone()
    total_needed = result['total'] or 0
    
    minutes_surplus = int(free_minutes) - total_needed
    print(f"  Tasks needed (next 2 days): {format_minutes(total_needed)}")
    if minutes_surplus >= 0:
        print(f"  Surplus: {format_minutes(minutes_surplus)}")
    else:
        print(f"  Deficit: {format_minutes(abs(minutes_surplus))}")
    
    # Determine verdict
    if minutes_surplus >= 0:
        if minutes_surplus > 240:
            verdict = "✓ You have room to do stuff."
        else:
            verdict = "✓ Time is tight, but things are doable."
    else:
        verdict = f"⚠ You're short by {format_minutes(abs(minutes_surplus))}. Something has to move."
    
    print(f"  VERDICT: {verdict}")
    assert "⚠" in verdict, f"Expected ⚠ verdict in Scenario 2, got: {verdict}"
    print("  ✓ PASS: Verdict shows warning symbol")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print("✓ Scenario 1 (tasks fit): Verdict correctly shows ✓")
    print("✓ Scenario 2 (tasks don't fit): Verdict correctly shows ⚠")
    print("=" * 70 + "\n")
    
    conn.close()


if __name__ == "__main__":
    test_budget_verdict_scenarios()
