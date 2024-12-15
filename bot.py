import discord
from discord.ext import commands
from datetime import datetime
import logging
import pytz
import os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('discord')

ALIASES = ['weather', 'forecast']

EMBED_TYPES = [
    'current_weather_state',
    'future_weather_time_zone',
    'future_weather_date',
]

GAME_HOUR_LENGTH = 120
SUNRISE_TIME = 5
SUNSET_TIME = 21

WEEKDAYS = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

epoch: datetime = datetime(1970, 1, 1)  # used to get total_seconds

TIME_ZONES = {
    "North America": {
        "Los Angeles": "US/Pacific",
        "Denver": "US/Mountain",
        "Chicago": "US/Central",
        "New York": "US/Eastern",
    },
    "South America": {
        "Buenos Aires": "America/Argentina/Buenos_Aires",
    },
    "Europe": {
        "UTC": "UTC",
        "London": "Europe/London",
        "Amsterdam": "Europe/Amsterdam",
    },
    "Asia": {
        "Vientiane": "Asia/Vientiane",
        "Japan": "Japan",
    },
    "Australia": {
        "Queensland": "Australia/Queensland",
        "Sydney": "Australia/Sydney",
    },
}

def hours_to_HHMM(hours: float) -> str:
    """
    Convert a floating-point hour value to HH:MM format.
    Example: 14.5 will be converted to '14:30'.
    """
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02}:{m:02}"

class Weather:
    def __init__(self, name: str, emoji: str, day_thumbnail: str, night_thumbnail: str):
        self.name = name
        self.emoji = emoji
        self.day_thumbnail = day_thumbnail
        self.night_thumbnail = night_thumbnail


class GTATime:
    def __init__(self, hours_game_time: float, weekday, weather_period_time: float):
        self.hours_game_time = hours_game_time
        self.str_game_time = hours_to_HHMM(self.hours_game_time)
        self.weekday = weekday
        self.weather_period_time = weather_period_time
        self.is_day_time = SUNRISE_TIME <= self.hours_game_time < SUNSET_TIME


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

        else:
            return minutes_str


class WeatherState:
    def __init__(self, weather: Weather, gta_time: GTATime, rain_eta: RainETA):
        self.weather = weather
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
    [246, WEATHER_STATES['mostly_clear']],
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

# Function to get GTA time
def get_gta_time(date: datetime) -> GTATime:
    timestamp: int = int((date - epoch).total_seconds())
    total_gta_hours: float = timestamp / GAME_HOUR_LENGTH
    weekday = WEEKDAYS[int(total_gta_hours % 168 / 24) - 1]
    current_gta_hour: float = total_gta_hours % 24
    return GTATime(current_gta_hour, weekday, total_gta_hours % 384)


# Function to get weather for a given time period
def get_weather_for_period_time(weather_period_time: float) -> Weather:
    for i, period in enumerate(WEATHER_STATE_CHANGES):
        if period[0] > weather_period_time:
            return WEATHER_STATE_CHANGES[i - 1][1]
    return WEATHER_STATE_CHANGES[-1][1]


# Function to check if it's raining
def check_is_raining(weather: Weather):
    return weather is WEATHER_STATES['raining']


# Function to get rain ETA
def get_rain_eta(weather_period_time: float, weather: Weather) -> RainETA:
    is_raining = check_is_raining(weather)
    len_weather_state_changes = len(WEATHER_STATE_CHANGES)

    for i in range(len_weather_state_changes * 2):
        index = i % len_weather_state_changes
        offset = int(i / len_weather_state_changes) * 384

        if WEATHER_STATE_CHANGES[index][0] + offset >= weather_period_time:
            if is_raining ^ check_is_raining(WEATHER_STATE_CHANGES[index][1]):
                rain_eta = WEATHER_STATE_CHANGES[index][0] + offset - weather_period_time
                return RainETA(rain_eta, check_is_raining(WEATHER_STATE_CHANGES[index][1]))
    return RainETA(0, is_raining)

# Create the bot client with commands extension
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def weather(ctx):
    # Example function to get weather information for a given command
    gta_time = get_gta_time(datetime.now())
    weather_period_time = gta_time.weather_period_time
    weather = get_weather_for_period_time(weather_period_time)
    rain_eta = get_rain_eta(weather_period_time, weather)

    # Prepare the detailed weather info
    detailed_info = (
        f"**GTA Time**: {gta_time.str_game_time} ({gta_time.weekday})\n"
        f"**Weather**: {weather.name} {weather.emoji}\n"
        f"**Weather Thumbnail (Day)**: {weather.day_thumbnail}\n"
        f"**Weather Thumbnail (Night)**: {weather.night_thumbnail}\n"
        f"**Is it Day Time?**: {'Yes' if gta_time.is_day_time else 'No'}\n"
        f"**Rain ETA**: {rain_eta.str_eta}\n"
        f"**Is it Raining?**: {'Yes' if rain_eta.is_raining else 'No'}\n"
    )

    # Log detailed information to console for debugging
    logger.debug(detailed_info)

    # Send the detailed info to the Discord channel
    await ctx.send(detailed_info)

@bot.command()
async def forecast(ctx):
    # Example function for future forecast
    await ctx.send("Here is the forecast...")

# Event when bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Start the bot with your token
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
