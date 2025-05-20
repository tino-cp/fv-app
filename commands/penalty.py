import asyncio
import re
from datetime import datetime, timedelta
import os
import csv

import discord
from discord.ext import commands

from utils.weather_utils import to_discord_timestamp

# Get server IDs as a set of integers
ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)

# Global variables
timer_message = None
timer_task = None
thread_counter = 1
penalty_summary = {}
auto_rename_threads = False

LOG_FILE = "penalty_log.txt"
CSV_LOG_FILE = "penalty_log.csv"

def log_penalty(user: str, action: str, thread_name: str):
    """Append penalty details to a log file."""
    log_entry = f"{action} \t by \t {user} \t in thread \t {thread_name}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def log_penalty_csv(user: str, action_list: list[str], thread_name: str, league: str = "?"):
    try:
        match = re.match(r"(\w+)\s+(\d+)\)", thread_name)
        league_from_name, thread_num = match.groups() if match else (league, "?")
    except Exception:
        league_from_name, thread_num = league, "?"

    combined_actions = "/".join(action_list)

    with open(CSV_LOG_FILE, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([league_from_name, thread_num, combined_actions, user])

def add_tick_to_name(name: str) -> str:
    """Add ✅ at the start if not already present."""
    return name if name.startswith("✅") else f"✅ {name}"

ALLOWED_CHANNEL_IDS = {1324562135803494520 , 1324565883120521216, 1313982452355825667, 1334666588997161074, 1177033855799132181,1361890376125780180, 1361678727876182106}

class PenaltyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_rename_threads = False
        self.thread_counter = 1
        self.current_league = None  

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.auto_rename_threads and thread.parent_id in ALLOWED_CHANNEL_IDS:
            new_thread_name = f"{self.current_league} {self.thread_counter}) {thread.name}"
            await thread.edit(name=new_thread_name)
            self.thread_counter += 1

@commands.command(name='rpo', help='Start a timer and display the status (can specify duration).')
async def start_timer(ctx, league: str = None, sprint: str = None, duration: int = 60):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return
    
    # ✅ Role check
    allowed_roles = ["Admin", "Steward", "League Director"]
    user_roles = [role.name for role in ctx.author.roles]

    if not any(role in user_roles for role in allowed_roles):
        await ctx.send("🚫 You do not have permission to use this command.")
        return
    
    global timer_message, timer_task, auto_rename_threads, thread_counter

    # Modify league check to include F3 and General
    if league not in ["F1", "F2", "F3", "general", "MotoVGP", "Indy"]:
        await ctx.send("Invalid league! Please use `!rpo F1`, `!rpo F2`, `!rpo F3`, `!rpo Indy`, `!rpo MotoVGP` or `!rpo general`.")
        return

    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.thread_counter = 1
        cog.auto_rename_threads = True
        cog.current_league = league
    thread_counter = 1
    auto_rename_threads = True

    # Allow the user to set the duration (in minutes). Default is 60, otherwise 90 if sprint is provided.
    if sprint and sprint.lower() == "sprint":
        duration = 90
    elif sprint is None:
        duration = 60
    else:
        try:
            duration = int(sprint)
        except ValueError:
            await ctx.send("Invalid duration! Please provide a number.")
            return

    end_time = datetime.now() + timedelta(minutes=duration)
    end_time_str = to_discord_timestamp(end_time, 't')
    countdown_str = to_discord_timestamp(end_time, 'R')

    embed = discord.Embed(
        title="FIA",
        description=(f"Penalty Submission window is now OPEN!\n\n"
                     ":white_small_square: Describe the incidents in the title\n"
                     ":white_small_square: Open the thread within the submission window\n"
                     ":white_small_square: @ all involved drivers\n"
                     ":white_small_square: Submit all evidence within 24h\n"
                     ":white_small_square: Leave the investigation to the FIA\n\n\n"
                     f"The submission window closes {countdown_str} at {end_time_str}"),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")
    timer_message = await ctx.send(embed=embed)
    timer_task = asyncio.create_task(wait_and_close_timer(ctx, end_time))
    thread = await ctx.channel.create_thread(name=f"{league} {thread_counter})")
    thread_counter += 1

async def wait_and_close_timer(ctx, end_time):
    global auto_rename_threads
    await asyncio.sleep((end_time - datetime.now()).total_seconds())
    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.auto_rename_threads = False
    auto_rename_threads = False
    await update_timer_message()
    await close_timer(ctx, end_time)

async def update_timer_message():
    global timer_message
    if timer_message:
        embed = discord.Embed(
            title="FIA",
            description="Penalty Submission window is now OPEN!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")
        await timer_message.edit(embed=embed)

async def close_timer(ctx, end_time):
    global thread_counter, auto_rename_threads
    cog = ctx.bot.get_cog('PenaltyCog')
    if cog:
        cog.thread_counter = 1
        cog.auto_rename_threads = False
    auto_rename_threads = False
    thread_counter = 1

    embed = discord.Embed(
        title="FIA",
        description=(f"Penalty Submission window is now CLOSED!\n\n"
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
                     ":white_small_square: SSIR - Incident was self-served in race\n\n"
                     f"The submission window closed at {to_discord_timestamp(end_time, 't')}"),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png")
    await ctx.send(embed=embed)

@commands.command(name='cancel', help='Cancel the ongoing timer.')
async def cancel_timer(ctx):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return
    # ✅ Role check
    allowed_roles = ["Admin", "Steward"]
    user_roles = [role.name for role in ctx.author.roles]

    if not any(role in user_roles for role in allowed_roles):
        await ctx.send("🚫 You do not have permission to use this command.")
        return    
    
    global timer_task, timer_message, auto_rename_threads, thread_counter
    if timer_task and not timer_task.done():
        timer_task.cancel()
        cog = ctx.bot.get_cog('PenaltyCog')
        if cog:
            cog.thread_counter = 1
            cog.auto_rename_threads = False
        auto_rename_threads = False
        thread_counter = 1
        embed = discord.Embed(title="Timer Cancelled", description="The penalty submission timer has been cancelled.", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="No Active Timer", description="There is no ongoing timer to cancel.", color=discord.Color.orange())
        await ctx.send(embed=embed)

@commands.command(name='pen', help='Apply a penalty to the current thread.')
async def pen_command(ctx, *, action: str):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return
    # ✅ Role check
    allowed_roles = ["Admin", "Steward", "League Director"]
    user_roles = [role.name for role in ctx.author.roles]

    if not any(role in user_roles for role in allowed_roles):
        await ctx.send("🚫 You do not have permission to use this command.")
        return    
    
    global penalty_summary
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send(embed=discord.Embed(title="Invalid Channel", description="This command can only be used in a thread.", color=discord.Color.orange()))
        return

    thread_name = ctx.channel.name
    user = str(ctx.author)
    cog = ctx.bot.get_cog('PenaltyCog')
    league = cog.current_league if cog else "?"

    no_reason_actions = ["NFA", "NFI", "LI", "RI", "NFH", "SSIR"]
    name_reason_actions = ["TLW", "LW", "REP", "DSQ", "BOTG"]
    if action.lower().startswith("pov "):
        parts = action.split(maxsplit=1)
        if len(parts) < 2:
            await ctx.send(embed=discord.Embed(description="Invalid format. Use `!pen pov <name>`.", color=discord.Color.red()))
            return
        pov_name = parts[1]
        thread_name_parts = ctx.channel.name.split(") ", 1)
        prefix = thread_name_parts[0] if len(thread_name_parts) > 1 else f"{league} ?"
        new_thread_name = f"{prefix}) Waiting for POV {pov_name}"
        try:
            await ctx.channel.edit(name=new_thread_name)
        except discord.HTTPException as e:
            if e.status == 429:
                await ctx.send("⚠️ Discord is rate limiting thread renames. Please wait a moment.")
                await asyncio.sleep(10)
            else:
                raise
        penalty_summary.setdefault(ctx.channel.id, []).append(f"Waiting for POV {pov_name}")
        await ctx.send(embed=discord.Embed(description=f"POV requested from **{pov_name}**.", color=discord.Color.green()))
        return

    if action.lower().strip() == "sug":
        thread_name_parts = ctx.channel.name.split(") ", 1)
        prefix = thread_name_parts[0] if len(thread_name_parts) > 1 else f"{league} ?"
        new_thread_name = f"{prefix}) Waiting for a suggestion"
        try:
            await ctx.channel.edit(name=new_thread_name)
        except discord.HTTPException as e:
            if e.status == 429:
                await ctx.send("⚠️ Discord is rate limiting thread renames. Please wait a moment.")
                await asyncio.sleep(10)
            else:
                raise
        penalty_summary.setdefault(ctx.channel.id, []).append("Waiting for a suggestion")
        await ctx.send(embed=discord.Embed(description="Thread renamed: **Waiting for a suggestion**", color=discord.Color.green()))
        return

    penalties = [p.strip() for p in action.split(',') if p.strip()]
    applied_penalties = []

    for penalty in penalties:
        match = re.match(r"(\+?\d+)(s|gd)\s+(\w+)(?:\s+(.*))?", penalty, re.IGNORECASE)
        if match:
            amount = match.group(1)
            type_ = match.group(2).lower()
            name = match.group(3)
            reason = match.group(4).strip() if match.group(4) else None

            if type_ == "s" and not (1 <= int(amount.lstrip('+')) <= 30):
                await ctx.send(embed=discord.Embed(description=f"Time penalty for {name} must be between 1 and 30 seconds.", color=discord.Color.red()))
                return
            if type_ == "gd" and not (1 <= int(amount) <= 30):
                await ctx.send(embed=discord.Embed(description=f"Grid drop for {name} must be between 1 and 30 positions.", color=discord.Color.red()))
                return

            full = f"{amount}{type_} {name}" + (f" - {reason}" if reason else "")
            applied_penalties.append(full)
            log_penalty_csv(user, applied_penalties, thread_name, cog.current_league if cog else "?")
            continue

        match_tlw = re.match(r"(\d+)\s+TLW\s+(\w+)", penalty, re.IGNORECASE)
        if match_tlw:
            amount = int(match_tlw.group(1))
            name = match_tlw.group(2)
            if not (1 <= amount <= 10):
                await ctx.send(embed=discord.Embed(description=f"TLW penalty for {name} must be between 1 and 10.", color=discord.Color.red()))
                return
            full = f"{amount} TLW {name}"
            applied_penalties.append(full)
            log_penalty_csv(user, applied_penalties, thread_name, cog.current_league if cog else "?")
            continue

        parts = penalty.split(maxsplit=2)
        if len(parts) >= 2 and parts[0].upper() in name_reason_actions:
            pen = parts[0].upper()
            name = parts[1]
            reason = parts[2] if len(parts) == 3 else None
            full = f"{pen} {name}" + (f" - {reason}" if reason else "")
            applied_penalties.append(full)
            log_penalty_csv(user, applied_penalties, thread_name, cog.current_league if cog else "?")

            continue

        if penalty.upper() in no_reason_actions:
            applied_penalties.append(penalty.upper())
            log_penalty_csv(user, applied_penalties, thread_name, cog.current_league if cog else "?")

            continue

        await ctx.send(embed=discord.Embed(description=f"Invalid penalty format: `{penalty}`", color=discord.Color.red()))
        return

    prefix = ctx.channel.name.split(") ", 1)[0]
    new_thread_name = f"✅ {prefix}) " + ", ".join([p.split(" - ")[0] for p in applied_penalties])
    try:
        await ctx.channel.edit(name=new_thread_name)
    except discord.HTTPException as e:
        if e.status == 429:
            await ctx.send("⚠️ Discord is rate limiting thread renames. Please wait a moment.")
            await asyncio.sleep(10)
        else:
            raise
    penalty_summary.setdefault(ctx.channel.id, []).extend(applied_penalties)
    embed = discord.Embed(description="\n".join([f"Penalty applied: **{pen}**" for pen in applied_penalties]), color=discord.Color.green())
    await ctx.send(embed=embed)

@commands.command(name='psum', help='Display the penalty summary for this thread.')
async def pen_summary(ctx):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send(embed=discord.Embed(title="Invalid Channel", description="This command can only be used in a thread.", color=discord.Color.orange()))
        return
    if ctx.channel.id not in penalty_summary or not penalty_summary[ctx.channel.id]:
        await ctx.send(embed=discord.Embed(title="No Penalties", description="No penalties applied to this thread yet.", color=discord.Color.orange()))
        return
    summary = "\n".join(penalty_summary[ctx.channel.id])
    embed = discord.Embed(title="Penalty Summary", description=summary, color=discord.Color.blue())
    await ctx.send(embed=embed)

