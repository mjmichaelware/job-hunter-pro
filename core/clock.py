from datetime import datetime, timezone, timedelta

def utc_now() -> datetime:
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    """Returns the current time in UTC as an ISO 8601 string."""
    return utc_now().replace(microsecond=0).isoformat()

def get_display_timezone():
    """Returns America/Denver timezone object. Placeholder for future tz handling."""
    # In a real app, this might come from user preferences.
    # For now, it's fixed as per project context.
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("America/Denver")
    except ImportError:
        # Fallback for older Python
        return timezone(timedelta(hours=-6))

def to_display_time(dt: datetime) -> str:
    """Converts a UTC datetime to a display string in the project's timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    display_tz = get_display_timezone()
    return dt.astimezone(display_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
