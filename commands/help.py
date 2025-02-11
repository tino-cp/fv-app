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
        color=discord.Color.gold()  # Use a general color for the embed
    )

    # General Commands
    embed.add_field(
        name="General Commands",
        value=(
            "`!regs` - Prints out link to regulations\n"
            "`!df` - Prints out downforce setting for each formula car\n"
            "---\n"
            "`!standings` `<F1>` `<F2>`\n"
            "Prints out standings from the spreadsheet\n"
            "---\n"            
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
            "- Shows 5 periods of upcoming rain forecasts at your location.\n\n"
            "---\n"
        ),
        inline=False
    )

        # Protests Commands
    embed.add_field(
        name="Protests",
        value=(
            "`!protest <team>`\n"
            "Creates a protest for your team, Only Academy CEO can submit a protest\n"
            "\n\n"
            "`!protests`\n"
            "See how many protests each team had\n"
            "\n\n"
            "`!revertProtest <team>`\n"
            "If protest was sucesfull their protest point will be reverted, Only Head stewards or Admins can revert\n"
            "\n\n"
        ),
        inline=False
    )

    # FIA Penalty Commands
    embed.add_field(
        name="FIA Penalty Commands",
        value=(
            "`!rpo <sprint>`\n"
            "- Start a 60 minute timer for the penalty submission window. After calling this command every thread will be automatically renamed. If there is a sprint then use !rpo sprint for a longer 90 minute timer.\n\n"
            "`!cancel`\n"
            "- Cancel the current penalty submission window.\n\n"
            "`!pen sug`\n"
            "- Renames thread to 'Waiting for suggestion' and pings the stewards and trainee stewards.\n\n"
            "`!pen pov <name>`\n"
            "- Renames thread to 'Waiting for POV <name>'\n\n"
            "`!pen <action> [name] [reason]`\n"
            "- Apply a penalty to the current thread. Reason is optional\n\n"
            "**Actions**:\n"
            "- `LW`: License Warning\n"
            "- `REP`: Reprimand\n"
            "- `SSIR`: Self Serve In Race\n"
            "- `xS`: x-Second Time Penalty\n"
            "- `TLW`: Track Limit Warning\n"
            "- `xGD`: x-Grid Drop Penalty\n\n"
            "`!pen <action> [reason]`\n"
            "- `NFA`: No Further Action\n"
            "- `NFI`: No Further Investigation\n"
            "- `LI`: Lag Incident\n"
            "- `RI`: Racing Incident\n"
            "**Examples**:\n"
            "- `!pen NFA`\n"
            "- `!pen 5S Lyte`\n"
            "- `!pen REP MrTino Brake Light`\n"
            "- `!pen 10GD Skittles Penalty last race (DNF) `\n"
        ),
        inline=False
    )

    embed.add_field(
            name="Race attendance commands",
            value=(
            "`!RAF1 or !RAF2`\n"
            "Creates an attendance form for the specified League\n"
            "`!reset F1 or !reset F2`\n"
            "Resets attendance\n"
            ),
            inline=False
        )


    await ctx.send(embed=embed)
