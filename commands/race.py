from datetime import datetime, timedelta, timezone as dt_timezone

import discord
from discord.ext import commands
from utils.race_utils import fetch_closest_upcoming_round, process_race_series

# Constants
BASE_RACE_START_DATES = {
    "f1": datetime(2025, 5, 4, 18, 0, tzinfo=dt_timezone.utc),
    "f2": datetime(2025, 5, 3, 17, 0, tzinfo=dt_timezone.utc),
    "f3": datetime(2025, 5, 2, 17, 0, tzinfo=dt_timezone.utc)
}
SPRINT_RACES = {"r3", "r6", "r11"}
MID_SEASON_BREAK = datetime(2025, 6, 20, 18, 0, tzinfo=dt_timezone.utc)
MID_SEASON_ROUND_BREAK = 8
TOTAL_ROUNDS = 13

async def send_embed(ctx, title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    await ctx.send(embed=embed)

@commands.command()
async def race(ctx, series: str = None, race_round: str = None):
    """
    Fetches the race weather for F1, F2, or F3 schedules.
    Example usage:
      !race f1 r1
      !race f2 r2
      !race f3 r11
    """
    series = (series or "f1").lower()
    race_round = race_round.lower() if race_round else None
    current_time = datetime.now(dt_timezone.utc)

    if series not in BASE_RACE_START_DATES:
        await send_embed(ctx, "Invalid Series", "Please specify either 'f1', 'f2' or 'f3'.", discord.Color.red())
        return

    race_start = BASE_RACE_START_DATES[series]

    # Determine the race round if not specified
    if not race_round:
        round_number = await fetch_closest_upcoming_round(race_start, current_time)
        race_round = f"r{round_number}"

    race_round_number = int(race_round[1:])

    if race_round_number == 0:
        await send_embed(ctx, "Invalid round number", "Please specify a round number between 1 and 13", discord.Color.red())
        return

    if race_round_number > TOTAL_ROUNDS:
        await send_embed(ctx, "Off-Season Break", "Season 14 is concluded.", discord.Color.red())
        return

    # Adjust for mid-season break
    if race_round_number >= MID_SEASON_ROUND_BREAK:
        race_start += timedelta(weeks=1)

    # Check if the race falls during a mid-season break
    if MID_SEASON_BREAK <= race_start < MID_SEASON_BREAK + timedelta(weeks=1):
        await send_embed(ctx, "Mid-Season Break", "There is a mid-season break during this week. No races scheduled.", discord.Color.red())
        return

    # Adjust start time for sprint races
    if race_round in SPRINT_RACES:
        race_start -= timedelta(minutes=30)

    # Process the race
    await process_race_series(ctx, race_round, race_start, current_time, series)
