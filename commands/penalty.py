import asyncio
import re
from datetime import datetime, timedelta

import discord

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.weather_utils import to_discord_timestamp

timer_message = None
timer_task = None
thread_counter = 1
penalty_summary = {}

@commands.command(name='rpo', help='Start a 60-minute timer and display the status.')
async def start_timer(ctx):
    global timer_message, timer_task

    # Calculate the end time
    end_time = datetime.now() + timedelta(minutes=60)
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
    # Wait for 60 minutes
    await asyncio.sleep(60 * 60)

    # After 60 minutes, call !rpc internally
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
    global timer_task, timer_message, thread_counter

    if timer_task and not timer_task.done():
        timer_task.cancel()
        thread_counter = 1
        await ctx.send("Timer has been cancelled.")
    else:
        await ctx.send("No active timer to cancel.")

@commands.command(name='pstart', help='Initialize the thread with a numbered prefix.')
async def pen_start(ctx):
    global thread_counter, penalty_summary

    # Ensure the command is used in a thread
    if isinstance(ctx.channel, discord.Thread):
        # Check if the thread is already initialized
        if ctx.channel.id in penalty_summary:
            await ctx.send("This thread has already been initialized for penalties.")
            return

        # Check if the thread already starts with a number prefix
        if ctx.channel.name.startswith(f"{thread_counter})"):
            await ctx.send("This thread is already correctly prefixed.")
            return

        # Rename the thread to include the thread number
        try:
            new_thread_name = f"{thread_counter}) {ctx.channel.name}"
            await ctx.channel.edit(name=new_thread_name)
            penalty_summary[ctx.channel.id] = []  # Initialize summary for this thread

            await ctx.send(f"Thread initialized as {new_thread_name}.")
            thread_counter += 1  # Increment the thread counter
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            return
    else:
        # Notify the user if the command is not issued in a thread
        await ctx.send("This command can only be used in a thread.")

@commands.command(name='pen', help='Apply a penalty to the current thread.')
async def pen_command(ctx, *, action: str):
    global penalty_summary

    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("This command can only be used in a thread.")
        return

    # Define no-reason actions
    no_reason_actions = ["NFA", "NFI", "LI", "RI"]

    # Parse penalties with amounts (e.g., "5S", "3GD")
    match = re.match(r"(\d+)(S|GD)\s*(.*)", action)
    if match:
        amount = int(match.group(1))
        type_ = match.group(2)
        reason = match.group(3).strip() if match.group(3) else "No reason provided"

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
            new_thread_name = f"{thread_name_parts[0]}) {amount}{type_} {reason}"
        else:
            new_thread_name = f"{amount}{type_} {reason}"
        await ctx.channel.edit(name=new_thread_name)

        # Update the summary
        if ctx.channel.id not in penalty_summary:
            penalty_summary[ctx.channel.id] = []
        penalty_summary[ctx.channel.id].append(f"{amount}{type_} - {reason}")
        await ctx.send(f"Penalty applied: {amount}{type_} - {reason}")
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
    required_role = "Academy CEO"  # Replace with the actual role name
    if required_role not in [role.name for role in ctx.author.roles]:
        await ctx.send("You do not have permission to use this command.")
        return

    await ctx.send("Protest submitted.")

