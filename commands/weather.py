from datetime import datetime, timezone as dt_timezone
from discord.ext import commands
from globals import RAIN_ETA_LABEL, RAIN_LENGTH_LABEL, bot_state, COUNTER_CLOCKWISE
from utils.weather_utils import (
    get_gta_time,
    get_weather_state,
    to_discord_timestamp,
    get_rain_eta,
    get_next_rain_periods,
)
import discord

@commands.command()
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


@commands.command(name='rain', help='Get the upcoming rain periods.')
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
