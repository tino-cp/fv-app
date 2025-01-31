import asyncio
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.weather_utils import to_discord_timestamp

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

# Global variables
timer_message = None
timer_task = None
thread_counter = 1
penalty_summary = {}
auto_rename_threads = False


class PenaltyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_rename_threads = False
        self.thread_counter = 1

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.auto_rename_threads:
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
    global thread_counter

    # Reset thread counter when the timer is closed
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
        await ctx.send("Timer has been cancelled.")
    else:
        await ctx.send("No active timer to cancel.")

@commands.command(name='pen', help='Apply a penalty to the current thread.')
async def pen_command(ctx, *, action: str):
    global penalty_summary

    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in a thread.")
        return

    # Define no-reason actions
    no_reason_actions = ["NFA", "NFI", "LI", "RI"]
    # Define actions that require name and reason
    name_reason_actions = ["TLW", "LW", "REP", "SSIR"]

    # Parse penalties with amounts (e.g., "5S", "3GD")
    match = re.match(r"(\d+)(S|GD)\s+(\w+)\s+(.*)", action)
    if match:
        amount = int(match.group(1))
        type_ = match.group(2)
        name = match.group(3)
        reason = match.group(4).strip() if match.group(4) else "No reason provided"

        # Validate input ranges
        if type_ == "S" and (amount < 1 or amount > 30):
            await ctx.send("Time penalty must be between 1 and 30 seconds.")
            return
        if type_ == "GD" and (amount < 1 or amount > 10):
            await ctx.send("Grid drops must be between 1 and 10 positions.")
            return

        # Update thread name and summary
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) {amount}{type_} {name} - {reason}"
        else:
            new_thread_name = f"{amount}{type_} {name} - {reason}"
        await ctx.channel.edit(name=new_thread_name)

        # Update the summary
        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(f"{amount}{type_} {name} - {reason}")
        await ctx.send(f"Penalty applied: {amount}{type_} {name} - {reason}")
    elif action.split()[0] in name_reason_actions:
        # Handle penalties that require name and reason
        parts = action.split(maxsplit=2)
        if len(parts) < 3:
            await ctx.send("Invalid format. Use !pen <pen> <name> <reason>")
            return
        pen, name, reason = parts
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) {pen} {name} - {reason}"
        else:
            new_thread_name = f"{pen} {name} - {reason}"
        await ctx.channel.edit(name=new_thread_name)

        # Update the summary
        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(f"{pen} {name} - {reason}")
        await ctx.send(f"Penalty applied: {pen} {name} - {reason}")
    elif action in no_reason_actions:
        # Handle no-reason penalties
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) {action}"
        else:
            new_thread_name = f"{action}"
        await ctx.channel.edit(name=new_thread_name)

        # Update the summary
        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(action)
        await ctx.send(f"Penalty applied: {action}")
    elif action.lower() == "sug":
        # Handle suggestion command
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) Waiting for suggestion"
        else:
            new_thread_name = "Waiting for suggestion"
        await ctx.channel.edit(name=new_thread_name)
        await ctx.send("@trainee-stewards @stewards")
        await ctx.send("Thread renamed to 'Waiting for suggestion' and trainee stewards & stewards have been notified.")
    elif action.lower().startswith("pov"):
        # Handle POV command
        name = action.split(maxsplit=1)[1] if len(action.split()) > 1 else "Unknown"
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) Waiting for POV {name}"
        else:
            new_thread_name = f"Waiting for POV {name}"
        await ctx.channel.edit(name=new_thread_name)
        await ctx.send(f"Thread renamed to 'Waiting for POV {name}'.")
    else:
        await ctx.send("Invalid penalty action or format. Use !pen start to initialize the thread first.")


@commands.command(name='psum', help='Display the penalty summary for this thread.')
async def pen_summary(ctx):
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in a thread.")
        return

    if ctx.channel.id not in penalty_summary or not penalty_summary[ctx.channel.id]:
        await ctx.send("No penalties applied to this thread yet.")
        return

    summary = "\n".join(penalty_summary[ctx.channel.id])
    await ctx.send(f"Penalty Summary:\n{summary}")

@commands.command(name='protest', help='Submit a protest.')
async def protest_command(ctx):
    # Check if the user has the required role
    required_role = "Academy CEO"
    if required_role not in [role.name for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await ctx.send("Protest submitted.")
