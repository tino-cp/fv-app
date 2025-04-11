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
        name="**---------**__**GENERAL COMMANDS**__**---------**",
        value=(
            "`!regs` - Prints out link to regulations\n"
            "`!df` - Prints out downforce setting for each formula car\n\n"
            "`!standings <F1><c> <F2><c>`\n"
            "Prints out standings from the spreadsheet\n"
            "f.e. `!standings F1` for drivers standings\n"
            "f.e. `!standings F2C` for teams standings\n\n"
            "`!weather`\n"
            "- Get the current weather conditions for the location.\n\n"
            "`!rain`\n"
            "- Shows 5 periods of upcoming rain forecasts at your location.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # Weather Command
    embed.add_field(
        name="**---------**__**WEATHER COMMAND**__**---------**",
        value=(
            "`!race <league> <round>`\n"
            "- Retrieve weather conditions at the start of a race.\n"
            "- **Leagues**: `f1`, `f2`\n"
            "- **Rounds**: `r1`, `r2`, `r3`, etc.\n\n"
            "**Examples**:\n"
            "- `!race f1 r1`\n"
            "- `!race f2`\n\n"
            "If no round is specified, it defaults to the nearest upcoming round.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # Results Command
    embed.add_field(
        name="**---------**__**RESULTS**__**---------**",
        value=(
            "`!results <race>`\n"
            "- Retrieve the results of a specific race from the spreadsheet.\n"
            "- **Race**: The name of the race or event (e.g., `F1_R1`, `F2_R2`, etc.).\n\n"
            "**Example**:\n"
            "- `!results F1_R1`\n"
            "- `!results F2_R3`\n\n"
            "The results include the positions, drivers, teams, points, race times, fastest laps, and any penalties.\n"
            "The driver with the fastest lap will be marked with a star ⭐ next to their time.\n"
            "If the race does not exist or there is an issue retrieving the data, an error message will be displayed.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # Trainee Steward Commands
    embed.add_field(
        name="**---------**__**TRAINEE STEWARD COMMANDS**__**---------**",
        value=(
            "`!suggestion <reason>`\n"
            "- Log a suggestion for a penalty in the current penalty thread.\n"
            "- Example: `!suggestion I think this driver deserves a 10s penalty for cutting the corner.`\n\n"
            "`!approve`\n"
            "- Used by stewards to approve a suggestion made by a trainee.\n"
            "- Reply to a suggestion and use this command to approve it.\n"
            "- Logs the suggestion as approved with the steward’s name.\n\n"
            "`!list_suggestions`\n"
            "- Retrieves a list of all logged trainee suggestions in CSV format.\n"
            "- Only available to stewards or admins.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # Protests Commands
    embed.add_field(
        name="**---------**__**PROTESTS**__**---------**",
        value=(
            "`!protest <team>`\n"
            "Creates a protest for your team. Only Academy CEO can submit a protest.\n\n"
            "`!protests`\n"
            "See how many protests each team has.\n\n"
            "`!revertProtest <team>`\n"
            "If the protest was successful, their protest point will be reverted. Only Head Stewards or Admins can revert.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # FIA Penalty Commands
    embed.add_field(
        name="**---------**__**FIA PENALTY COMMANDS**__**---------**",
        value=(
            "`!rpo <sprint>`\n"
            "- Start a 60-minute timer for the penalty submission window. Use `!rpo sprint` for a 90-minute timer.\n\n"
            "`!cancel`\n"
            "- Cancel the current penalty submission window.\n\n"
            "`!pen sug`\n"
            "- Renames thread to 'Waiting for suggestion' and pings the stewards and trainee stewards.\n\n"
            "`!pen pov <name>`\n"
            "- Renames thread to 'Waiting for POV <name>'\n\n"
            "`!pen <action> [name] [reason]`\n"
            "- Apply a penalty to the current thread. Reason is optional.\n\n"
            "**Actions**:\n"
            "- `LW`: License Warning\n"
            "- `REP`: Reprimand\n"
            "- `SSIR`: Self Serve In Race\n"
            "- `xS`: x-Second Time Penalty\n"
            "- `TLW`: Track Limit Warning\n"
            "- `xGD`: x-Grid Drop Penalty\n\n"
            "`!pen <action> [reason]`\n"
            "- `NFA`: No Further Action\n"
            "- `NFI`: No Further Investigation - this will not get logged\n"
            "- `NFH`: Nothing fucking happened - this will not get logged\n"
            "- `LI`: Lag Incident\n"
            "- `RI`: Racing Incident\n\n"
            "**Examples**:\n"
            "- `!pen NFA`\n"
            "- `!pen 5S Lyte`\n"
            "- `!pen REP MrTino Brake Light`\n"
            "- `!pen 10GD Skittles Penalty last race (DNF)`\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    # Logs Commands
    embed.add_field(
        name="**---------**__**LOGS COMMANDS**__**---------**",
        value=(
            "`!pen getLogs`\n"
            "- Retrieve and send the penalty log file.\n\n"
            "`!pen clearLogs`\n"
            "- Clear all entries in the penalty log.\n\n"
            "`!pen filterLogs`\n"
            "- Filter the logs to keep only the most recent entry for each league and thread.\n\n"
            "`!pen sortLogs`\n"
            "- Sort the logs by league and thread counter in ascending order.\n\n"
        ),
        inline=False
    )

    # Race Attendance Commands
    embed.add_field(
        name="**---------**__**RACE ATTENDANCE COMMANDS**__**---------**",
        value=(
            "`!RA <Track name>`\n"
            "Creates an attendance form for the entire weekend.\n\n"
            "`!RAF1 or !RAF2`\n"
            "Creates an attendance form for the specified League.\n\n"
            "`!reset F1 or !reset F2`\n"
            "Resets attendance for the specified League.\n\n\n\n"  # Two empty lines
        ),
        inline=False
    )

    await ctx.send(embed=embed)
