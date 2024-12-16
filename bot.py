import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone as dt_timezone
import logging
from pytz import timezone as pytz_timezone
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

WEATHER_PERIOD = 384
GAME_HOUR_LENGTH = 120
SUNRISE_TIME = 5
SUNSET_TIME = 21

WEEKDAYS = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

epoch: datetime = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)  # used to get total_seconds

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

ORANGE = int(0xF03C00)
ZERO_WIDTH = chr(8203)  # or the thing in between the dashes -​-
SPACE_CHAR = "⠀"
HEAVY_CHECKMARK = "✔"
BALLOT_CHECKMARK = "☑️"
WRENCH = "🔧"
FLAG_ON_POST = "🚩"
COUNTER_CLOCKWISE = "🔄"
CALENDAR = "📆"
RAIN_WITH_SUN = "🌦️"
X = "❌"
MOON = "🌙"
BOOKS = "📚"
THUMBSUP = "👍"
THUMBSDOWN = "👎"
SHRUG = "🤷"
ORANGE_HEART = "🧡"
NUMBERS_EMOJIS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
LETTERS_EMOJIS = {
    "a": "🇦", "b": "🇧", "c": "🇨", "d": "🇩", "e": "🇪", "f": "🇫", "g": "🇬", "h": "🇭", "i": "🇮",
    "j": "🇯", "k": "🇰", "l": "🇱", "m": "🇲", "n": "🇳", "o": "🇴", "p": "🇵", "q": "🇶", "r": "🇷",
    "s": "🇸", "t": "🇹", "u": "🇺", "v": "🇻", "w": "🇼", "x": "🇽", "y": "🇾", "z": "🇿", "?": "❔"
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


async def handle_reaction_add(
        msg: discord.Message,
        emoji: str,
        user: discord.User,
        client: discord.Client,
        embed_meta: str = ""
) -> None:
    embed_type = embed_meta.split('type=')[1].split('/')[0]

    if embed_type == 'current_weather_state':

        if emoji == COUNTER_CLOCKWISE:
            await send_weather(msg)

        elif emoji == CALENDAR:

            try:
                await msg.clear_reactions()
            except discord.Forbidden:
                pass

            await get_user_timezone(msg)

    elif embed_type == "future_weather_time_zone":

        if emoji in embed_meta:

            try:
                await msg.clear_reactions()
            except discord.Forbidden:
                pass

            time_zone_str = embed_meta.split(f"{emoji}=")[1].split("/")[0]
            await get_user_date(msg, time_zone_str)

    elif embed_type == "future_weather_date":

        if emoji == BALLOT_CHECKMARK:
            await send_future_weather(msg, user, embed_meta)


async def handle_reaction_remove(
        msg: discord.Message,
        emoji: str,
        user: discord.User,
        client: discord.Client,
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
    return GTATime(current_gta_hour, weekday, total_gta_hours % WEATHER_PERIOD)


# Function to get weather for a given time period
def get_weather_for_period_time(weather_period_time: float) -> Weather:
    for i, period in enumerate(WEATHER_STATE_CHANGES):
        if period[0] > weather_period_time:
            return WEATHER_STATE_CHANGES[i - 1][1]
    return WEATHER_STATE_CHANGES[-1][1]


# Function to check if it's raining
def check_is_raining(weather: Weather):
    return weather == WEATHER_STATES['raining'] or weather == WEATHER_STATES['drizzling']


# Function to get rain ETA
def get_rain_eta(weather_period_time: float, weather: Weather) -> RainETA:
    is_raining = check_is_raining(weather)

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


def get_gta_time_from_input(input_datetime: datetime) -> GTATime:
    timestamp: int = int((input_datetime - epoch).total_seconds())
    total_gta_hours: float = timestamp / GAME_HOUR_LENGTH
    weekday = WEEKDAYS[int(total_gta_hours % 168 / 24) - 1]
    current_gta_hour: float = total_gta_hours % 24
    return GTATime(current_gta_hour, weekday, total_gta_hours % WEATHER_PERIOD)


def get_forecast(date: datetime, hours=4) -> list[list[datetime, WeatherState]]:
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
    weather: Weather = get_weather_for_period_time(gta_time.weather_period_time)
    rain_eta = get_rain_eta(gta_time.weather_period_time, weather)

    return WeatherState(
        weather, gta_time, rain_eta
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

async def get_user_timezone(msg: discord.Message):
    embed = discord.Embed(
        color=discord.Color(ORANGE),
        title="**Future Weather**",
        description="Which time zone?"
    )

    reactions = []
    letters = list(LETTERS_EMOJIS.keys())
    embed_meta = "embed_meta/type=future_weather_time_zone/"

    for continent in TIME_ZONES:

        value_str = ""
        for location in TIME_ZONES[continent]:
            time_zone = TIME_ZONES[continent][location].replace("/", "\\")

            letter_emoji = LETTERS_EMOJIS[letters[len(reactions)]]
            embed_meta += f"{letter_emoji}={time_zone}/"
            reactions.append(letter_emoji)

            value_str += f"{letter_emoji} {location}\n"

        embed.add_field(
            name=f"**__{continent}__**",
            value=f"{value_str}{SPACE_CHAR}"
        )

    embed.description += f"||[{ZERO_WIDTH}]({embed_meta})||"
    await msg.edit(embed=embed)
    [await msg.add_reaction(r) for r in reactions]


async def get_user_date(msg: discord.Message, time_zone_str: str):
    embed = discord.Embed(
        color=discord.Color(ORANGE),
        title="**Future Weather**",
        description=f"What's the date?\n"
                    f"Type `Now` for the current 4-hour forecast."

                    "\n\n**Format:** `MM/DD/YYYY HH:MM`"
                    "\n19th August 2021 9:12pm -> `8/19/2021 21:12`"
                    f"\n\nType it below, then click the {BALLOT_CHECKMARK}"
    )

    embed.description += f"||[{ZERO_WIDTH}](embed_meta/type=future_weather_date/time_zone={time_zone_str}/)||"

    await msg.edit(embed=embed)
    await msg.add_reaction(BALLOT_CHECKMARK)


async def send_future_weather(msg: discord.Message, user: discord.User, embed_meta: str):
    time_zone = pytz_timezone(embed_meta.split("time_zone=")[1].split("/")[0].replace('\\', '/'))

    history = []
    async for m in msg.channel.history(after=msg.created_at, oldest_first=False):
        history.append(m)

    date = None
    for m in history:

        if m.author.id == user.id:
            message = m

            try:
                if message.content.lower() == "now":
                    date = pytz_timezone("UTC").localize(datetime.now())

                else:
                    date = datetime.strptime(message.content, "%m/%d/%Y %H:%M")  # get the date
                    date = time_zone.localize(date)  # set TZ as user TZ
                    date = date.astimezone(pytz_timezone("UTC"))  # then convert to UTC

            except ValueError:
                await message.reply(
                    f"`{message.content}` does not match the format `MM/DD/YYYY` (8/18/2021). "
                    f"Edit your message, then re-click the button."
                )
                return
            date = date.replace(tzinfo=None)  # remove tzinfo
            break

    if date:
        forecast = get_forecast(date)

    else:  # no date, means no message
        return

    try:
        await msg.clear_reactions()
    except discord.Forbidden:
        pass

    await send_forecast(msg, forecast, pytz_timezone('UTC').localize(date).astimezone(time_zone))


async def send_forecast(msg: discord.Message, forecast: list[list[datetime, WeatherState]], date):
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

    logger.info(f"Sent Forecast: {date}")


async def send_weather(message: discord.Message) -> discord.Message:
    utc_now = datetime.now(dt_timezone.utc)

    weather_state = get_weather_state(utc_now)
    future_weather_state = get_weather_state(utc_now + timedelta(seconds=weather_state.rain_eta.sec_eta, minutes=1))

    rain_str = f"Rain will {'end' if weather_state.rain_eta.is_raining else 'begin'} " \
               f"in {weather_state.rain_eta.str_eta}." \
               f"\nRoads will be {'dry' if weather_state.rain_eta.is_raining else 'wet'} " \
               f"for {future_weather_state.rain_eta.str_eta}."

    metadata = "embed_meta/type=current_weather_state/"

    embed = discord.Embed(
        colour=discord.Colour(ORANGE),
        title=f'**It is {weather_state.weather.name.lower()} at '
              f'{weather_state.gta_time.str_game_time} on {weather_state.gta_time.weekday}!**',
        description=f"{rain_str}\n\n||[{ZERO_WIDTH}]({metadata})||"
    )

    embed.set_thumbnail(
        url=weather_state.weather.day_thumbnail if weather_state.gta_time.is_day_time else weather_state.weather.night_thumbnail
    )

    embed.set_footer(text=f"Updated: {smart_day_time_format('%H:%M UTC %A, {S} %B %Y', utc_now)}")

    msg = await message.channel.send(embed=embed)
    await msg.add_reaction(COUNTER_CLOCKWISE)
    await msg.add_reaction(CALENDAR)

    return msg

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def weather(ctx):
    """
    Fetches the current weather state and sends it to the Discord channel.
    """
    current_time = datetime.now(dt_timezone.utc)
    gta_time = get_gta_time(current_time)
    weather_state = get_weather_state(current_time)
    future_weather_state = get_weather_state(current_time + timedelta(seconds=weather_state.rain_eta.sec_eta, minutes=1))

    embed = discord.Embed(
        title="Current Weather State",
        color=discord.Color(ORANGE)
    )
    embed.add_field(name="Time", value=gta_time.str_game_time)
    embed.add_field(name="Day", value=gta_time.weekday)
    embed.add_field(name="Weather", value=f"{weather_state.weather.name} {weather_state.weather.emoji}")
    embed.add_field(name="Rain ETA", value=weather_state.rain_eta.str_eta)
    embed.add_field(name="Rain Length", value=f"\nIt's going to be {'dry' if weather_state.rain_eta.is_raining else 'wet'} " \
               f"for {future_weather_state.rain_eta.str_eta}.")
    embed.set_thumbnail(
        url=weather_state.weather.day_thumbnail if gta_time.is_day_time else weather_state.weather.night_thumbnail)

    embed.set_footer(text="React with 🔄 to refresh or 📆 to check the forecast.")

    embed_meta = "embed_meta/type=current_weather_state/"
    if embed.description is None:
        embed.description = ""
    embed.description += f"||[{ZERO_WIDTH}]({embed_meta})||"

    message = await ctx.send(embed=embed)
    await message.add_reaction(COUNTER_CLOCKWISE)
    await message.add_reaction(CALENDAR)


@bot.command()
async def forecast(ctx, hours: int = 4):
    """
    Fetches the weather forecast for the next specified number of hours (default: 4 hours).
    """
    current_time = datetime.now(dt_timezone.utc)
    forecast_data = get_forecast(current_time, hours)

    embed = discord.Embed(
        title=f"Weather Forecast for the next {hours} hours",
        color=discord.Color(ORANGE)
    )
    for dt, weather_state in forecast_data:
        gta_time = get_gta_time(dt)
        embed.add_field(
            name=f"{dt.strftime('%Y-%m-%d %H:%M')} ({gta_time.str_game_time})",
            value=f"{weather_state.weather.name} {weather_state.weather.emoji} - Rain ETA: {weather_state.rain_eta.str_eta}",
            inline=False
        )
    await ctx.send(embed=embed)


@bot.command()
async def getTimezone(ctx):
    """
    Allows the user to select a timezone for future weather forecasts.
    """
    await get_user_timezone(await ctx.send("Please select a timezone."))


@bot.command()
async def future_weather(ctx, *, input_date: str = "now"):
    """
    Fetches the weather forecast for a specific future date and time provided by the user.
    Example: !future_weather 8/19/2021 21:12
    """
    try:
        time_zone = pytz_timezone("UTC")  # Default to UTC
        if input_date.lower() == "now":
            date = datetime.now(dt_timezone.utc)
        else:
            date = datetime.strptime(input_date, "%m/%d/%Y %H:%M")
            date = time_zone.localize(date)  # Set timezone
            date = date.astimezone(pytz_timezone("UTC"))

        forecast_data = get_weather_state(date)

        gta_time = get_gta_time(date)
        embed = discord.Embed(
            title=f"Weather Forecast for {date.strftime('%Y-%m-%d %H:%M')}",
            color=discord.Color(ORANGE)
        )
        embed.add_field(name="Time", value=gta_time.str_game_time)
        embed.add_field(name="Day", value=gta_time.weekday)
        embed.add_field(name="Weather", value=f"{forecast_data.weather.name} {forecast_data.weather.emoji}")
        embed.add_field(name="Rain ETA", value=forecast_data.rain_eta.str_eta)
        embed.set_thumbnail(
            url=forecast_data.weather.day_thumbnail if gta_time.is_day_time else forecast_data.weather.night_thumbnail)

        await ctx.send(embed=embed)

    except ValueError:
        await ctx.send(f"`{input_date}` is not a valid date. Use the format MM/DD/YYYY HH:MM.")


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg = reaction.message
    emoji = str(reaction.emoji)

    if not msg.embeds:
        return

    embed_meta = msg.embeds[0].description if msg.embeds else None
    if not embed_meta:
        return

    await handle_reaction_add(msg, emoji, user, bot, embed_meta=embed_meta)


@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return

    msg = reaction.message
    emoji = str(reaction.emoji)

    if not msg.embeds:
        return

    embed_meta = msg.embeds[0].description if msg.embeds else None
    if not embed_meta:
        return

    await handle_reaction_remove(msg, emoji, user, bot, embed_meta=embed_meta)


# Start the bot with the token from your .env file
bot.run(os.getenv('DISCORD_TOKEN'))
