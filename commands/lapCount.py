import discord
from discord.ext import commands
from math import ceil
import math

class LapCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_lap_count(self, lap_time: float) -> int:
        return ceil(2400 / lap_time) + 2

    @commands.command(name='lapcount', aliases=['lapCount', 'lc'])
    async def lap_count(self, ctx, time: float):
        user_lap_count = self.calculate_lap_count(time)

        intervals = {}
        current_lap = None
        current_start = None

        # Sweep through a range to find intervals
        for t in [round(time + i * 0.1, 1) for i in range(-100, 101)]:
            laps = self.calculate_lap_count(t)

            if current_lap is None:
                current_lap = laps
                current_start = t
            elif laps != current_lap:
                intervals.setdefault(current_lap, []).append((round(current_start, 1), round(t - 0.1, 1)))
                current_lap = laps
                current_start = t

        # Handle final interval
        intervals.setdefault(current_lap, []).append((round(current_start, 1), round(t, 1)))

        # Create the embed
        embed = discord.Embed(title="🏁 Lap Count Estimator", color=discord.Color.blue())
        embed.add_field(name="Your Time", value=f"**{time:.1f} - {user_lap_count} Laps**", inline=False)
        embed.add_field(name="Lap Count Intervals", value="────────────────────", inline=False)

        # Add 1 lap more
        if user_lap_count + 1 in intervals:
            for start, end in intervals[user_lap_count + 1]:
                embed.add_field(name=f"{start:.1f} - {end:.1f}", value=f"{user_lap_count + 1} Laps", inline=False)

        # Add same lap count
        if user_lap_count in intervals:
            for start, end in intervals[user_lap_count]:
                embed.add_field(name=f"{start:.1f} - {end:.1f}", value=f"{user_lap_count} Laps", inline=False)

        # Add 1 lap less
        if user_lap_count - 1 in intervals:
            for start, end in intervals[user_lap_count - 1]:
                embed.add_field(name=f"{start:.1f} - {end:.1f}", value=f"{user_lap_count - 1} Laps", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LapCount(bot))
