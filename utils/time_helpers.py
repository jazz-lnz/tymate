import math
import re


def format_minutes(minutes: int | float | None) -> str:
    """Convert minutes to human-readable Xh Ym format, preserving sub-minute precision."""
    if minutes is None or minutes == 0:
        return "0m"

    if isinstance(minutes, float) and not minutes.is_integer():
        total_seconds = int(round(minutes * 60))
        if total_seconds < 60:
            return f"{total_seconds}s"
        hours = total_seconds // 3600
        remaining_seconds = total_seconds % 3600
        mins = remaining_seconds // 60
        secs = remaining_seconds % 60
        if hours > 0:
            if secs > 0:
                return f"{hours}h {mins}m {secs}s" if mins > 0 else f"{hours}h {secs}s"
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        if secs > 0:
            return f"{mins}m {secs}s"
        return f"{mins}m"

    minutes_int = int(minutes)
    if minutes_int < 60:
        return f"{minutes_int}m"
    h = minutes_int // 60
    m = minutes_int % 60
    return f"{h}h {m}m" if m > 0 else f"{h}h"


def parse_time_input(time_str: str) -> float | None:
    """Parse user input like '2h 30m', '90m', '1.5h', or '45s' into total minutes."""
    if not time_str:
        return None

    normalized = time_str.strip().lower()
    if not normalized:
        return None

    if normalized.isdigit():
        return int(normalized)

    token_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*([hms])")
    matches = list(token_pattern.finditer(normalized))
    if not matches:
        return None

    remaining = token_pattern.sub("", normalized).strip()
    if remaining:
        return None

    total_minutes = 0.0
    for match in matches:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == "h":
            total_minutes += value * 60
        elif unit == "s":
            total_minutes += value / 60
        else:
            total_minutes += value

    return total_minutes