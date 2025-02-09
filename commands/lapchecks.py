import random
from discord.ext import commands
import discord

def calculate_lap_check_chance(position):
    """
    Calculate the chance of being lap-checked based on the given position using the adjusted formula.

    Args:
        position (int): The qualifying position (1-20).

    Returns:
        float: The chance of being lap-checked as a decimal (e.g., 0.05 for 5%).
    """
    if position < 1 or position > 20:
        raise ValueError("Position must be between 1 and 20.")

    # Positions higher than 5 have a 0% chance
    if position > 5:
        return 0.0

    # = (0.0000015625*(21-5)^6)/100
    chance = (0.0000015625 * (21 - position) ** 6) / 100

    return chance

class LapChecks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='lapchecks', help='Roll out lap checks for all positions (1-20) using the adjusted formula.')
    async def lapchecks(self, ctx):
        """
        Command to roll out lap checks for all positions using the adjusted formula.
        """
        global roll
        lap_checks = []  # Stores positions that get a lap check
        output_lines = []  # Stores formatted output for each position
        roll_values = {}  # Stores the roll value for each position

        # Iterate through positions 1 to 20
        for position in range(1, 21):
            # Calculate the chance of a lap check using the adjusted formula
            chance = calculate_lap_check_chance(position)

            # Roll a random number between 0 and 1 to determine if it hits
            roll = random.random()
            roll_values[position] = roll

            if roll < chance:
                lap_checks.append(position)
                hit_status = "🟢"  # Green emoji for hit
            else:
                hit_status = "🔴"  # Red emoji for miss

            # Format the output line for this position
            chance_str = f"{chance:.2%}" if chance < 1.0 else "100.0%"
            output_lines.append(
                f"|   P{position}   | {chance_str} | {roll:.2f} |  {hit_status}  |"
            )

            print(f"Position: {position}, Chance: {chance:.2%}, Roll: {roll:.2f}, Status: {hit_status}")


        # If any position hits, ensure all positions above the lowest one also hit
        if lap_checks:
            # Find the lowest position that hit
            lowest_position = max(lap_checks)

            # Add all positions above the lowest position
            for position in range(1, lowest_position):
                if position not in lap_checks:
                    lap_checks.append(position)
                    # Update the output line for this position to show it was added
                    output_lines[position - 1] = (
                        f"|   P{position}   | {calculate_lap_check_chance(position):.2%} | {roll_values[position]:.2f} |  🟡  |"
                    )

        # Create the embed
        embed = discord.Embed(
            title="Lap Check Calculator",
            description="Rolls a random number to determine lap checks for each position. Green and red indicate a hit or miss, respectively. Yellow indicates it was added due to a lower position being hit.",
            color=discord.Color.blue()
        )

        # Add the lap check results as a code block
        embed.add_field(
            name="Results",
            value=f"```\n{'| Position | Chance | Roll | Status |'}\n{'-' * 33}\n" +
                  "\n".join(output_lines[:5]) + "\n```",
            inline=False
        )

        # Add the final lap-checked positions
        if lap_checks:
            embed.add_field(
                name="Final Lap Checks",
                value=f"```{', '.join(f'P{p}' for p in sorted(lap_checks))}```",
                inline=False
            )
        else:
            embed.add_field(
                name="Final Lap Checks",
                value="```No lap checks were issued.```",
                inline=False
            )

        # Send the embed to the channel
        await ctx.send(embed=embed)