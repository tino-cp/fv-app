def hours_to_hhmm(hours: float) -> str:
    """Convert a floating-point hour value (e.g., 14.5) to HH:MM (e.g., '14:30')."""
    h, m = divmod(round(hours * 60), 60)
    return f"{h:02}:{m:02}"
