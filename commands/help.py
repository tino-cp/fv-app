import discord
from discord.ext import commands

@commands.command(name="help", aliases=['h'])
async def show_help(ctx):
    """
    Unified help command displaying all bot commands in two embeds.
    """
    # First Embed
    embed1 = discord.Embed(
        title="Bot Command Help (Part 1/2)",
        description="Here are all the available commands for this bot:",
        color=discord.Color.gold()
    )

    # General Commands
    embed1.add_field(
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
            "- Shows 5 periods of upcoming rain forecasts at your location.\n\n\n\n"
            "`!lapchecks`\n"
            "- Roll out lap checks for all positions (1-5) using a custom formula.\n\n"
            "- Displays the chance of being lap-checked, the value rolled, and the status for each position.\n\n"
        ),
        inline=False
    )

    # Weather Command
    embed1.add_field(
        name="**---------**__**WEATHER COMMAND**__**---------**",
        value=(
            "`!race <league> <round>`\n"
            "- Retrieve weather conditions at the start of a race.\n"
            "- **Leagues**: `f1`, `f2`\n"
            "- **Rounds**: `r1`, `r2`, `r3`, etc.\n\n"
            "**Examples**:\n"
            "- `!race f1 r1`\n"
            "- `!race f2`\n\n"
            "- `!race f3 r11`\n\n"
            "If no round is specified, it defaults to the nearest upcoming round.\n"
            "---\n"
            "`!weather`\n"
            "- Get the current weather conditions.\n"
            "---\n"
            "`!rain`\n"
            "- Shows 5 periods of upcoming rain forecasts for the current time.\n\n"
            "---\n"
        ),
        inline=False
    )

    # Results Command
    embed1.add_field(
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
            "If the race does not exist or there is an issue retrieving the data, an error message will be displayed.\n\n\n\n"
        ),
        inline=False
    )


    # Penalty Points Command
    embed1.add_field(
        name="**---------**__**PENALTY POINTS COMMAND**__**---------**",
        value=(
            "`!pp [league]`\n"
            "- Get penalty points for drivers in specified league.\n"
            "- **Leagues**: `F1`, `F2`, `F3` (optional - shows all if omitted)\n\n"
            "**Examples**:\n"
            "- `!pp F1` - Shows F1 penalty points\n"
            "- `!pp` - Shows penalty points for all leagues\n\n"
            "**Features**:\n"
            "- Automatically sorts drivers by points (highest first)\n"
            "- Highlights drivers with 12+ points (ban threshold)\n"
        ),
        inline=False
    )
    # Poll Commands
    embed1.add_field(
        name="**---------**__**POLL COMMANDS**__**---------**",
        value=(
            "`!poll <duration in hours>, <option1>, <option 2>, ...`\n"
            "- Create a new poll with specified options and duration.\n"
            "- **Duration**: Time in hours for how long the poll will last.\n"
            "- **Options**: The options users can vote for, separated by commas.\n\n"
            "**Example**:\n"
            "- `!poll 2, Option 1, Option 2, Option 3`\n"
            "- Creates a poll for 2 hours with 3 options.\n\n"
            "The poll will send an anonymous vote button for users to choose an option. The results will be available once the poll ends.\n\n"
        ),
        inline=False
    )
    # Send first embed
    await ctx.send(embed=embed1)

    # Second Embed
    embed2 = discord.Embed(
        title="Bot Command Help (Part 2/2)",
        color=discord.Color.gold()
    )

    # Poll Commands (continued)
    embed2.add_field(
        name="**---------**__**POLL COMMANDS (CONTINUED)**__**---------**",
        value=(
            "`!pollCorrection <poll_number> <correct_answer>`\n"
            "- Correct the correct answer for a specific poll by updating the CSV file.\n"
            "- **Poll Number**: The ID of the poll you wish to correct.\n"
            "- **Correct Answer**: The updated correct answer for the poll.\n\n"
            "**Example**:\n"
            "- `!pollCorrection 1, Option 2`\n"
            "- Updates the correct answer for poll #1 to 'Option 2'.\n\n"
            "This command can be used to correct any inaccuracies in the poll answers after the poll has ended.\n\n"

            "`!getPollLogs`\n"
            "- Retrieves and sends the CSV file containing all poll results.\n"
            "- Available to everyone.\n\n"
            "**Example**:\n"
            "- `!getPollLogs`\n"
            "- Sends the `all_polls.csv` file containing the results of all polls.\n\n"
            "This command allows users to access the poll logs for review or record-keeping.\n\n\n\n"
        ),
        inline=False
    )

    # Trainee Steward Commands
    embed2.add_field(
        name="**---------**__**TRAINEE STEWARD COMMANDS**__**---------**",
        value=(
            "`!suggestion <reason>`\n"
            "- Log a suggestion for a penalty in the current penalty thread.\n"
            "- Example: `!suggestion I think this driver deserves a 10s penalty for cutting the corner.`\n\n"
            "`!approve`\n"
            "- Used by stewards to approve a suggestion made by a trainee.\n"
            "- Reply to a suggestion and use this command to approve it.\n"
            "- Logs the suggestion as approved with the steward's name.\n\n"
            "`!listSuggestions`\n"
            "- Retrieves a list of all logged trainee suggestions in CSV format.\n"
            "- Only available to stewards or admins.\n\n\n\n"
        ),
        inline=False
    )

    # Protests Commands
    embed2.add_field(
        name="**---------**__**PROTESTS**__**---------**",
        value=(
            "`!protest <team>`\n"
            "Creates a protest for your team. Only Academy CEO can submit a protest.\n\n"
            "`!protests`\n"
            "See how many protests each team has.\n\n"
            "`!revertProtest <team>`\n"
            "If the protest was successful, their protest point will be reverted. Only Head Stewards or Admins can revert.\n\n\n\n"
        ),
        inline=False
    )

    # FIA Penalty Commands
    embed2.add_field(
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
        ),
        inline=False
    )

    # FIA Penalty Commands (continued)
    embed2.add_field(
        name="**---------**__**FIA PENALTY COMMANDS (CONTINUED)**__**---------**",
        value=(
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
            "- `!pen 10GD Skittles Penalty last race (DNF)`\n\n\n\n"
        ),
        inline=False
    )

    # Logs Commands
    embed2.add_field(
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
    embed2.add_field(
        name="**---------**__**RACE ATTENDANCE COMMANDS**__**---------**",
        value=(
            "`!RA <Track name>`\n"
            "Creates an attendance form for the entire weekend.\n\n"
            "`!RAF1 or !RAF2`\n"
            "Creates an attendance form for the specified League.\n\n"
            "`!reset F1 or !reset F2`\n"
            "Resets attendance for the specified League.\n\n\n\n"
        ),
        inline=False
    )

    # Send second embed
    await ctx.send(embed=embed2)