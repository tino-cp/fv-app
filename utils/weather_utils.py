from datetime import datetime, timezone as dt_timezone, timedelta
import discord
from pytz import timezone as pytz_timezone

from globals import DEFAULT_TIMEZONE_STR, epoch, GAME_HOUR_LENGTH, WEEKDAYS, WEATHER_PERIOD, ORANGE, COUNTER_CLOCKWISE
from models.weather import GTATime, Weather, WEATHER_STATE_CHANGES, WEATHER_STATES, RainETA, WeatherState

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

def to_discord_timestamp(date_time: datetime, time_format: str = 'F') -> str:
    """
    Convert a datetime object to a Discord timestamp format.
    :param date_time: The datetime object to convert.
    :param time_format: The format for the timestamp (default: 'F').
    :return: A string in the format <t:unix_timestamp:format>.
    """
    unix_timestamp = int(date_time.timestamp())
    return f"<t:{unix_timestamp}:{time_format}>"


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