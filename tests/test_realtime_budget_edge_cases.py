"""
Test real-time budget calculations throughout the day
This tests get_remaining_budget which uses clock-based calculations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, date
from storage.sqlite import get_database
from state.onboarding_manager import OnboardingManager
import sqlite3


def test_realtime_budget_edge_cases():
    """Test real-time budget calculations with edge cases"""
    
    print("\n" + "=" * 80)
    print("REAL-TIME BUDGET CALCULATION TEST")
    print("=" * 80)
    print("Testing get_remaining_budget() at different times with 5h sleep")
    
    # Create in-memory test database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create minimal tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            sleep_hours REAL,
            wake_time TEXT,
            has_work INTEGER,
            work_hours_per_week REAL,
            work_days_per_week INTEGER,
            study_goal_hours_per_day REAL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER,
            setting_key TEXT,
            setting_value TEXT,
            updated_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_sessions (
            user_id INTEGER,
            duration_minutes INTEGER,
            date_logged TEXT
        )
    """)
    
    conn.commit()
    
    # Test scenarios with 5h sleep
    test_cases = [
        {"sleep": 5.0, "wake": "07:00", "name": "5h sleep, 7 AM wake"},
        {"sleep": 5.0, "wake": "08:00", "name": "5h sleep, 8 AM wake"},
        {"sleep": 5.0, "wake": "06:00", "name": "5h sleep, 6 AM wake"},
    ]
    
    today = date.today()
    
    for test_idx, test_case in enumerate(test_cases, 1):
        print(f"\n  SCENARIO {test_idx}: {test_case['name']}")
        print("  " + "-" * 70)
        
        user_id = test_idx
        sleep_hrs = test_case["sleep"]
        wake_str = test_case["wake"]
        
        # Insert user profile
        cursor.execute("""
            INSERT INTO users (id, username, sleep_hours, wake_time, has_work, 
                             work_hours_per_week, work_days_per_week, 
                             study_goal_hours_per_day, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, f"user{test_idx}", sleep_hrs, wake_str, 0, 0, 0, 4.0, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        # Mark onboarding complete
        cursor.execute("""
            INSERT INTO settings (user_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, "onboarding_completed", "true", datetime.now().isoformat()))
        
        conn.commit()
        
        # Test at different times of day
        times_to_test = [
            ("02:00", "Before wake, during sleep"),        # During sleep
            ("07:00", "Exactly at wake time"),             # At wake (if 7 AM wake)
            ("09:00", "2 hours after wake"),               # After wake
            ("12:00", "Midday"),                           # Midday
            ("18:00", "Evening"),                          # Evening
            ("23:00", "Late night (before sleep)"),        # Before bedtime
            ("01:00", "Early morning (past bedtime)"),     # After bedtime
        ]
        
        for time_str, description in times_to_test:
            hour, minute = map(int, time_str.split(':'))
            test_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Calculate using OnboardingManager
            om = OnboardingManager()
            om.db.connection = conn
            
            try:
                budget = om.get_user_budget(user_id)
                if not budget:
                    print(f"    {time_str} ({description}): ERROR - No budget")
                    continue
                
                # Calculate metrics at this time
                wake_time = om.parse_wake_time(wake_str)
                is_before_wake = test_time.time() < wake_time
                
                if is_before_wake:
                    hours_until_wake = (datetime.combine(today, wake_time) - test_time).total_seconds() / 3600
                    hours_since_wake = 0
                    hours_until_bedtime = 24 - sleep_hrs  # Full waking period
                else:
                    hours_since_wake = om.get_hours_since_wake(test_time, wake_time)
                    hours_until_bedtime = om.get_hours_until_bedtime(test_time, wake_time, sleep_hrs)
                    hours_until_wake = 0
                
                # Validate
                if hours_until_bedtime < 0:
                    status = "✗ NEGATIVE bedtime"
                elif hours_until_bedtime > (24 - sleep_hrs) + 0.1:
                    status = f"✗ EXCESSIVE bedtime ({hours_until_bedtime:.1f}h > {24-sleep_hrs}h)"
                elif hours_since_wake < 0:
                    status = "✗ NEGATIVE hours_since_wake"
                else:
                    status = "✓"
                
                print(f"    {time_str} ({description}): {status}", end="")
                if status == "✓":
                    print(f" | Since wake: {hours_since_wake:.1f}h | Until bed: {hours_until_bedtime:.1f}h")
                else:
                    print()
                    
            except Exception as e:
                print(f"    {time_str} ({description}): ERROR - {e}")
        
        # Clean up for next scenario
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
        conn.commit()


def test_bedtime_boundary_logic():
    """Test bedtime boundary conditions that might cause computation errors"""
    
    print("\n" + "=" * 80)
    print("BEDTIME BOUNDARY LOGIC TEST")
    print("=" * 80)
    
    om = OnboardingManager()
    today = date.today()
    
    test_cases = [
        # (sleep_hours, wake_time, test_time_before_bed, test_time_after_bed)
        (5.0, "07:00", "01:30", "02:30"),  # Bedtime 02:00 - test before and after
        (5.0, "08:00", "02:30", "03:30"),  # Bedtime 03:00
        (3.0, "09:00", "05:30", "06:30"),  # Bedtime 06:00
        (7.0, "07:00", "23:30", "00:30"),  # Bedtime 00:00 (midnight)
    ]
    
    for sleep_hrs, wake_str, time_before_str, time_after_str in test_cases:
        print(f"\n  Sleep {sleep_hrs}h, Wake {wake_str}, Bedtime {om.calculate_bedtime(om.parse_wake_time(wake_str), sleep_hrs).strftime('%H:%M')}")
        print("  " + "-" * 70)
        
        wake_time = om.parse_wake_time(wake_str)
        bedtime = om.calculate_bedtime(wake_time, sleep_hrs)
        
        # Test time before bedtime
        hour_before, min_before = map(int, time_before_str.split(':'))
        time_before = datetime.combine(today, datetime.min.time().replace(hour=hour_before, minute=min_before))
        
        # Test time after bedtime  
        hour_after, min_after = map(int, time_after_str.split(':'))
        time_after = datetime.combine(today, datetime.min.time().replace(hour=hour_after, minute=min_after))
        
        # For times very late at night (after midnight), adjust date
        if hour_before < hour_after and hour_before < 6:
            # Likely crossed midnight
            time_before = time_before + timedelta(days=1)
        
        hours_until_bed_before = om.get_hours_until_bedtime(time_before, wake_time, sleep_hrs)
        hours_until_bed_after = om.get_hours_until_bedtime(time_after, wake_time, sleep_hrs)
        
        print(f"    At {time_before_str}: {hours_until_bed_before:.1f}h until bedtime", end="")
        if hours_until_bed_before < 0:
            print(" ✗ NEGATIVE!")
        else:
            print(" ✓")
        
        print(f"    At {time_after_str}: {hours_until_bed_after:.1f}h until bedtime", end="")
        if hours_until_bed_after < 0:
            print(" ✗ NEGATIVE!")
        else:
            print(" ✓")
        
        # Check logic: time_after should have LESS time until bed than time_before
        if time_after > time_before and hours_until_bed_after >= hours_until_bed_before:
            print(f"    ✗ LOGIC ERROR: Later time shouldn't have more time left until bed")


if __name__ == "__main__":
    test_realtime_budget_edge_cases()
    test_bedtime_boundary_logic()
    
    print("\n" + "=" * 80)
    print("REAL-TIME EDGE CASE TESTING COMPLETE")
    print("=" * 80 + "\n")
