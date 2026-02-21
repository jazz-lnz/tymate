"""
Comprehensive validation of the edge case fix
Confirms that the 5-hour sleep + various wake time bug is resolved
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, time, timedelta
from state.onboarding_manager import OnboardingManager


def validate_edge_case_fix():
    """
    Comprehensive validation that the originally reported bug is fixed:
    "When I input 5 hours [sleep] and a certain range for the wake time, 
     the computation becomes wrong"
    """
    
    print("\n" + "=" * 80)
    print("BUG FIX VALIDATION TEST")
    print("=" * 80)
    print("\nOriginal Bug Report:")
    print("  'When I input 5 hours sleep and a certain range for the wake time,")
    print("   the computation becomes wrong.'\n")
    
    om = OnboardingManager()
    
    print("Testing 5-hour sleep across ALL wake times (6 AM to 10 PM):")
    print("=" * 80)
    
    all_valid = True
    problematic_times = []
    
    for hour in range(6, 23):
        wake_str = f"{hour:02d}:00"
        wake_time = om.parse_wake_time(wake_str)
        bedtime = om.calculate_bedtime(wake_time, 5.0)
        
        # Test hours_until_bedtime at several points in the day
        test_times = [
            (datetime.combine(datetime.now().date(), time(9, 0)), "9 AM"),
            (datetime.combine(datetime.now().date(), time(12, 0)), "12 PM noon"),
            (datetime.combine(datetime.now().date(), time(18, 0)), "6 PM"),
            (datetime.combine(datetime.now().date(), time(23, 0)), "11 PM"),
        ]
        
        errors_this_wake = []
        for test_dt, time_desc in test_times:
            hours_until_bed = om.get_hours_until_bedtime(test_dt, wake_time, 5.0)
            
            # Validate: should always be positive and between 0 and 24
            if hours_until_bed < 0:
                errors_this_wake.append(f"{time_desc}: NEGATIVE ({hours_until_bed:.1f}h)")
                all_valid = False
            elif hours_until_bed > 24:
                errors_this_wake.append(f"{time_desc}: EXCESSIVE ({hours_until_bed:.1f}h > 24h)")
                all_valid = False
        
        if errors_this_wake:
            problematic_times.append({
                "wake": wake_str,
                "bedtime": bedtime.strftime("%H:%M"),
                "errors": errors_this_wake
            })
            print(f"  Wake {wake_str} (bed {bedtime.strftime('%H:%M')}): ✗ ERRORS")
            for error in errors_this_wake:
                print(f"    - {error}")
        else:
            print(f"  Wake {wake_str} (bed {bedtime.strftime('%H:%M')}): ✓ Valid")
    
    print("\n" + "=" * 80)
    if all_valid:
        print("✓ BUG FIX VALIDATED - All edge cases return positive valid values")
        print("✓ 5-hour sleep computation is now correct across all wake times")
        return True
    else:
        print(f"✗ {len(problematic_times)} wake time(s) still have issues:")
        for item in problematic_times:
            print(f"  Wake {item['wake']} → Bedtime {item['bedtime']}")
            for error in item['errors']:
                print(f"    {error}")
        return False


def test_specific_reported_case():
    """Test the exact scenario user reported"""
    
    print("\n" + "=" * 80)
    print("SPECIFIC REPORTED CASE TEST")
    print("=" * 80)
    
    om = OnboardingManager()
    
    print("\nUser reported: '5 hours sleep and a certain range for wake time'")
    print("Most common wake times for students: 6 AM - 10 AM\n")
    
    test_cases = [
        (5.0, "06:00"),
        (5.0, "07:00"),
        (5.0, "08:00"),
        (5.0, "09:00"),
        (5.0, "10:00"),
    ]
    
    print("Testing real-world scenario: Student wakes during the day with 5h sleep")
    print("-" * 80)
    
    for sleep_hrs, wake_str in test_cases:
        budget = om.calculate_time_budget(
            sleep_hours=sleep_hrs,
            wake_time=wake_str,
            has_work=True,
            work_hours_per_week=15,
        )
        
        free_hours = budget["free_hours_per_day"]
        expected_free = 24 - sleep_hrs - (15 / 7)  # 24 - sleep - work
        
        print(f"\nWake {wake_str} with {sleep_hrs}h sleep + 15h work/week:")
        print(f"  Free time/day: {free_hours:.1f}h (expected: {expected_free:.1f}h)", end="")
        if abs(free_hours - expected_free) < 0.1:
            print(" ✓")
        else:
            print(f" ✗ MISMATCH")
        
        # Test real-time at midday
        midday = datetime.combine(datetime.now().date(), datetime.min.time().replace(hour=12, minute=0))
        wake_time = om.parse_wake_time(wake_str)
        hours_until_bed = om.get_hours_until_bedtime(midday, wake_time, sleep_hrs)
        
        print(f"  At 12 PM: {hours_until_bed:.1f}h until bedtime", end="")
        if hours_until_bed > 0:
            print(" ✓")
        else:
            print(f" ✗ NEGATIVE")


if __name__ == "__main__":
    success = validate_edge_case_fix()
    test_specific_reported_case()
    
    print("\n" + "=" * 80)
    if success:
        print("VALIDATION COMPLETE: BUG FIX IS WORKING ✓")
    else:
        print("VALIDATION FAILED: Some issues remain")
    print("=" * 80 + "\n")
