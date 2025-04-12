import discord
from discord.ext import commands
from math import ceil
import math

class LapCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lapcount', aliases=['lapCount', 'lc'])
    async def lap_count(self, ctx, time: float):
        # Calculate lap count
        def calculate_lap_count(time):
            return math.ceil(2400 / time) + 2

        # Prepare a list for the table
        time_range = []
        for i in range(8):

            upper_time = time + (0.1 * (8 - i))
            time_range.append((upper_time, calculate_lap_count(upper_time)))

        # Add the exact value of the user input as bold
        time_range.append((time, f"**--{calculate_lap_count(time)}--**"))

        for i in range(8):

            lower_time = time - (0.1 * (i + 1))
            time_range.append((lower_time, calculate_lap_count(lower_time)))
            

        # Create the embed
        embed = discord.Embed(title="🏁 Lap Count Estimator", color=discord.Color.blue())

        for t, lap in time_range:
            embed.add_field(name=f"{t:.1f} seconds", value=f"{lap} laps", inline=False)

        # Send the embed
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LapCount(bot))
