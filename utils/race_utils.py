from datetime import datetime, timedelta

import discord
from discord import Embed
from utils.weather_utils import get_weather_state, to_discord_timestamp

async def fetch_closest_upcoming_round(series_start_date: datetime, current_time: datetime) -> int:
    days_since_start = (current_time - series_start_date).days
    round_number = max(1, days_since_start // 7 + 1)

    race_start_time = series_start_date + timedelta(weeks=(round_number - 1))
    if race_start_time < current_time:
        round_number += 1

    return round_number

async def process_race_series(ctx, race_round: str, series_start: datetime, current_time: datetime, series: str):
    round_number = int(race_round[1:])
    race_start_time = series_start + timedelta(weeks=(round_number - 1))
    race_weather_state = get_weather_state(race_start_time)

    embed = Embed(
        title=f"{series.upper()} Race Weather for {to_discord_timestamp(race_start_time, 'F')}",
        color=discord.Color.orange()
    )
    embed.add_field(name="Weather", value=f"{race_weather_state.weather.name} {race_weather_state.weather.emoji}")
    await ctx.send(embed=embed)
