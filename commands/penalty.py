import asyncio
import re
import discord
from discord.ext import commands
from datetime import datetime, timedelta

from utils.common_utils import generate_embed
from utils.weather_utils import to_discord_timestamp

# ALLOWED_CHANNEL_IDS = { penalty submissions, variety submissions, testing }
ALLOWED_CHANNEL_IDS = {1324562135803494520 , 1324565883120521216, 1313982452355825667}

class PenaltyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timer_message = None
        self.timer_task = None
        self.thread_counter = 1
        self.penalty_summary = {}
        self.auto_rename_threads = False

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if self.auto_rename_threads and thread.parent_id in ALLOWED_CHANNEL_IDS:
            new_thread_name = f"{self.thread_counter}) {thread.name}"
            await thread.edit(name=new_thread_name)
            self.thread_counter += 1

    @commands.command(name='rpo', help='Start a 60-minute timer and display the status.')
    async def start_timer(self, ctx, sprint: str = None):
        self.thread_counter = 1
        self.auto_rename_threads = True

        duration = 90 if sprint and sprint.lower() == "sprint" else 60
        end_time = datetime.now() + timedelta(minutes=duration)

        embed = generate_embed(
            "FIA",
            (
                "Penalty Submission window is now OPEN!\n\n"
                ":white_small_square: Describe the incidents in the title\n"
                ":white_small_square: Open the thread within the submission window\n"
                ":white_small_square: @ all involved drivers\n"
                ":white_small_square: Submit all evidence within 24h\n"
                ":white_small_square: Leave the investigation to the FIA\n"
                ":white_small_square: You may open threads for one hour \n\n\n"
                f"The submission window closes {to_discord_timestamp(end_time, 'R')} at {to_discord_timestamp(end_time, 't')}"
            ),
            thumbnail_url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png",
        )
        self.timer_message = await ctx.send(embed=embed)
        self.timer_task = asyncio.create_task(self.wait_and_close_timer(ctx, end_time, duration))

    async def wait_and_close_timer(self, ctx, end_time, duration):
        await asyncio.sleep(duration * 60)
        self.auto_rename_threads = False
        await self.close_timer(ctx, end_time)


    async def close_timer(self, ctx, end_time):
        self.auto_rename_threads = False
        self.thread_counter = 1

        embed = generate_embed(
            "FIA",
            (
                "Penalty Submission window is now CLOSED!\n\n"
                "Abbreviations:\n"
                ":white_small_square: TLW - Track limit warning (4th = penalty)\n"
                ":white_small_square: LW - Lag warning (3rd = penalty)\n"
                ":white_small_square: REP - Reprimand (3rd = grid drop)\n"
                ":white_small_square: Xs - Time penalty\n"
                ":white_small_square: GD - Grid drop\n"
                ":white_small_square: NFA - Evidence provided but not worthy for steward action\n"
                f"The submission window closed at {to_discord_timestamp(end_time, 't')}"
            ),
            thumbnail_url="https://i.ibb.co/GVs75Rk/FV-trans-Square.png",
        )

        await ctx.send(embed=embed)

    @commands.command(name='cancel', help='Cancel the ongoing timer.')
    async def cancel_timer(self, ctx):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
            self.auto_rename_threads = False
            self.thread_counter = 1

            embed = generate_embed("Timer Cancelled", "The penalty submission timer has been cancelled.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = generate_embed("No Active Timer", "There is no ongoing timer to cancel.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    async def apply_penalty(self, ctx, amount, type_, name, reason=None):
        thread_name_parts = ctx.channel.name.split(") ", 1)
        if len(thread_name_parts) > 1:
            new_thread_name = f"{thread_name_parts[0]}) {amount}{type_} {name}"
        else:
            new_thread_name = f"{amount}{type_} {name}"
        if reason:
            new_thread_name += f" - {reason}"

        await ctx.channel.edit(name=new_thread_name)
        if ctx.channel.id not in self.penalty_summary:
            self.penalty_summary[ctx.channel.id] = []
        self.penalty_summary[ctx.channel.id].append(f"{amount}{type_} {name}" + (f" - {reason}" if reason else ""))
        embed = discord.Embed(
            description=f"Penalty applied: **{amount}{type_} {name}" + (f" - {reason}**" if reason else "**"),
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    async def apply_simple_penalty(self, ctx, action):
        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) {action.upper()}"
            if len(thread_name_parts) > 1
            else action.upper()
        )
        await ctx.channel.edit(name=new_thread_name)
        if ctx.channel.id not in self.penalty_summary:
            self.penalty_summary[ctx.channel.id] = []
        self.penalty_summary[ctx.channel.id].append(action.upper())
        embed = generate_embed("Penalty Applied",f"**{action.upper()}**", discord.Color.green())
        await ctx.send(embed=embed)

    async def rename_for_suggestion(self, ctx):
        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) Waiting for suggestion"
            if len(thread_name_parts) > 1
            else "Waiting for suggestion"
        )
        await ctx.channel.edit(name=new_thread_name)
        embed = generate_embed("Thread renamed", "Renamed to 'Waiting for suggestion'. Stewards and Trainee stewards have been notified.", discord.Color.green())
        await ctx.send(embed=embed)
        await ctx.send("<@&1172648589323939880> <@&1271689962785603654>")

    async def rename_for_pov(self, ctx, name):
        thread_name_parts = ctx.channel.name.split(") ", 1)
        new_thread_name = (
            f"{thread_name_parts[0]}) Waiting for POV {name}"
            if len(thread_name_parts) > 1
            else f"Waiting for POV {name}"
        )
        await ctx.channel.edit(name=new_thread_name)
        embed = generate_embed("Thread renamed", f"Renamed to 'Waiting for POV {name}'.", discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name='pen', help='Apply a penalty to the current thread.')
    async def pen_command(self, ctx, *, action: str):
        if not isinstance(ctx.channel, discord.Thread):
            embed = generate_embed("Invalid Channel", "This command can only be used in a thread.", discord.Color.orange())
            await ctx.send(embed=embed)
            return

        # Define no-reason actions
        no_reason_actions = ["NFA", "NFI", "LI", "RI"]
        # Define reason actions
        reason_actions = ["TLW", "LW", "REP", "SSIR"]

        # Handle penalties with amounts (e.g., "+5S", "3GD")
        match = re.match(r"(\+?\d+)(s|gd)\s+(\w+)(?:\s+(.*))?", action, re.IGNORECASE)

        if match:
            amount, type_, name, reason = match.groups()
            if type_ == "s" and (int(amount.lstrip('+')) < 1 or int(amount.lstrip('+')) > 30):
                embed = generate_embed("Invalid Amount", "Time penalty must be between 1 and 30 seconds.", discord.Color.red())
                await ctx.send(embed=embed)
                return
            if type_ == "gd" and (int(amount) < 1 or int(amount) > 30):
                embed = generate_embed("Invalid Amount", "Grid drops must be between 1 and 30 positions.", discord.Color.red())
                await ctx.send(embed=embed)
                return
            await self.apply_penalty(ctx, amount, type_, name, reason)

        # Handle reason-based penalties
        elif action.upper().split()[0] in [a.upper() for a in reason_actions]:
            parts = action.split(maxsplit=2)
            if len(parts) < 2:
                embed = generate_embed("Invalid Format", "Use !pen <action> <name> *<reason> *(* optional)*.", discord.Color.red())
                await ctx.send(embed=embed)
                return
            pen = parts[0].upper()
            name = parts[1]
            reason = parts[2].strip() if len(parts) > 2 else None
            await self.apply_penalty(ctx, "", pen, name, reason)

        # Handle no-reason penalties
        elif action.upper() in [a.upper() for a in no_reason_actions]:
            await self.apply_simple_penalty(ctx, action)

        # Handle suggestion case
        elif action.lower() == "sug":
            await self.rename_for_suggestion(ctx)

        # Handle POV case
        elif action.lower().startswith("pov"):
            name = action.split(maxsplit=1)[1] if len(action.split()) > 1 else "Unknown"
            await self.rename_for_pov(ctx, name)

        else:
            embed = generate_embed("Invalid Penalty", "Invalid penalty action or format.", discord.Color.red())
            await ctx.send(embed=embed)
