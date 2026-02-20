import re


def format_minutes(minutes: int | None) -> str:
    """Convert minutes to human-readable Xh Ym format"""
    if minutes is None or minutes == 0:
        return "0m"
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m > 0 else f"{h}h"


def parse_time_input(time_str: str) -> int | None:
    """Parse user input like '2h 30m', '90m', '1.5h' into total minutes"""
    if not time_str:
        return None

    normalized = time_str.strip().lower()
    if not normalized:
        return None

    if normalized.isdigit():
        return int(normalized)

    token_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*([hm])")
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
        else:
            total_minutes += value

    return int(round(total_minutes))