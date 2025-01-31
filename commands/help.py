import discord
from discord.ext import commands

@commands.command(name="help")
async def show_help(ctx):
    """
    Custom help command displaying bot commands in an embed.
    """
    embed = discord.Embed(
        title="Race Weather Commands",
        description="Here are the available commands for this bot:",
        color=discord.Color.blue()  # Use a suitable color for the embed
    )

    # Add command descriptions
    embed.add_field(
        name="`!race <league> <round>`",
        value=(
            "Retrieve weather conditions at the start of a race.\n"
            "**Leagues**: `f1`, `f2`\n"
            "**Rounds**: `r1`, `r2`, `r3`, etc.\n\n"
            "If no round is specified (e.g., `!race f1` or `!race f2`), "
            "it defaults to the nearest upcoming round.\n\n"
            "Example: `!race f1 r1`"
        ),
        inline=False
    )

    embed.add_field(
        name="`!weather`",
        value="Get the current weather conditions for the location.",
        inline=False
    )

    embed.add_field(
        name="`!rain`",
        value="Shows 5 periods of upcoming rain forecasts at your location.",
        inline=False
    )

    await ctx.send(embed=embed)