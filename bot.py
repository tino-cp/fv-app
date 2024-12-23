import os
import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any

import discord
from discord.ext import commands
from pytz import timezone as pytz_timezone
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('weather_bot')
logger.setLevel(logging.INFO)

ALIASES = ['current_weather', 'future_forecast']

EMBED_TYPES = [  # Supported embed types for reactions
    'current_weather', 'future_timezone_selection', 'future_weather_date'
]

WEATHER_PERIOD = 384  # Number of in-game hours per weather cycle
GAME_HOUR_LENGTH = 120  # IRL seconds per in-game hour
SUNRISE_TIME = 5  # In-game sunrise hour
SUNSET_TIME = 21  # In-game sunset hour

WEEKDAYS = [  # Weekday names
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

epoch: datetime = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)  # used to get total_seconds

TIME_ZONES = {  # Mapping of key time zones by region and city
    "North America": {"Los Angeles": "US/Pacific", "Denver": "US/Mountain", "Chicago": "US/Central", "New York": "US/Eastern"},
    "South America": {"Buenos Aires": "America/Argentina/Buenos_Aires"},
    "Europe": {"UTC": "UTC", "London": "Europe/London", "Amsterdam": "Europe/Amsterdam"},
    "Asia": {"Vientiane": "Asia/Vientiane", "Japan": "Japan"},
    "Australia": {"Queensland": "Australia/Queensland", "Sydney": "Australia/Sydney"}
}

ORANGE = int(0xF03C00)
ZERO_WIDTH = chr(8203)  # Zero-width character for spacing
SPACE_CHAR = "⠀"
HEAVY_CHECKMARK = "✔"
BALLOT_CHECKMARK = "☑️"
WRENCH = "🔧"
FLAG_ON_POST = "🚩"
COUNTER_CLOCKWISE = "🔄"
CALENDAR = "📆"
RAIN_WITH_SUN = "🌦️"

MOON = "🌙"
BOOKS = "📚"
THUMBSUP = "👍"
THUMBSDOWN = "👎"
SHRUG = "🤷"
ORANGE_HEART = "🧡"
NUMBERS_EMOJIS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
LETTERS_EMOJIS = {  # Emoji mapping for letters (A-Z) and additional special characters
    "a": "🇦", "b": "🇧", "c": "🇨", "d": "🇩", "e": "🇪", "f": "🇫", "g": "🇬", "h": "🇭", "i": "🇮",
    "j": "🇯", "k": "🇰", "l": "🇱", "m": "🇲", "n": "🇳", "o": "🇴", "p": "🇵", "q": "🇶", "r": "🇷",
    "s": "🇸", "t": "🇹", "u": "🇺", "v": "🇻", "w": "🇼", "x": "🇽", "y": "🇾", "z": "🇿", "?": "❔"
}

bot_state = {}

def hours_to_hhmm(hours: float) -> str:
    """Convert a floating-point hour value (e.g., 14.5) to HH:MM (e.g., '14:30')."""
    h, m = divmod(round(hours * 60), 60)
    return f"{h:02}:{m:02}"


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

        minutes = self.sec_eta % 60
        hours = int(self.sec_eta / 3600 + (minutes / 6000))
        minutes = int((self.sec_eta - (hours * 3600)) / 60 + (minutes / 60))

        hours_str = f"{hours} hour{'s' if hours > 1 else ''}" if hours > 0 else ''
        minutes_str = f"{minutes} minute{'s' if minutes > 1 else ''}" if minutes > 0 else ''

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
        tz = pytz_timezone(timezone_str)
        eta_time_tz = eta_time.astimezone(tz)
        return eta_time_tz.strftime("%Y-%m-%d %H:%M:%S")

class WeatherState:
    """Represents the full current weather conditions"""
    def __init__(self, gta_weather: Weather, gta_time: GTATime, rain_eta: RainETA):
        self.weather = gta_weather
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


async def handle_reaction_add(
        msg: discord.Message,
        emoji: str,
        embed_meta: str = ""
) -> None:
    embed_type = embed_meta.split('type=')[1].split('/')[0]

    if embed_type == 'current_weather_state':

        if emoji == COUNTER_CLOCKWISE:
            await send_weather(msg)


