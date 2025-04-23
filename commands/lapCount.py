import discord
from discord.ext import commands
from math import ceil
import math

class LapCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lapcount', aliases=['lapCount', 'lc'])
    async def lap_count(self, ctx, time: float):
        def calculate_lap_count(t):
            return math.ceil(2400 / t) + 2

        user_laps = calculate_lap_count(time)

        # Generate all possible intervals around the user's time
        intervals = []
        
        # Find the full range for the user's lap count
        lower_bound = upper_bound = time
        while calculate_lap_count(lower_bound - 0.1) == user_laps:
            lower_bound -= 0.1
        while calculate_lap_count(upper_bound + 0.1) == user_laps:
            upper_bound += 0.1
        user_interval = (lower_bound, upper_bound, user_laps)
        
        # Find the next higher lap count (slower times)
        higher_lower = upper_bound + 0.1
        higher_laps = calculate_lap_count(higher_lower)
        higher_upper = higher_lower
        while calculate_lap_count(higher_upper + 0.1) == higher_laps:
            higher_upper += 0.1
        higher_interval = (higher_lower, higher_upper, higher_laps)
        
        # Find the next lower lap count (faster times)
        lower_upper = lower_bound - 0.1
        lower_laps = calculate_lap_count(lower_upper)
        lower_lower = lower_upper
        while calculate_lap_count(lower_lower - 0.1) == lower_laps:
            lower_lower -= 0.1
        lower_interval = (lower_lower, lower_upper, lower_laps)

        # Combine and sort all intervals (fastest to slowest)
        all_intervals = [lower_interval, user_interval, higher_interval]
        all_intervals.sort()  # Sorts by start time (fastest first)

        # Prepare the embed
        embed = discord.Embed(title="🏁 Lap Count Estimator", color=discord.Color.blue())
        
        # Add user's specific time
        embed.add_field(
            name="Your Time", 
            value=f"{time:.1f} - **{user_laps} Laps**", 
            inline=False
        )
        
        # Add interval header
        embed.add_field(
            name="Lap Count Intervals",
            value="────────────────────",
            inline=False
        )
        
        # Add all intervals in order
        for lower, upper, laps in all_intervals:
            embed.add_field(
                name=f"{lower:.1f} - {upper:.1f}",
                value=f"{laps} Laps",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LapCount(bot))