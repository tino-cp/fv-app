from discord.ext import commands
import discord
import csv
import os
from datetime import datetime


# Get server IDs as a set of integers
ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)

CSV_FILE = "trainee_suggestions.csv"

class TraineeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestion_map = {}  # message.id -> (trainee, message, thread_link)

        # Ensure CSV has headers
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Trainee", "Suggestion", "Thread Link", "Status", "Timestamp"])

    @commands.command(name='suggestion')
    async def suggestion(self, ctx, *, message: str):
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
        
        
        """Trainees log a penalty suggestion"""
        if not any(role.name == ["Trainee Steward", "Steward"] for role in ctx.author.roles):
            await ctx.send("🚫 Only Trainees can use this command.")
            return

        if not isinstance(ctx.channel, discord.Thread):
            await ctx.send("❌ Please use this command inside a penalty thread.")
            return

        trainee = str(ctx.author)
        thread_link = ctx.channel.jump_url
        timestamp = datetime.utcnow().isoformat()

        # Log suggestion to CSV
        with open(CSV_FILE, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([trainee, message, thread_link, "pending", timestamp])

        # Store message ID for approval tracking
        self.suggestion_map[ctx.message.id] = (trainee, message, thread_link)

        await ctx.send(f"✅ Suggestion from **{trainee}** logged.\nThread: {thread_link}")

    @commands.command(name='approve', aliases=['approved', 'Aprroved', 'Approve'])
    async def approve(self, ctx):
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
        """Steward approves a trainee suggestion (must reply to original message)"""
        if not any(role.name == "Steward" for role in ctx.author.roles):
            await ctx.send("🚫 Only Stewards can approve suggestions.")
            return

        if not ctx.message.reference:
            await ctx.send("❌ You need to reply to a trainee's suggestion to approve it.")
            return

        try:
            original = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.send("❌ Could not find the original message.")
            return

        suggestion_data = self.suggestion_map.get(original.id)
        if not suggestion_data:
            await ctx.send("⚠️ That message is not tracked as a suggestion.")
            return

        trainee, message, thread_link = suggestion_data
        steward = str(ctx.author)
        timestamp = datetime.utcnow().isoformat()

        # Log approval to CSV
        with open(CSV_FILE, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([trainee, message, thread_link, f"approved by {steward}", timestamp])

        await ctx.send(f"✅ Suggestion from **{trainee}** approved by **{steward}** in thread **{ctx.channel.name}**.")


    @commands.command(name='listSuggestions', aliases=['ls', 'suggestionList', 'ListSuggestion'])
    async def list_suggestions(self, ctx):
        """Send the full trainee_suggestions.csv file"""
        if not any(role.name in ["Steward", "Admin"] for role in ctx.author.roles):
            await ctx.send("🚫 Only Stewards or Admins can list suggestions.")
            return

        if not os.path.exists(CSV_FILE):
            await ctx.send("⚠️ No suggestions have been logged yet.")
            return

        await ctx.send(file=discord.File(CSV_FILE))

def setup(bot):
    bot.add_cog(TraineeCog(bot))
