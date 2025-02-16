import discord
import random
from discord.ext import commands
from tabulate import tabulate

def calculate_lap_check_chance(position):
    # = (0.0000015625*(21-5)^6)/100
    return (0.0000015625 * (21 - position) ** 6) / 100

class LapChecks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lapchecks', help='Roll out lap checks for all positions (1-20) using the adjusted formula.')
    async def lapchecks(self, ctx):
        """
        Command to roll out lap checks for all positions using the adjusted formula.
        """
        lap_checks = []  # Stores positions that get a lap check
        table_data = []  # Stores data for the table
        rolled_values = {}  # Stores the rolled value for each position

        for position in range(1, 6):
            chance = calculate_lap_check_chance(position)
            roll = random.random() # Roll a random number between 0 and 1 to determine if it hits
            rolled_values[position] = roll

            if roll < chance:
                lap_checks.append(position)
                status = "🟢"
            else:
                status = "🔴"

            table_data.append([f"P{position}", f"{chance:.2%}", f"{roll:.2f}", status])

        # Ensure all positions above the lowest hit also hit
        if lap_checks:
            lowest_position = max(lap_checks)
            for position in range(1, lowest_position):
                if position not in lap_checks:
                    lap_checks.append(position)
                    status = "🟡"
                    table_data[position - 1][3] = status

        headers = ["Position", "Chance", "Roll", "Status"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        print (table)

        embed = discord.Embed(
            title="Lap Check Calculator",
            description=
                "Rolls a random number to determine lap checks for each position. "
                "Green and red indicate a hit or miss, respectively. "
                "Yellow indicates it was added due to a lower position being hit.",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Results",
            value=f"```{table}```",
            inline=False
        )

        embed.add_field(
            name="Final Lap Checks",
            value=f"```{', '.join(f'P{p}' for p in sorted(lap_checks))}```",
            inline=False
        )

        await ctx.send(embed=embed)