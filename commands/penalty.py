import asyncio
import re
from datetime import datetime, timedelta
import os

import discord
from discord.ext import commands

from utils.weather_utils import to_discord_timestamp

# Global variables
timer_message = None
timer_task = None
thread_counter = 1
penalty_summary = {}
auto_rename_threads = False

LOG_FILE = "penalty_log.txt"

def log_penalty(user: str, action: str, thread_name: str):
    """Append penalty details to a log file."""
    log_entry = f"{action} \t by \t {user} \t in thread \t {thread_name}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)




# ALLOWED_CHANNEL_IDS = { penalty submissions, variety submissions, testing }
ALLOWED_CHANNEL_IDS = {1324562135803494520 , 1324565883120521216, 1313982452355825667}

class PenaltyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_rename_threads = False
        self.thread_counter = 1

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.auto_rename_threads and thread.parent_id in ALLOWED_CHANNEL_IDS:
            new_thread_name = f"{self.thread_counter}) {thread.name}"
            await thread.edit(name=new_thread_name)
            self.thread_counter += 1

@commands.command(name='rpo', help='Start a 60-minute timer and display the status.')
async def start_timer(ctx, sprint: str = None):
    global timer_message, timer_task, auto_rename_threads, thread_counter

    # Reset thread counter and enable auto-renaming
    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.thread_counter = 1
        cog.auto_rename_threads = True
    thread_counter = 1
    auto_rename_threads = True

    if sprint and sprint.lower() == "sprint":
        duration = 90
    else:
        duration = 60

    # Calculate the end time
    end_time = datetime.now() + timedelta(minutes=duration)
    end_time_str = to_discord_timestamp(end_time, 't')
    countdown_str = to_discord_timestamp(end_time, 'R')

    # Create the embed message
    embed = discord.Embed(
        title="FIA",
        description=(
            "Penalty Submission window is now OPEN!\n\n"
            ":white_small_square: Describe the incidents in the title\n"
            ":white_small_square: Open the thread within the submission window\n"
            ":white_small_square: @ all involved drivers\n"
            ":white_small_square: Submit all evidence within 24h\n"
            ":white_small_square: Leave the investigation to the FIA\n\n\n"
            f"The submission window closes {countdown_str} at {end_time_str}"
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")

    # Send the initial timer message
    timer_message = await ctx.send(embed=embed)

    # Start the timer task
    timer_task = asyncio.create_task(wait_and_close_timer(ctx, end_time))

async def wait_and_close_timer(ctx, end_time):
    global auto_rename_threads

    # Wait for 60 minutes
    await asyncio.sleep(60 * 60)

    # After 60 minutes, disable auto-renaming and close the timer
    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.auto_rename_threads = True
    auto_rename_threads = False
    await update_timer_message()
    await close_timer(ctx, end_time)

async def update_timer_message():
    global timer_message

    if timer_message:
        # Update the embed message to show the window is closed
        embed = discord.Embed(
            title="FIA",
            description=(
                "Penalty Submission window is now OPEN!\n\n"
                ":white_small_square: Describe the incidents in the title\n"
                ":white_small_square: Open the thread within the submission window\n"
                ":white_small_square: @ all involved drivers\n"
                ":white_small_square: Submit all evidence within 24h\n"
                ":white_small_square: Leave the investigation to the FIA\n\n\n"
            ),
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")

        # Edit the original message
        await timer_message.edit(embed=embed)

async def close_timer(ctx, end_time):
    global thread_counter, auto_rename_threads

    # Reset thread counter when the timer is closed
    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.thread_counter = 1
        cog.auto_rename_threads = False
    auto_rename_threads = False
    thread_counter = 1

    # Create the embed message
    embed = discord.Embed(
        title="FIA",
        description=(
            "Penalty Submission window is now CLOSED!\n\n"
            "Abbreviations:\n"
            ":white_small_square: TLW - Track limit warning (4th = penalty)\n"
            ":white_small_square: LW - Lag warning (3rd = penalty)\n"
            ":white_small_square: LI - Incident involving lag was judged by the stewards not worth a penalty\n"
            ":white_small_square: REP - Reprimand (3rd = grid drop)\n"
            ":white_small_square: Xs - Time penalty\n"
            ":white_small_square: GD - Grid drop\n"
            ":white_small_square: NFA - Evidence provided but not worthy for steward action\n"
            ":white_small_square: NFI - No evidence provided to the FIA\n"
            ":white_small_square: RI - Incident was judged by the stewards not worth a penalty\n"
            ":white_small_square: SSIR - Incident was self-served in race\n\n\n"
            f"The submission window closed at {to_discord_timestamp(end_time, 't')}"
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")

    # Send the closed timer message
    await ctx.send(embed=embed)

@commands.command(name='cancel', help='Cancel the ongoing timer.')
async def cancel_timer(ctx):
    global timer_task, timer_message, auto_rename_threads, thread_counter

    if timer_task and not timer_task.done():
        timer_task.cancel()

        cog = ctx.bot.get_cog('PenaltyCog')
        if cog:
            cog.thread_counter = 1
            cog.auto_rename_threads = False
        auto_rename_threads = False
        thread_counter = 1

        embed = discord.Embed(
            title="Timer Cancelled",
            description="The penalty submission timer has been cancelled.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="No Active Timer",
            description="There is no ongoing timer to cancel.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

@commands.command(name='pen', help='Apply a penalty to the current thread.')
async def pen_command(ctx, *, action: str):
    global penalty_summary

    if not isinstance(ctx.channel, discord.Thread):
        embed = discord.Embed(
            title="Invalid Channel",
            description="This command can only be used in a thread.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    thread_name = ctx.channel.name
    user = ctx.author.display_name

    # Define no-reason actions (case-insensitive)
    no_reason_actions = ["NFA", "NFI", "LI", "RI"]
    # Define actions that require name but reason is optional (case-insensitive)
    name_reason_actions = ["TLW", "LW", "REP", "SSIR"]

    # Handle penalties with amounts (e.g., "+5S", "3GD")
    match = re.match(r"(\+?\d+)(s|gd)\s+(\w+)(?:\s+(.*))?", action, re.IGNORECASE)
    if match:
        amount = match.group(1)  # Includes "+" if present
        type_ = match.group(2).lower()  # Uniformly lowercase
        name = match.group(3)  # Retains original casing
        reason = match.group(4).strip() if match.group(4) else None

        # Validate ranges
        if type_ == "s" and (int(amount.lstrip('+')) < 1 or int(amount.lstrip('+')) > 30):
            embed = discord.Embed(description="Time penalty must be between 1 and 30 seconds.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        if type_ == "gd" and (int(amount) < 1 or int(amount) > 30):
            embed = discord.Embed(description="Grid drops must be between 1 and 30 positions.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) {amount}{type_} {name}" + (f" - {reason}" if reason else "")
            if len(thread_name_parts) > 1
            else f"{amount}{type_} {name}" + (f" - {reason}" if reason else "")
        )
        await ctx.channel.edit(name=new_thread_name)

        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(f"{amount}{type_} {name}" + (f" - {reason}" if reason else ""))

        # **Log successful penalty**
        log_penalty(user, f"{amount}{type_} {name}" + (f" - {reason}" if reason else ""), thread_name)

        embed = discord.Embed(
            description=f"Penalty applied: **{amount}{type_} {name}" + (f" - {reason}**" if reason else "**"),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    elif action.upper().split()[0] in [a.upper() for a in name_reason_actions]:
        parts = action.split(maxsplit=2)
        if len(parts) < 2:
            embed = discord.Embed(description="Invalid format. Use !pen <action> <name> *<reason> (* optional).", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        pen = parts[0].upper()
        name = parts[1]
        reason = parts[2].strip() if len(parts) > 2 else None

        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) {pen} {name}" + (f" - {reason}" if reason else "")
            if len(thread_name_parts) > 1
            else f"{pen} {name}" + (f" - {reason}" if reason else "")
        )
        await ctx.channel.edit(name=new_thread_name)

        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(f"{pen} {name}" + (f" - {reason}" if reason else ""))

        # **Log successful penalty**
        log_penalty(user, f"{pen} {name}" + (f" - {reason}" if reason else ""), thread_name)

        embed = discord.Embed(
            description=f"Penalty applied: **{pen} {name}" + (f" - {reason}**" if reason else "**"),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    elif action.upper() in [a.upper() for a in no_reason_actions]:
        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) {action.upper()}"
            if len(thread_name_parts) > 1
            else action.upper()
        )
        await ctx.channel.edit(name=new_thread_name)

        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(action.upper())

        # **Log successful penalty**
        log_penalty(user, action.upper(), thread_name)

        embed = discord.Embed(
            description=f"Penalty applied: **{action.upper()}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            description="Invalid penalty action or format.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@commands.command(name='psum', help='Display the penalty summary for this thread.')
async def pen_summary(ctx):
    if not isinstance(ctx.channel, discord.Thread):
        embed = discord.Embed(
            title="Invalid Channel",
            description="This command can only be used in a thread.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    if ctx.channel.id not in penalty_summary or not penalty_summary[ctx.channel.id]:
        embed = discord.Embed(
            title="No Penalties",
            description="No penalties applied to this thread yet.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    summary = "\n".join(penalty_summary[ctx.channel.id])
    embed = discord.Embed(
        title="Penalty Summary",
        description=summary,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
