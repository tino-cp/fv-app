from datetime import datetime, timezone as dt_timezone

import discord
from discord.ext import commands
from utils.race_utils import fetch_closest_upcoming_round, process_race_series  # Adjusted imports

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
        embed = discord.Embed(
            title="Invalid Series",
            description="Please specify either 'f1' or 'f2'.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
