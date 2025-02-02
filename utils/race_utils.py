import discord

from datetime import datetime, timedelta, timezone as dt_timezone

from globals import DEFAULT_TIMEZONE_STR, RAIN_ETA_LABEL, RAIN_LENGTH_LABEL, ORANGE
from models.weather import WEATHER_STATES
from utils.weather_utils import get_weather_state, to_discord_timestamp, convert_to_timezone, get_next_rain_periods, \
    get_rain_eta, get_gta_time

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
            next_rain_period = get_next_rain_periods(race_start_time, race_weather_state.gta_time.weather_period_time, 1)
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
