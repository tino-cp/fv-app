from pytz import timezone as pytz_timezone
from datetime import datetime, timezone as dt_timezone

epoch: datetime = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)  # used to get total_seconds

ALIASES = ['current_weather', 'future_forecast']

EMBED_TYPES = [  # Supported embed types for reactions
    'current_weather', 'future_timezone_selection', 'future_weather_date'
]

WEEKDAYS = [  # Weekday names
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

TIME_ZONES = {  # Mapping of key time zones by region and city
    "North America": {"Los Angeles": "US/Pacific", "Denver": "US/Mountain", "Chicago": "US/Central", "New York": "US/Eastern"},
    "South America": {"Buenos Aires": "America/Argentina/Buenos_Aires"},
    "Europe": {"UTC": "UTC", "London": "Europe/London", "Amsterdam": "Europe/Amsterdam"},
    "Asia": {"Vientiane": "Asia/Vientiane", "Japan": "Japan"},
    "Australia": {"Queensland": "Australia/Queensland", "Sydney": "Australia/Sydney"}
}

DEFAULT_TIMEZONE_STR = "UTC"
DEFAULT_TIMEZONE = pytz_timezone(DEFAULT_TIMEZONE_STR)

WEATHER_PERIOD = 384  # Number of in-game hours per weather cycle
GAME_HOUR_LENGTH = 120  # IRL seconds per in-game hour
SUNRISE_TIME = 5  # In-game sunrise hour
SUNSET_TIME = 21  # In-game sunset hour

ORANGE = int(0xF03C00)
RAIN_ETA_LABEL = "Rain ETA"
RAIN_LENGTH_LABEL = "Rain Length"
COUNTER_CLOCKWISE = "🔄"
CALENDAR = "📆"
MOON = "🌙"

bot_state = {}

