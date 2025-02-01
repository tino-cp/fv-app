# utils/common_utils.py
from datetime import datetime, timedelta
from pytz import timezone as pytz_timezone

def hours_to_hhmm(hours: float) -> str:
    """Convert a floating-point hour value (e.g., 14.5) to HH:MM (e.g., '14:30')."""
    h, m = divmod(round(hours * 60), 60)
    return f"{h:02}:{m:02}"
#
# def convert_to_timezone(date_time: datetime, timezone_str: str) -> datetime:
#     """
#     Convert a datetime object to the specified timezone.
#     :param date_time: The original datetime object.
#     :param timezone_str: The timezone to convert to.
#     :return: A datetime object in the specified timezone.
#     """
#     target_timezone = pytz_timezone(timezone_str)
#     return date_time.astimezone(target_timezone)

# def format_datetime(date_time: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
#     """
#     Format a datetime object into a string according to a specified format.
#     :param date_time: The datetime object to format.
#     :param format_str: The format string (default: "%Y-%m-%d %H:%M:%S %Z").
#     :return: A formatted datetime string.
#     """
#     return date_time.strftime(format_str)

# def seconds_to_verbose_interval(sec_eta: int) -> str:
#     if sec_eta < 60:
#         return 'Less than 1 minute'
#
#     minutes, seconds_left = divmod(int(sec_eta), 60)
#     hours, minutes = divmod(minutes, 60)
#
#     if hours > 0:
#         hours_suffix = "s" if hours > 1 else ""
#         hours_str = f"{hours} hour{hours_suffix}"
#     else:
#         hours_str = ''
#
#     if minutes > 0:
#         minutes_suffix = "s" if minutes > 1 else ""
#         minutes_str = f"{minutes} minute{minutes_suffix}"
#     else:
#         minutes_str = ''
#
#     if hours_str and minutes_str:
#         return f"{hours_str} and {minutes_str}"
#
#     elif hours_str and not minutes_str:
#         return hours_str
#
#     return minutes_str
#
# def get_rain_eta_irl_time(sec_eta: int, current_time: datetime, timezone_str: str) -> str:
#     """
#     Calculate the IRL time when the rain will arrive, in the specified timezone.
#     """
#     if sec_eta == 0:
#         return 'No rain'
#
#     eta_time = current_time + timedelta(seconds=sec_eta)
#     eta_time_tz = convert_to_timezone(eta_time, timezone_str)
#     return format_datetime(eta_time_tz)