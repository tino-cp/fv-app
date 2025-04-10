from datetime import datetime, timedelta, timezone as dt_timezone

import discord
from discord.ext import commands
from utils.race_utils import fetch_closest_upcoming_round, process_race_series

@commands.command()
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

    # Define base start dates for regular races
    base_race_start_dates = {
        "f1": datetime(2025, 1, 5, 18, 0, tzinfo=dt_timezone.utc),
        "f2": datetime(2025, 1, 4, 17, 0, tzinfo=dt_timezone.utc)
    }

    # Define sprint races that start 30 minutes earlier
    sprint_races = {"r3", "r7", "r11"}

    if series in base_race_start_dates:
        # Fetch the base race start time
        race_start = base_race_start_dates[series]

        # Determine the race round if not specified
        if not race_round:
            round_number = await fetch_closest_upcoming_round(race_start, current_time)
            race_round = f"r{round_number}"

        # Adjust start time for sprint races
        if race_round in sprint_races:
            race_start -= timedelta(minutes=30)

        # Process the race
        await process_race_series(ctx, race_round, race_start, current_time, series)
    else:
        # Handle invalid series input
        embed = discord.Embed(
            title="Invalid Series",
            description="Please specify either 'f1' or 'f2'.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)