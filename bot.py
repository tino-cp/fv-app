import os
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
import discord
from discord.ext import commands
from pytz import timezone as pytz_timezone
from dotenv import load_dotenv
import aiohttp

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

class Weather:
    def __init__(self, name: str, emoji: str, day_thumbnail: str, night_thumbnail: str):
        self.name = name
        self.emoji = emoji
        self.day_thumbnail = day_thumbnail
        self.night_thumbnail = night_thumbnail


# Represents GTA game time and its related attributes
class GTATime:
    def __init__(self, hours_game_time: float, weekday, weather_period_time: float):
        self.hours_game_time = hours_game_time
        self.str_game_time = hours_to_hhmm(self.hours_game_time)
        self.weekday = weekday
        self.weather_period_time = weather_period_time
        self.is_day_time = SUNRISE_TIME <= self.hours_game_time < SUNSET_TIME


# Represents rain estimation details (ETA)
class RainETA:
    def __init__(self, sec_eta: int, is_raining: bool):
        self.sec_eta = sec_eta
        self.str_eta = self.seconds_to_verbose_interval()
        self.is_raining = is_raining

    def seconds_to_verbose_interval(self):
        if self.sec_eta < 60:
            return 'Less than 1 minute'

        minutes, seconds_left = divmod(int(self.sec_eta), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            hours_suffix = "s" if hours > 1 else ""
            hours_str = f"{hours} hour{hours_suffix}"
        else:
            hours_str = ''

        if minutes > 0:
            minutes_suffix = "s" if minutes > 1 else ""
            minutes_str = f"{minutes} minute{minutes_suffix}"
        else:
            minutes_str = ''

        if hours_str and minutes_str:
            return f"{hours_str} and {minutes_str}"

        elif hours_str and not minutes_str:
            return hours_str

        return minutes_str

    def get_rain_eta_irl_time(self, current_time: datetime, timezone_str: str) -> str:
        """
        Calculate the IRL time when the rain will arrive, in the specified timezone.
        """
        if self.sec_eta == 0:
            return 'No rain'

        eta_time = current_time + timedelta(seconds=self.sec_eta)
        eta_time_tz = convert_to_timezone(eta_time, timezone_str)
        return format_datetime(eta_time_tz)

class WeatherState:
    """Represents the full current weather conditions"""
    def __init__(self, weather_instance: Weather, gta_time: GTATime, rain_eta: RainETA):
        self.weather = weather_instance
        self.gta_time = gta_time
        self.rain_eta = rain_eta

# Weather states with all conditions
WEATHER_STATES = {
    'clear': Weather(
        "Clear", "☀️", "https://i.imgur.com/LerUU1Z.png", "https://i.imgur.com/waFNkp1.png"
    ),
    'raining': Weather(
        "Raining", "🌧️", "https://i.imgur.com/qsAl41k.png", "https://i.imgur.com/jc98A0G.png"
    ),
    'drizzling': Weather(
        "Drizzling", "🌦️", "https://i.imgur.com/Qx18aHp.png", "https://i.imgur.com/EWSCz5d.png"
    ),
    'misty': Weather(
        "Misty", "🌁", "https://i.imgur.com/mjZwX2A.png", "https://i.imgur.com/Mh1PDXS.png"
    ),
    'foggy': Weather(
        "Foggy", "🌫️", "https://i.imgur.com/mjZwX2A.png", "https://i.imgur.com/Mh1PDXS.png"
    ),
    'hazy': Weather(
        "Hazy", "🌫️", "https://i.imgur.com/mjZwX2A.png", "https://i.imgur.com/Mh1PDXS.png"
    ),
    'snowy': Weather(
        "Snowy", "❄️", "https://i.imgur.com/WJEjWM6.png", "https://i.imgur.com/1TxfthS.png"
    ),
    'cloudy': Weather(
        "Cloudy", "☁️", "https://i.imgur.com/1oMUp2V.png", "https://i.imgur.com/qSOc8XX.png"
    ),
    'mostly_cloudy': Weather(
        "Mostly cloudy", "🌥️", "https://i.imgur.com/aY4EQhE.png", "https://i.imgur.com/2LIbOFC.png"
    ),
    'partly_cloudy': Weather(
        "Partly cloudy", "⛅", "https://i.imgur.com/aY4EQhE.png", "https://i.imgur.com/2LIbOFC.png"
    ),
    'mostly_clear': Weather(
        "Mostly clear", "🌤️", "https://i.imgur.com/aY4EQhE.png", "https://i.imgur.com/2LIbOFC.png"
    )
}

# Weather state changes based on the game time
WEATHER_STATE_CHANGES = [
    [0, WEATHER_STATES['partly_cloudy']],
    [4, WEATHER_STATES['misty']],
    [7, WEATHER_STATES['mostly_cloudy']],
    [11, WEATHER_STATES['clear']],
    [14, WEATHER_STATES['misty']],
    [16, WEATHER_STATES['clear']],
    [28, WEATHER_STATES['misty']],
    [31, WEATHER_STATES['clear']],
    [41, WEATHER_STATES['hazy']],
    [45, WEATHER_STATES['partly_cloudy']],
    [52, WEATHER_STATES['misty']],
    [55, WEATHER_STATES['cloudy']],
    [62, WEATHER_STATES['foggy']],
    [66, WEATHER_STATES['cloudy']],
    [72, WEATHER_STATES['partly_cloudy']],
    [78, WEATHER_STATES['foggy']],
    [82, WEATHER_STATES['cloudy']],
    [92, WEATHER_STATES['mostly_clear']],
    [104, WEATHER_STATES['partly_cloudy']],
    [105, WEATHER_STATES['drizzling']],
    [108, WEATHER_STATES['partly_cloudy']],
    [125, WEATHER_STATES['misty']],
    [128, WEATHER_STATES['partly_cloudy']],
    [131, WEATHER_STATES['raining']],
    [134, WEATHER_STATES['drizzling']],
    [137, WEATHER_STATES['cloudy']],
    [148, WEATHER_STATES['misty']],
    [151, WEATHER_STATES['mostly_cloudy']],
    [155, WEATHER_STATES['foggy']],
    [159, WEATHER_STATES['clear']],
    [176, WEATHER_STATES['mostly_clear']],
    [196, WEATHER_STATES['foggy']],
    [201, WEATHER_STATES['partly_cloudy']],
    [220, WEATHER_STATES['misty']],
    [222, WEATHER_STATES['mostly_clear']],
    [244, WEATHER_STATES['misty']],
    [247, WEATHER_STATES['raining']],
    [250, WEATHER_STATES['drizzling']],
    [252, WEATHER_STATES['partly_cloudy']],
    [268, WEATHER_STATES['misty']],
    [270, WEATHER_STATES['partly_cloudy']],
    [272, WEATHER_STATES['cloudy']],
    [277, WEATHER_STATES['partly_cloudy']],
    [292, WEATHER_STATES['misty']],
    [295, WEATHER_STATES['partly_cloudy']],
    [300, WEATHER_STATES['mostly_cloudy']],
    [306, WEATHER_STATES['partly_cloudy']],
    [318, WEATHER_STATES['mostly_cloudy']],
    [330, WEATHER_STATES['partly_cloudy']],
    [337, WEATHER_STATES['clear']],
    [367, WEATHER_STATES['partly_cloudy']],
    [369, WEATHER_STATES['raining']],
    [376, WEATHER_STATES['drizzling']],
    [377, WEATHER_STATES['partly_cloudy']]
]

def hours_to_hhmm(hours: float) -> str:
    """Convert a floating-point hour value (e.g., 14.5) to HH:MM (e.g., '14:30')."""
    h, m = divmod(round(hours * 60), 60)
    return f"{h:02}:{m:02}"

def smart_day_time_format(date_format: str, dt: datetime) -> str:
    """
    :param date_format: day in format should be {S}
    :param dt: datetime
    :return: formatted time as String
    """

    return dt.strftime(date_format).replace("{S}", f"{num_suffix(dt.day)}")

def num_suffix(num: int) -> str:
    """
    :param num: ex. 2
    :return: ex. 2nd
    """

    return f"{num}{'th' if 11 <= num <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')}"

def convert_to_timezone(date_time: datetime, timezone_str: str) -> datetime:
    """
    Convert a datetime object to the specified timezone.

    :param date_time: The original datetime object.
    :param timezone_str: The timezone to convert to.
    :return: A datetime object in the specified timezone.
    """
    target_timezone = pytz_timezone(timezone_str)
    return date_time.astimezone(target_timezone)

def format_datetime(date_time: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format a datetime object into a string according to a specified format.

    :param date_time: The datetime object to format.
    :param format_str: The format string (default: "%Y-%m-%d %H:%M:%S %Z").
    :return: A formatted datetime string.
    """
    return date_time.strftime(format_str)

def to_discord_timestamp(date_time: datetime, format: str = 'F') -> str:
    """
    Convert a datetime object to a Discord timestamp format.
    :param date_time: The datetime object to convert.
    :param format: The format for the timestamp (default: 'F').
    :return: A string in the format <t:unix_timestamp:format>.
    """
    unix_timestamp = int(date_time.timestamp())
    return f"<t:{unix_timestamp}:{format}>"

# Function to get GTA time
def get_gta_time(date: datetime, timezone: str = DEFAULT_TIMEZONE_STR) -> GTATime:
    if date.tzinfo is None:
        date = date.replace(tzinfo=dt_timezone.utc)
    localized_date = convert_to_timezone(date, timezone)
    timestamp: int = int((localized_date - epoch).total_seconds())
    total_gta_hours: float = timestamp / GAME_HOUR_LENGTH
    weekday = WEEKDAYS[int(total_gta_hours % 168 / 24) - 1]
    current_gta_hour: float = total_gta_hours % 24
    return GTATime(
        hours_game_time=current_gta_hour,
        weekday=weekday,
        weather_period_time=total_gta_hours % WEATHER_PERIOD
    )

# Function to get weather for a given time period
def get_weather_for_period_time(weather_period_time: float) -> Weather:
    for i, period in enumerate(WEATHER_STATE_CHANGES):
        if period[0] > weather_period_time:
            return WEATHER_STATE_CHANGES[i - 1][1]
    return WEATHER_STATE_CHANGES[-1][1]


# Function to check if it's raining
def check_is_raining(weather_instance: Weather):
    return weather_instance == WEATHER_STATES['raining'] or weather_instance == WEATHER_STATES['drizzling']


# Function to calculate rain ETA
def get_rain_eta(weather_period_time: float, weather_instance: Weather) -> RainETA:
    is_raining = check_is_raining(weather_instance)

    len_weather_state_changes = len(WEATHER_STATE_CHANGES)
    for i in range(len_weather_state_changes * 2):
        index = i % len_weather_state_changes
        offset = int(i / len_weather_state_changes) * WEATHER_PERIOD

        if WEATHER_STATE_CHANGES[index][0] + offset >= weather_period_time:
            if is_raining ^ check_is_raining(WEATHER_STATE_CHANGES[index][1]):
                return RainETA(
                    sec_eta=((WEATHER_STATE_CHANGES[index][0] + offset) - weather_period_time) * GAME_HOUR_LENGTH,
                    is_raining=is_raining
                )

    return RainETA(0, is_raining)

def get_next_rain_periods(start_time: datetime, weather_period_time: float, count: int) -> list[dict]:
    """
    Get the next rain periods in chronological order, ensuring unique results with IRL timestamps.
    :param start_time: The start time to calculate rain periods from.
    :param weather_period_time: The in-game weather period time.
    :param count: The number of rain periods to return.
    :return: A list of dictionaries containing rain period details.
    """
    result = []
    current_time = weather_period_time
    found_periods = 0

    # Extend WEATHER_STATE_CHANGES for wraparound handling
    extended_changes = WEATHER_STATE_CHANGES + [
        [change[0] + WEATHER_PERIOD, change[1]] for change in WEATHER_STATE_CHANGES
    ]

    # Sort changes based on period start time
    extended_changes.sort(key=lambda x: x[0])

    while found_periods < count:
        for i, (period_start, state) in enumerate(extended_changes):
            if period_start <= current_time:
                continue  # Skip periods in the past

            if check_is_raining(state):
                # Calculate rain start and duration
                next_index = (i + 1) % len(extended_changes)
                next_period_start = extended_changes[next_index][0]

                rain_start_irl = start_time + timedelta(
                    seconds=((period_start - weather_period_time) * GAME_HOUR_LENGTH)
                )
                rain_duration_seconds = (next_period_start - period_start) * GAME_HOUR_LENGTH
                rain_end_irl = rain_start_irl + timedelta(seconds=rain_duration_seconds)

                # Append the rain period details
                result.append({
                    'type': state.name,
                    'start_time': rain_start_irl.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': f"{rain_duration_seconds % 3600 // 60}m",
                    'end_time': rain_end_irl.strftime('%Y-%m-%d %H:%M:%S')
                })

                found_periods += 1
                current_time = period_start  # Move current time to avoid duplicates
                break

    return result

def get_weather_state(date: datetime, timezone: str = DEFAULT_TIMEZONE_STR) -> WeatherState:
    gta_time: GTATime = get_gta_time(date, timezone)
    weather_instance: Weather = get_weather_for_period_time(gta_time.weather_period_time)
    rain_eta = get_rain_eta(gta_time.weather_period_time, weather_instance)

    return WeatherState(
        weather_instance, gta_time, rain_eta
    )

async def send_weather(message: discord.Message, timezone: str = DEFAULT_TIMEZONE_STR) -> discord.Message:
    utc_now = datetime.now(dt_timezone.utc)
    future_weather_state = get_weather_state(utc_now + timedelta(days=1), timezone)
    weather_state = get_weather_state(utc_now, timezone)

    rain_str = f"Rain will {'end' if weather_state.rain_eta.is_raining else 'begin'} in {weather_state.rain_eta.str_eta}."
    embed = discord.Embed(
        colour=discord.Colour(ORANGE),
        title=f'**It is {weather_state.weather.name.lower()} at {weather_state.gta_time.str_game_time}!**',
        description=f'{rain_str} {future_weather_state.weather.emoji}'
    )
    embed.set_thumbnail(
        url=weather_state.weather.day_thumbnail if weather_state.gta_time.is_day_time else weather_state.weather.night_thumbnail
    )
    msg = await message.channel.send(embed=embed)
    await msg.add_reaction(COUNTER_CLOCKWISE)
    return msg

async def fetch_closest_upcoming_round(series_start_date: datetime, current_time: datetime) -> int:
    """
    Fetches the closest upcoming round for a race series.
    """
    if series_start_date.tzinfo is None:
        series_start_date = series_start_date.replace(tzinfo=dt_timezone.utc)
    # Calculate the difference in days between the current time and the series start date
    days_since_start = (convert_to_timezone(current_time, DEFAULT_TIMEZONE_STR) - series_start_date).days

    # Determine the current round number
    round_number = max(1, days_since_start // 7 + 1)

    # Calculate the start time of the round
    race_start_time = series_start_date + timedelta(weeks=(round_number - 1))

    # If the current time has passed the race start time, move to the next round
    if race_start_time < current_time:
        round_number += 1

    return round_number

async def process_race_series(ctx, race_round: str, series_start_date: datetime, current_time: datetime, series: str = "f1"):
    if not race_round or not race_round.startswith("r") or not race_round[1:].isdigit():
        round_number = await fetch_closest_upcoming_round(series_start_date, current_time)
        race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
        await send_race_weather(ctx, race_start_time, series)
        return
    round_number = int(race_round[1:])
    race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
    await send_race_weather(ctx, race_start_time, series)

async def send_race_weather(ctx, race_start_time: datetime, series: str) -> None:
    """
    Sends a weather forecast for a specified race start time.
    :param ctx: The context of the command.
    :param race_start_time: The start time of the race as a datetime object.
    :param series: The racing series (e.g., F1 or F2).
    """
    try:
        # Get the weather for the exact time
        race_weather_state = get_weather_state(race_start_time)
        gta_time = get_gta_time(race_start_time)

        # Prepare and send an embed with weather details
        embed = discord.Embed(
            title=f"{series.upper()} Race Weather for {to_discord_timestamp(race_start_time, 'F')}",
            color=discord.Color(ORANGE)
        )
        embed.add_field(name="Weather", value=f"{race_weather_state.weather.name} {race_weather_state.weather.emoji}")

        # Calculate Rain ETA and Duration Safely
        rain_eta = get_rain_eta(
            weather_period_time=race_weather_state.gta_time.weather_period_time,
            weather_instance=race_weather_state.weather
        )

        # Ensure duration is converted to an integer for calculations
        rain_duration_seconds = rain_eta.sec_eta if rain_eta.is_raining else 0
        if not rain_eta.is_raining:
            next_rain_period = get_next_rain_periods(race_start_time, race_weather_state.gta_time.weather_period_time,
                                                     1)
            if next_rain_period and "duration" in next_rain_period[0]:
                duration_str = next_rain_period[0]["duration"]
                if duration_str.endswith("m"):
                    rain_duration_seconds = int(duration_str[:-1]) * 60

        rain_duration_minutes = rain_duration_seconds // 60
        if rain_duration_minutes >= 60:
            formatted_duration = f"{rain_duration_minutes // 60}h {rain_duration_minutes % 60}m"
        else:
            formatted_duration = f"{rain_duration_minutes}m"

        # Add fields to the embed
        embed.add_field(name=RAIN_ETA_LABEL, value=race_weather_state.rain_eta.str_eta)
        embed.add_field(name=RAIN_LENGTH_LABEL, value=f"It's going to be wet for {formatted_duration}")
        embed.set_thumbnail(
            url=race_weather_state.weather.day_thumbnail if gta_time.is_day_time else race_weather_state.weather.night_thumbnail
        )

        await ctx.send(embed=embed)

        # Add the 3 closest upcoming periods of rain as a separate embed
        next_three_rain_periods = get_next_rain_periods(race_start_time, race_weather_state.gta_time.weather_period_time, 3)

        rain_embed = discord.Embed(
            title=f"🌧️ {series.upper()} Race Rain Weather Forecast",
            color=discord.Color.blue()
        )

        for i, rain_info in enumerate(next_three_rain_periods):
            rain_start_time = datetime.strptime(rain_info['start_time'].replace(" UTC", ""),"%Y-%m-%d %H:%M:%S").replace(tzinfo=dt_timezone.utc)
            rain_end_time = datetime.strptime(rain_info['end_time'].replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt_timezone.utc)
            time_until_rain = rain_start_time - race_start_time
            hours, remainder = divmod(int(time_until_rain.total_seconds()), 3600)
            minutes = remainder // 60
            time_in_display = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"

            rain_embed.add_field(
                name=f"Next Rain #{i + 1}",
                value=f"**Type:** {rain_info.get('type', 'Unknown')} {WEATHER_STATES[rain_info.get('type', 'unknown').lower()].emoji}\n"
                      f"**ETA:** {time_in_display}\n"
                      f"**Duration:** {rain_info.get('duration', 'Unknown')}\n"
                      f"**Time:** {to_discord_timestamp(rain_start_time, 't')} - {to_discord_timestamp(rain_end_time, 't')}\n",
            )

        await ctx.send(embed=rain_embed)

    except Exception as e:
        await ctx.send(f"An error occurred while fetching the race weather: {str(e)}")

# Bot commands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def race(ctx, series: str = None, race_round: str = None):
    """
    Fetches the race weather for F1 or F2 schedules.
    Example usage:
      !race f1 r1
      !race f2 r2
    """
    series = (series or "f1").lower()
    race_round = race_round.lower() if race_round else None
    current_time = datetime.now(dt_timezone.utc)

    race_start_dates = {
        "f1": datetime(2025, 1, 5, 19, 0, tzinfo=dt_timezone.utc),
        "f2": datetime(2025, 1, 4, 19, 0, tzinfo=dt_timezone.utc)
    }

    if series in race_start_dates:
        race_start = race_start_dates[series]
        if not race_round:
            round_number = await fetch_closest_upcoming_round(race_start, current_time)
            race_round = f"r{round_number}"
        await process_race_series(ctx, race_round, race_start, current_time, series)
    else:
        await ctx.send("Invalid series! Please specify either 'f1' or 'f2'.")

@bot.command()
async def weather(ctx) -> None:
    """
    Displays weather information for the specified location or race.
    :param ctx: The context of the command.
    """
    try:
        # Fetch weather state based on location or default context
        current_time = datetime.now(dt_timezone.utc)
        gta_time = get_gta_time(current_time)
        weather_state = get_weather_state(current_time)

        # Prepare the embed for weather information
        embed = discord.Embed(
            title=f"Current Weather at {to_discord_timestamp(current_time)}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Weather", value=f"{weather_state.weather.name} {weather_state.weather.emoji}")

        # Calculate and display Rain ETA and Rain Duration
        rain_eta = get_rain_eta(
            weather_period_time=weather_state.gta_time.weather_period_time,
            weather_instance=weather_state.weather
        )

        # Handle rain duration logic
        rain_duration_seconds = 0  # Default to no rain
        if rain_eta.is_raining:
            rain_duration_seconds = rain_eta.sec_eta
        else:
            # Get the next rain period for future rain duration
            next_rain_period = get_next_rain_periods(current_time, weather_state.gta_time.weather_period_time, 1)
            if next_rain_period and "duration" in next_rain_period[0]:
                duration_str = next_rain_period[0]["duration"]  # e.g., "30m"
                if duration_str.endswith("m"):
                    # Strip "m" and calculate seconds
                    rain_duration_seconds = int(duration_str[:-1]) * 60

        # Format rain duration for display
        rain_duration_minutes = rain_duration_seconds // 60
        if rain_duration_minutes >= 60:
            formatted_duration = f"{rain_duration_minutes // 60}h {rain_duration_minutes % 60}m"
        else:
            formatted_duration = f"{rain_duration_minutes}m"

        # Add rain-related information to embed
        embed.add_field(name=RAIN_ETA_LABEL, value=weather_state.rain_eta.str_eta)
        embed.add_field(
            name=RAIN_LENGTH_LABEL,
            value=f"\nIt's going to be {'wet' if rain_duration_seconds > 0 else 'dry'} for {formatted_duration}"
        )
        # Add a thumbnail for weather time (day/night)
        embed.set_thumbnail(
            url=weather_state.weather.day_thumbnail if gta_time.is_day_time else weather_state.weather.night_thumbnail
        )
        embed.set_footer(text="React with 🔄 to refresh")

        current_weather_message = await ctx.send(embed=embed)
        bot_state[current_weather_message.id] = {
            "type": "current_weather_state",
            "time": current_time,
            "channel_id": ctx.channel.id
        }
        await current_weather_message.add_reaction(COUNTER_CLOCKWISE)

    except Exception as e:
        # Send user-friendly error if something fails during execution
        await ctx.send(f"An error occurred while fetching the weather: {str(e)}")

@bot.event
async def on_reaction_add(reaction, user):
    """
    Handles reactions for weather refresh.
    """
    if user.bot:
        return

    message_id = reaction.message.id
    if message_id not in bot_state:
        return

    metadata = bot_state[message_id]
    interaction_type = metadata["type"]

    # Handle the interaction type
    if interaction_type == "current_weather_state":
        # Handle refresh (🔄)
        if str(reaction.emoji) == COUNTER_CLOCKWISE:
            await refresh_weather(reaction.message)

async def refresh_weather(message):
    """
    Refresh the weather information for the given message.
    """
    try:
        # Fetch updated weather data
        current_time = datetime.now(dt_timezone.utc)
        weather_state = get_weather_state(current_time)

        # Access the existing embed
        embed = message.embeds[0]

        # Update fields in the embed
        embed.title = f"Current Weather at {to_discord_timestamp(current_time)}"
        embed.set_field_at(0, name="Weather", value=f"{weather_state.weather.name} {weather_state.weather.emoji}")
        embed.set_field_at(1, name=RAIN_ETA_LABEL, value=weather_state.rain_eta.str_eta)

        # Handle rain duration logic
        rain_duration_seconds = 0
        if weather_state.rain_eta.is_raining:
            rain_duration_seconds = weather_state.rain_eta.sec_eta
        else:
            # Get the next rain period if it exists
            next_rain_period = get_next_rain_periods(current_time, weather_state.gta_time.weather_period_time, 1)
            if next_rain_period and "duration" in next_rain_period[0]:
                duration_str = next_rain_period[0]["duration"]  # e.g., "30m"
                if duration_str.endswith("m"):
                    rain_duration_seconds = int(duration_str[:-1]) * 60  # Strip "m" and convert to seconds

        # Format rain duration
        rain_duration_minutes = rain_duration_seconds // 60
        if rain_duration_minutes >= 60:
            formatted_duration = f"{rain_duration_minutes // 60}h {rain_duration_minutes % 60}m"
        else:
            formatted_duration = f"{rain_duration_minutes}m"

        # Update the rain length field in the embed
        embed.set_field_at(2, name=RAIN_LENGTH_LABEL, value=f"\nIt's going to be {'wet' if rain_duration_seconds > 0 else 'dry'} for {formatted_duration}")

        # Edit the message with the updated embed
        await message.edit(embed=embed)

    except Exception as e:
        # Handle errors during the refresh
        await message.channel.send(f"An error occurred while refreshing the weather: {str(e)}")


@bot.command(name='rain', help='Get the upcoming rain periods.')
async def rain(ctx):
    """
    Fetches the next 4 upcoming periods of rain and sends them in an embed.
    """
    current_time = datetime.now(dt_timezone.utc)
    weather_state = get_weather_state(current_time)
    next_four_rain_periods = get_next_rain_periods(current_time, weather_state.gta_time.weather_period_time, 4)

    if not next_four_rain_periods:
        fallback_embed = discord.Embed(
            title="🌦️ Rain Forecast",
            description="No rain periods found in the upcoming future.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=fallback_embed)
        return

    rain_forecast_embed = discord.Embed(
        title=f"🌧️ Next Rain Periods {to_discord_timestamp(datetime.now(dt_timezone.utc), 'F')}",
        color=discord.Color.blue()
    )

    for i, rain_info in enumerate(next_four_rain_periods):
        # Convert strings to datetime objects
        rain_start_time = datetime.strptime(rain_info['start_time'].replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=dt_timezone.utc)
        rain_end_time = datetime.strptime(rain_info['end_time'].replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=dt_timezone.utc)

        now = datetime.now(dt_timezone.utc)  # Get the current UTC time

        # Calculate the time until the rain starts
        time_until_rain = rain_start_time - now
        hours, remainder = divmod(int(time_until_rain.total_seconds()), 3600)
        minutes = remainder // 60

        # Explicitly cast hours and minutes to integers and format the string
        time_in_display = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"

        rain_forecast_embed.add_field(
            name=f"Rain Period {i + 1}",
            value=f"**Type:** {rain_info.get('type', 'Unknown')}\n"
                  f"**{RAIN_ETA_LABEL}:** {time_in_display}\n"
                  f"**Duration:** {rain_info.get('duration', 'Unknown')}\n"
                  f"**Time:** {to_discord_timestamp(rain_start_time, 't')} - {to_discord_timestamp(rain_end_time, 't')}\n",
            inline=False
        )

    await ctx.send(embed=rain_forecast_embed)

@bot.command(name="help")
async def show_help(ctx):
    """
    Custom help command displaying bot commands in an embed.
    """
    embed = discord.Embed(
        title="Race Weather Commands",
        description="Here are the available commands for this bot:",
        color=discord.Color.blue()  # Use a suitable color for the embed
    )

    # Add command descriptions
    embed.add_field(
        name="`!race <league> <round>`",
        value=(
            "Retrieve weather conditions at the start of a race.\n"
            "**Leagues**: `f1`, `f2`\n"
            "**Rounds**: `r1`, `r2`, `r3`, etc.\n\n"
            "If no round is specified (e.g., `!race f1` or `!race f2`), "
            "it defaults to the nearest upcoming round.\n\n"
            "Example: `!race f1 r1`"
        ),
        inline=False
    )

    embed.add_field(
        name="`!weather`",
        value="Get the current weather conditions for the location.",
        inline=False
    )

    embed.add_field(
        name="`!rain`",
        value="Shows 5 periods of upcoming rain forecasts at your location.",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.after_invoke
async def fetch_message_history(ctx):
    """
    Fetch the last 10 messages in the channel whenever a command is invoked.
    """
    try:
        # Fetch last 10 messages from the channel
        messages = []
        async for msg in ctx.channel.history(limit=50):
            messages.append(msg)

        # Format the messages
        message_log = '\n'.join([f"[{msg.author.display_name}]: {msg.content}" for msg in messages])

        # Send the messages to the Google Sheet webhook
        async with aiohttp.ClientSession() as session:
            webhook_url = "https://script.google.com/macros/s/AKfycbzbyLfB5xWSeoFy2lIIAVdGP0BFWezE2v3OnTNMXghjaqg4iGIos5IVSkGsOVqisiDT/exec?gid=0"
            payload = {'messages': message_log}
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    pass

    except Exception as e:
        print(f"Error fetching messages: {e}")


# Start the bot with the token from your .env file
bot.run(os.getenv('DISCORD_TOKEN'))
