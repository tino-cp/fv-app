import discord
from discord.ext import commands
from math import ceil
import math

class LapCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_time(self, seconds: float) -> str:
        """Convert seconds to MM:SS.sss format"""
        minutes = int(seconds // 60)
        seconds_remainder = seconds % 60
        return f"{minutes}:{seconds_remainder:04.1f}"

    @commands.command(name='lapcount', aliases=['lapCount', 'lc'])
    async def lap_count(self, ctx, time: float):
        # Truncate time to one decimal place
        time_truncated = int(time * 10) / 10  # Step 1: Truncate here

        def calculate_lap_count(t):
            return math.ceil(2400 / t) + 2

        user_laps = calculate_lap_count(time_truncated)  # Use truncated time

        # Generate all intervals
        intervals = []
        
        # Find user's interval range using truncated time
        lower = upper = time_truncated
        while calculate_lap_count(lower - 0.1) == user_laps:
            lower -= 0.1
        while calculate_lap_count(upper + 0.1) == user_laps:
            upper += 0.1
        user_interval = (lower, upper, user_laps)
        
        # Find adjacent intervals
        def get_interval(start_time, step):
            laps = calculate_lap_count(start_time)
            bound = start_time
            while calculate_lap_count(bound + step) == laps:
                bound += step
            return (min(start_time, bound), max(start_time, bound), laps)
        
        faster_interval = get_interval(lower - 0.1, -0.1)
        slower_interval = get_interval(upper + 0.1, +0.1)

        # Combine and sort intervals
        all_intervals = sorted([faster_interval, user_interval, slower_interval])

        # Build embed with truncated time
        embed = discord.Embed(
            title="🏁 Lap Count Estimator",
            color=discord.Color.green()
        )
        
        # User's truncated time
        embed.add_field(
            name="⏱️ Your Time",
            value=f"`{self.format_time(time_truncated)}` → **{user_laps} Laps**",  # Display truncated
            inline=False
        )
        
        # Interval table
        interval_lines = []
        for lower, upper, laps in all_intervals:
            interval_lines.append(
                f"`{self.format_time(lower)} - {self.format_time(upper)}` → {laps} Laps"
            )
        
        embed.add_field(
            name="📊 Lap Count Intervals",
            value="\n".join(interval_lines),
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LapCount(bot))