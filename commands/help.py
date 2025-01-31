import discord
from discord.ext import commands

@commands.command(name="help")
async def show_help(ctx, *, arg: str = None):
    """
    Custom help command displaying bot commands in an embed.
    """
    if arg and arg.lower() == "fia":
        # Display FIA-specific help
        embed = discord.Embed(
            title="FIA Penalty Commands",
            description="Here are the available FIA penalty commands:",
            color=discord.Color.red()  # Use a suitable color for the embed
        )

        # Add FIA command descriptions
        embed.add_field(
            name="`!pen <action> [name] [reason]`",
            value=(
                "Apply a penalty to the current thread.\n\n"
                "**Actions**:\n"
                "- `NFA`: No Further Action\n"
                "- `NFI`: No Further Investigation\n"
                "- `LI`: Light Investigation\n"
                "- `RI`: Regular Investigation\n"
                "- `TLW`: Time Loss Warning\n"
                "- `LW`: License Warning\n"
                "- `REP`: Reprimand\n"
                "- `SSIR`: Stop and Start Investigation Required\n"
                "- `5S`: 5-Second Time Penalty\n"
                "- `3GD`: 3-Grid Drop Penalty\n\n"
                "**Examples**:\n"
                "- `!pen NFA`\n"
                "- `!pen 5S John Blocking`\n"
                "- `!pen TLW Jane Ignoring Blue Flags`"
            ),
            inline=False
        )

        embed.add_field(
            name="`!rpo`",
            value=(
                "Request a Race Penalty Overview.\n\n"
                "This command generates a summary of all penalties applied in the current thread."
            ),
            inline=False
        )

        await ctx.send(embed=embed)
    else:
        # Display general help
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

        embed.add_field(
            name="`!help fia`",
            value="Display FIA penalty-related commands.",
            inline=False
        )

        await ctx.send(embed=embed)


@commands.command(name="rpo")
async def race_penalty_overview(ctx):
    """
    Generate a Race Penalty Overview for the current thread.
    """
    global penalty_summary

    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in a thread.")
        return

    if ctx.channel.id not in penalty_summary or not penalty_summary[ctx.channel.id]:
        await ctx.send("No penalties have been applied in this thread.")
        return

    # Create an embed for the penalty overview
    embed = discord.Embed(
        title="Race Penalty Overview",
        description="Here are the penalties applied in this thread:",
        color=discord.Color.orange()  # Use a suitable color for the embed
    )

    # Add each penalty to the embed
    for penalty in penalty_summary[ctx.channel.id]:
        embed.add_field(
            name="Penalty",
            value=penalty,
            inline=False
        )

    await ctx.send(embed=embed)