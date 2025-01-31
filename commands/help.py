import discord
from discord.ext import commands

@commands.command(name="help")
async def show_help(ctx):
    """
    Unified help command displaying all bot commands in a single embed.
    """
    embed = discord.Embed(
        title="Bot Command Help",
        description="Here are all the available commands for this bot:",
        color=discord.Color.blue()  # Use a general color for the embed
    )

    # General Commands
    embed.add_field(
        name="General Commands",
        value=(
            "`!race <league> <round>`\n"
            "- Retrieve weather conditions at the start of a race.\n"
            "- **Leagues**: `f1`, `f2`\n"
            "- **Rounds**: `r1`, `r2`, `r3`, etc.\n\n"
            "**Examples**:\n"
            "- `!race f1 r1`\n"
            "- `!race f2`\n\n"
            "If no round is specified, it defaults to the nearest upcoming round.\n"
            "---\n"
            "`!weather`\n"
            "- Get the current weather conditions for the location.\n"
            "---\n"
            "`!rain`\n"
            "- Shows 5 periods of upcoming rain forecasts at your location.\n"
            "`!RAF1 or !RAF2`\n"
            "Creates an attendance form for the specified League"
        ),
        inline=False
    )

    # FIA Penalty Commands
    embed.add_field(
        name="FIA Penalty Commands",
        value=(
            "`!rpo | !rpo sprint`\n"
            "- Start a 60 or 90 minute timer for the penalty submission window. After calling this command every thread will be automatically renamed. \n\n"
            "`!cancel`\n"
            "- Cancel the current penalty submission window.\n\n"
            "`!pen sug`\n"
            "- Renames thread to 'Waiting for suggestion' and pings the stewards and trainee stewards\n\n"
            "`!pen pov <name>`\n"
            "- Renames thread to 'Waiting for POV <name>'\n\n"
            "`!pen <action> [name] [reason]`\n"
            "- Apply a penalty to the current thread. This is sensitive to capitalization.\n\n"
            "**Actions**:\n"
            "- `LW`: License Warning\n"
            "- `REP`: Reprimand\n"
            "- `SSIR`: Stop and Start Investigation Required\n"
            "- `xS`: 5-Second Time Penalty\n"
            "- `xGD`: 3-Grid Drop Penalty\n\n"
            "`!pen <action> [reason]`\n"
            "- `NFA`: No Further Action\n"
            "- `NFI`: No Further Investigation\n"
            "- `LI`: Light Investigation\n"
            "- `RI`: Regular Investigation\n"
            "- `TLW`: Time Loss Warning\n"
            "**Examples**:\n"
            "- `!pen NFA`\n"
            "- `!pen 5S Lyte Spinning Anthonyy`\n"
            "- `!pen REP MrTino Brake Light`\n"
            "- `!pen 10GD Skittles Penalty last race (DNF) `\n"
            "---\n"
        ),
        inline=False
    )

    await ctx.send(embed=embed)