async def handle_reaction_remove(
        msg: discord.Message,
        emoji: str,
        embed_meta: str = ""
) -> None:
    embed_type = embed_meta.split('type=')[1].split('/')[0]

    if embed_type == 'current_weather_state':

        if emoji == COUNTER_CLOCKWISE:
            await send_weather(msg)


# Function to get GTA time
def get_gta_time(date: datetime) -> GTATime:
    if date.tzinfo is None:
        date = date.replace(tzinfo=dt_timezone.utc)
    timestamp: int = int((date - epoch).total_seconds())
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
def check_is_raining(gta_weather: Weather):
    return gta_weather == WEATHER_STATES['raining'] or gta_weather == WEATHER_STATES['drizzling']


# Function to calculate rain ETA
def get_rain_eta(weather_period_time: float, gta_weather: Weather) -> RainETA:
    is_raining = check_is_raining(gta_weather)

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

def get_next_rain_periods(weather_period_time: float, count: int) -> list[dict]:
    """
    Get the next rain periods in chronological order, ensuring unique results with IRL timestamps.
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

                rain_start_irl = datetime.now(dt_timezone.utc) + timedelta(
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



def get_gta_time_from_input(input_datetime: datetime) -> GTATime:
    timestamp: int = int((input_datetime - epoch).total_seconds())
    total_gta_hours: float = timestamp / GAME_HOUR_LENGTH
    weekday = WEEKDAYS[int(total_gta_hours % 168 / 24) - 1]
    current_gta_hour: float = total_gta_hours % 24
    return GTATime(current_gta_hour, weekday, total_gta_hours % WEATHER_PERIOD)


def get_forecast(date: datetime, hours=4) -> list[list[datetime | WeatherState | Any]]:
    weather_states = []

    d = date
    previous_weather_name = None
    while d < date + timedelta(hours=hours):
        weather_state = get_weather_state(d)

        if weather_state.weather.name != previous_weather_name:
            weather_states.append([d, weather_state])
            previous_weather_name = weather_state.weather.name

        d += timedelta(minutes=1)

    return weather_states


def get_weather_state(date: datetime) -> WeatherState:
    gta_time: GTATime = get_gta_time(date)
    gta_weather: Weather = get_weather_for_period_time(gta_time.weather_period_time)
    rain_eta = get_rain_eta(gta_time.weather_period_time, gta_weather)

    return WeatherState(
        gta_weather, gta_time, rain_eta
    )

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


async def send_forecast(msg: discord.Message, forecast: list[list[datetime, WeatherState]], date):
    """
    Displays the forecast in an embed.
    """
    forecast_str = ""
    for dt, weather_state in forecast:
        dt = pytz_timezone("UTC").localize(dt).astimezone(date.tzinfo)
        forecast_str += f"{dt.strftime('%H:%M')} - " \
                        f"{weather_state.weather.emoji} {weather_state.weather.name}\n"

    embed = msg.embeds[0]
    embed.title = f"**Forecast for {date.strftime('%Y-%m-%d %H:%M %Z')}**"
    embed.description = f"```{forecast_str}```"

    await msg.edit(embed=embed)

async def send_weather(message: discord.Message) -> discord.Message:
    utc_now = datetime.now(dt_timezone.utc)
    weather_state = get_weather_state(utc_now)

    rain_str = f"Rain will {'end' if weather_state.rain_eta.is_raining else 'begin'} in {weather_state.rain_eta.str_eta}."
    embed = discord.Embed(
        colour=discord.Colour(ORANGE),
        title=f'**It is {weather_state.weather.name.lower()} at {weather_state.gta_time.str_game_time}!**',
        description=rain_str
    )
    embed.set_thumbnail(
        url=weather_state.weather.day_thumbnail if weather_state.gta_time.is_day_time else weather_state.weather.night_thumbnail
    )
    msg = await message.channel.send(embed=embed)
    await msg.add_reaction(COUNTER_CLOCKWISE)
    return msg

async def process_race_series(ctx, race_round: str, series_start_date: datetime, current_time: datetime):
    if not race_round or not race_round.startswith("r") or not race_round[1:].isdigit():
        # Automatically detect the closest upcoming round
        round_number = max(1, int((current_time - series_start_date).days // 7) + 1)
        race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
        if race_start_time < current_time:
            round_number += 1
            race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
        await ctx.send(f"No round specified. Closest upcoming round: r{round_number}.")
        await send_race_weather(ctx, race_start_time)
        return
    # If a specific round is mentioned
    round_number = int(race_round[1:])
    race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
    await send_race_weather(ctx, race_start_time)

async def send_race_weather(ctx, race_start_time: datetime) -> None:
    """
    Sends a weather forecast for a specified race start time.
    :param ctx: The context of the command.
    :param race_start_time: The start time of the race as a datetime object.
    """
    try:
        # Get the weather for the exact time
        race_weather_state = get_weather_state(race_start_time)
        gta_time = get_gta_time(race_start_time)

        # Prepare and send an embed with weather details
        embed = discord.Embed(
            title=f"Race Weather for {race_start_time.strftime('%d-%m-%Y %H:%M')} UTC",
            color=discord.Color(ORANGE)
        )
        embed.add_field(name="Weather", value=f"{race_weather_state.weather.name} {race_weather_state.weather.emoji}")

        # Calculate Rain ETA and Duration Safely
        rain_eta = get_rain_eta(
            weather_period_time=race_weather_state.gta_time.weather_period_time,
            gta_weather=race_weather_state.weather
        )

        # Ensure duration is converted to an integer for calculations
        if rain_eta.is_raining:
            rain_duration_seconds = rain_eta.sec_eta
        else:
            next_rain_period = get_next_rain_periods(race_weather_state.gta_time.weather_period_time, 1)
            if next_rain_period and "duration" in next_rain_period[0]:
                # Strip 'm' and convert to minutes as integer
                duration_str = next_rain_period[0]["duration"]
                if duration_str.endswith("m"):
                    rain_duration_minutes = int(
                        duration_str[:-1])  # Removes 'm' and converts the remaining number to int
                    rain_duration_seconds = rain_duration_minutes * 60
                else:
                    rain_duration_seconds = 0  # Default fallback in case there is no valid duration string
            else:
                rain_duration_seconds = 0  # Fallback to 0 if no valid duration is found

        rain_duration_minutes = rain_duration_seconds // 60
        if rain_duration_minutes >= 60:
            formatted_duration = f"{rain_duration_minutes // 60}h {rain_duration_minutes % 60}m"
        else:
            formatted_duration = f"{rain_duration_minutes}m"

        # Add fields to the embed
        embed.add_field(name="Rain ETA", value=race_weather_state.rain_eta.str_eta)
        embed.add_field(name="Rain Length", value=f"It's going to be wet for {formatted_duration}")
        embed.set_thumbnail(
            url=race_weather_state.weather.day_thumbnail if gta_time.is_day_time else race_weather_state.weather.night_thumbnail
        )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred while fetching the race weather: {str(e)}")


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def race(ctx, series: str = "f1", race_round: str = None):
    series = series.lower()
    race_round = race_round.lower() if race_round else None
    current_time = datetime.now(dt_timezone.utc)

    """
    Fetches the race weather for F1 or F2 schedules.
    Example usage:
      !race f1 r1
      !race f2 r2
    """
    if series == "f1":
        f1_race_start = datetime(2025, 1, 5, 19, 0)
        await process_race_series(ctx, race_round, f1_race_start, current_time)
    elif series == "f2":
        f2_race_start = datetime(2025, 1, 4, 19, 0)
        await process_race_series(ctx, race_round, f2_race_start, current_time)
    else:
        await ctx.send("Invalid series! Please specify 'f1' or 'f2'.")

@race.error
async def race_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You forgot to specify the series! Use `!race f1` or `!race f2`.")
    elif isinstance(error, ValueError):  # Added
        await ctx.send("Invalid round. Please specify a valid round number.")  # Added


@bot.command(name='weather', help='Fetch the current weather state only.')
async def weather(ctx):
    """
    Fetches the current weather state and sends it to the Discord channel.
    """
    current_time = datetime.now(dt_timezone.utc)
    gta_time = get_gta_time(current_time)
    weather_state = get_weather_state(current_time)
    future_weather_state = get_weather_state(
        current_time + timedelta(
            seconds=weather_state.rain_eta.sec_eta,
            minutes=1
        )
    )
# Generate the Current Weather embed
    current_weather_embed = discord.Embed(
        title="Current Weather",
        color=discord.Color.orange()
    )
    current_weather_embed.add_field(name="Weather", value=f"{weather_state.weather.name} {weather_state.weather.emoji}")
    current_weather_embed.add_field(name="Rain ETA", value=weather_state.rain_eta.str_eta)
    current_weather_embed.add_field(
        name="Rain Length",
        value=f"\nIt's going to be {'dry' if weather_state.rain_eta.is_raining else 'wet'} "
              f"for {future_weather_state.rain_eta.str_eta}."
    )
    current_weather_embed.set_thumbnail(
        url=weather_state.weather.day_thumbnail if gta_time.is_day_time else weather_state.weather.night_thumbnail
    )
    current_weather_embed.set_footer(text="React with 🔄 to refresh")

    # Send embed and track the message ID in bot_state
    current_weather_message = await ctx.send(embed=current_weather_embed)
    bot_state[current_weather_message.id] = {
        "type": "current_weather_state",
        "time": current_time,
        "channel_id": ctx.channel.id
    }
    await current_weather_message.add_reaction(COUNTER_CLOCKWISE)


@bot.event
async def on_reaction_add(reaction, user):
    """
    Handles reactions for weather refresh.
    """
    # Ignore bot reactions
    if user.bot:
        return

    # Check if the message ID is in bot_state
    message_id = reaction.message.id
    if message_id not in bot_state:
        return  # No metadata available, do nothing

    # Get the metadata for the message
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
    # Example: Use metadata to fetch updated weather data
    current_time = datetime.now(dt_timezone.utc)
    gta_time = get_gta_time(current_time)
    weather_state = get_weather_state(current_time)

    # Update the embed
    embed = message.embeds[0]
    embed.set_field_at(0, name="Time", value=gta_time.str_game_time)
    embed.set_field_at(2, name="Weather", value=f"{weather_state.weather.name} {weather_state.weather.emoji}")
    embed.set_field_at(3, name="Rain ETA", value=weather_state.rain_eta.str_eta)

    # Edit the message with the updated embed
    await message.edit(embed=embed)

async def show_forecast(msg, forecast: list[list[datetime, WeatherState]], date):
    """
    Show the weather forecast for a specific time period.
    """
    forecast_str = ""
    for d, weather_state in forecast:
        d = pytz_timezone("UTC").localize(d).astimezone(date.tzinfo)
        forecast_str += f"{datetime.strftime(d, '%H:%M')} - " \
                        f"{weather_state.weather.emoji} {weather_state.weather.name} " \
                        f"{ZERO_WIDTH if weather_state.gta_time.is_day_time else MOON}\n"

    embed = msg.embeds[0]
    embed.title = f"**Forecast: \n" \
                  f"{smart_day_time_format('{S} %b %Y @ %H:%M %Z', date)}**"
    embed.description = f"```{forecast_str}```"

    await msg.edit(embed=embed)


@bot.command(name='rain', help='Get the upcoming rain periods.')
async def rain(ctx):
    """
    Fetches the next 4 upcoming periods of rain and sends them in an embed.
    """
    current_time = datetime.now(dt_timezone.utc)
    weather_state = get_weather_state(current_time)
    next_four_rain_periods = get_next_rain_periods(weather_state.gta_time.weather_period_time, 4)

    if not next_four_rain_periods:
        fallback_embed = discord.Embed(
            title="🌦️ Rain Forecast",
            description="No rain periods found in the upcoming future.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=fallback_embed)
        return

    rain_forecast_embed = discord.Embed(
        title=f"🌧️ Next Rain Periods {datetime.now(dt_timezone.utc).strftime('%d-%m-%Y %H:%M %Z')}",
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
        hours, remainder = divmod(time_until_rain.total_seconds(), 3600)
        minutes = remainder // 60

        # Display time in hours and minutes, like "3h 18m"
        time_in_display = f"{int(hours)}h {int(minutes)}m" if hours > 0 else f"{int(minutes)}m"

        rain_forecast_embed.add_field(
            name=f"Rain Period {i + 1}",
            value=f"**Type:** {rain_info.get('type', 'Unknown')}\n"
                  f"**ETA:** {time_in_display}\n"
                  f"**Duration:** {rain_info.get('duration', 'Unknown')}\n"
                  f"**Time:** {rain_start_time.strftime('%H:%M')} - "
                  f"{rain_end_time.strftime('%H:%M')}\n",
            inline=False
        )

    await ctx.send(embed=rain_forecast_embed)

# Start the bot with the token from your .env file
bot.run(os.getenv('DISCORD_TOKEN', 'your-token-placeholder'))
