import discord
from discord.ext import commands
from discord.ui import View, Button
import csv
import os
import asyncio
from datetime import datetime, timedelta
import json

# Get server IDs as a set of integers
ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)

class PollView(View):
    def __init__(self, options, timeout, poll_id, notification_channel=None, creator_id=None):
        super().__init__(timeout=timeout)
        self.options = options
        self.votes = {}
        self.poll_id = poll_id
        self.notification_channel = notification_channel  # Store the channel for notifications
        self.creator_id = creator_id  # Store the creator's user ID
        self.timeout = timeout

        # Save poll data to JSON when the poll starts
        self.save_poll_data()

        for idx, option in enumerate(options):
            button = Button(label=option, custom_id=f"poll_{poll_id}_{idx}", style=discord.ButtonStyle.primary)
            button.callback = self.vote
            self.add_item(button)

        # Add the End Poll button (red)
        end_poll_button = Button(label="End Poll", custom_id=f"end_poll_{poll_id}", style=discord.ButtonStyle.danger)
        end_poll_button.callback = self.end_poll
        self.add_item(end_poll_button)

    def save_poll_data(self):
        """Save ongoing poll data to a JSON file."""
        poll_data = {
            'poll_id': self.poll_id,
            'options': self.options,
            'votes': self.votes,
            'creator_id': self.creator_id,
            'end_time': str(datetime.utcnow() + timedelta(seconds=self.timeout)),
            'message_id': getattr(self, "message_id", None),
            'channel_id': getattr(self, "channel_id", None)
        }
        with open(f"poll_results/poll_{self.poll_id}.json", "w", encoding="utf-8") as f:
            json.dump(poll_data, f, ensure_ascii=False, indent=4)

    async def vote(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name  # Get the username
        option_index = int(interaction.data['custom_id'].split('_')[-1])

        if user_id in self.votes:
            previous_option = self.votes[user_id]["vote"]
            if previous_option == option_index:
                await interaction.response.send_message("You already voted for this option!", ephemeral=True)
                return
            else:
                self.votes[user_id] = {"username": username, "vote": option_index}
                await interaction.response.send_message(f"Your vote has been changed to **{self.options[option_index]}**!", ephemeral=True)
        else:
            self.votes[user_id] = {"username": username, "vote": option_index}
            await interaction.response.send_message(f"Your vote has been recorded anonymously! You voted for **{self.options[option_index]}**.", ephemeral=True)

        # ✅ Save updated votes to JSON
        self.save_poll_data()

        await interaction.channel.send(f"{username} has voted! in poll #{self.poll_id}")

        if self.notification_channel:
            channel = interaction.guild.get_channel(self.notification_channel)
            if channel:
                await channel.send(f"📩 {username} has voted for option **{self.options[option_index]}** in poll #{self.poll_id}")


    async def end_poll(self, interaction: discord.Interaction):
        # Ensure only the poll creator can end the poll
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("You are not the creator of this poll and cannot end it!", ephemeral=True)
            return

        await interaction.response.send_message("Ending the poll now...")

        # Stop the poll immediately
        self.stop()

        # Process the poll results and display them
        result_embed = discord.Embed(title=f"📢 Poll Results #{self.poll_id}",
                                     description="The poll has ended! Here are the results:",
                                     color=discord.Color.green())

        vote_counts = [0] * len(self.options)
        votes_per_option = {i: [] for i in range(len(self.options))}  # Store who voted for each option
        for user_data in self.votes.values():
            vote_counts[user_data["vote"]] += 1
            votes_per_option[user_data["vote"]].append(user_data["username"])

        for i, (option, count) in enumerate(zip(self.options, vote_counts)):
            result_embed.add_field(name=f"{option}", value=f"Votes: {count}", inline=False)

        winning_index = vote_counts.index(max(vote_counts)) if vote_counts else None
        winning_option = self.options[winning_index] if winning_index is not None else "No winner"

        if winning_index is not None:
            result_embed.add_field(name="🏆 Winner", value=winning_option, inline=False)

        # Send detailed results of who voted for each option
        detailed_results = "### Detailed Votes:\n"
        for i, option in enumerate(self.options):
            detailed_results += f"\n**{option}:**\n"
            for username in votes_per_option[i]:
                detailed_results += f"- {username}\n"
        
        result_embed.add_field(name="📜 Voters per Option", value=detailed_results, inline=False)

        # Send the results in the same channel where the poll was created
        await interaction.channel.send(embed=result_embed)

        # Save the results to CSV
        os.makedirs("poll_results", exist_ok=True)
        with open("poll_results/all_polls.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # If the file is empty, write the header
            if f.tell() == 0:
                writer.writerow(["Poll ID", "Username", "Voted Option", "Winning Option"])
            for user_data in self.votes.values():
                writer.writerow([self.poll_id, user_data["username"], self.options[user_data["vote"]], winning_option])

        # Delete the JSON file after the poll ends
        os.remove(f"poll_results/poll_{self.poll_id}.json")

    def check_for_ongoing_polls(self):
        """Check for ongoing polls that need to be resumed."""
        for filename in os.listdir("poll_results"):
            if filename.endswith(".json"):
                poll_id = int(filename.split("_")[1].split(".")[0])  # Extract poll ID
                with open(f"poll_results/{filename}", "r", encoding="utf-8") as f:
                    poll_data = json.load(f)
                    # You can check if the poll has timed out and then end it or load it manually
                    # (e.g., check the poll's `end_time` and compare it with the current time)



class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_counter = self.get_last_poll_id()  # Get the last poll ID from the CSV or set to 0
        self.bot.loop.create_task(self.load_ongoing_polls())


    async def load_ongoing_polls(self):
        for filename in os.listdir("poll_results"):
            if filename.endswith(".json"):
                with open(f"poll_results/{filename}", "r", encoding="utf-8") as f:
                    data = json.load(f)

                end_time = datetime.fromisoformat(data["end_time"])
                remaining_time = (end_time - datetime.utcnow()).total_seconds()

                if remaining_time <= 0:
                    continue  # Poll already expired

                channel = self.bot.get_channel(data["channel_id"])
                if not channel:
                    continue

                try:
                    message = await channel.fetch_message(data["message_id"])
                except discord.NotFound:
                    continue

                view = PollView(
                    options=data["options"],
                    timeout=remaining_time,
                    poll_id=data["poll_id"],
                    notification_channel=None,
                    creator_id=data["creator_id"]
                )
                view.votes = {int(k): v for k, v in data["votes"].items()}
                view.save_poll_data()
                view.message_id = data["message_id"]
                view.channel_id = data["channel_id"]

                # Reattach the view
                print(f"[Poll] Restoring poll #{data['poll_id']} in channel {data['channel_id']}...")
                await message.edit(view=view)

    def get_last_poll_id(self):
        last_id_csv = 0
        last_id_json = 0

        # Check CSV for last used poll ID
        if os.path.exists("poll_results/all_polls.csv"):
            with open("poll_results/all_polls.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                rows = list(reader)
                if rows:
                    last_row = rows[-1]
                    if last_row:
                        try:
                            last_id_csv = int(last_row[0])
                        except ValueError:
                            pass

        # Check JSON files for max poll ID
        for filename in os.listdir("poll_results"):
            if filename.endswith(".json") and filename.startswith("poll_"):
                try:
                    poll_id = int(filename.split("_")[1].split(".")[0])
                    last_id_json = max(last_id_json, poll_id)
                except (ValueError, IndexError):
                    continue

        return max(last_id_csv, last_id_json)

    @commands.command(name="poll")
    async def create_poll(self, ctx, *, args):

        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
        # ✅ Role check
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return       
       
        parts = [p.strip() for p in args.split(',') if p.strip()]
        if len(parts) < 3:
            await ctx.send("Usage: !poll <duration in hours>, <option1>, <option2>, ...")
            return

        try:
            duration_hours = int(parts[0])
            options = parts[1:]
        except ValueError:
            await ctx.send("Invalid duration. It must be a number (hours).")
            return

        self.poll_counter += 1
        poll_id = self.poll_counter
        timeout = duration_hours * 3600

        end_time = datetime.utcnow() + timedelta(hours=duration_hours)
        timestamp = int(end_time.timestamp())

        embed = discord.Embed(title=f"📊 Verdict #{poll_id}",
                              description=f"Vote anonymously by clicking below\n**Poll ends <t:{timestamp}:R>**",
                              color=discord.Color.blue())

        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i + 1}", value=option, inline=False)

        # You can specify a channel ID here for vote notifications
        notification_channel = 123456789  # Replace with your actual channel ID
        view = PollView(options, timeout=timeout, poll_id=poll_id, notification_channel=notification_channel, creator_id=ctx.author.id)
        message = await ctx.send(embed=embed, view=view)
        view.message_id = message.id
        view.channel_id = ctx.channel.id
        view.save_poll_data()

        await asyncio.sleep(timeout)

        # Poll ended
        result_embed = discord.Embed(title=f"📢 Poll Results #{poll_id}",
                                     description="The poll has ended! Here are the results:",
                                     color=discord.Color.green())

        vote_counts = [0] * len(options)
        votes_per_option = {i: [] for i in range(len(options))}  # Store who voted for each option
        for user_data in view.votes.values():
            vote_counts[user_data["vote"]] += 1
            votes_per_option[user_data["vote"]].append(user_data["username"])

        for i, (option, count) in enumerate(zip(options, vote_counts)):
            result_embed.add_field(name=f"{option}", value=f"Votes: {count}", inline=False)

        winning_index = vote_counts.index(max(vote_counts)) if vote_counts else None
        winning_option = options[winning_index] if winning_index is not None else "No winner"

        if winning_index is not None:
            result_embed.add_field(name="🏆 Winner", value=winning_option, inline=False)

        # Send detailed results of who voted for each option
        detailed_results = "### Detailed Votes:\n"
        for i, option in enumerate(options):
            detailed_results += f"\n**{option}:**\n"
            for username in votes_per_option[i]:
                detailed_results += f"- {username}\n"
        
        result_embed.add_field(name="📜 Voters per Option", value=detailed_results, inline=False)

        await ctx.send(embed=result_embed)

        # Save to a single CSV file, appending the results
        os.makedirs("poll_results", exist_ok=True)
        with open("poll_results/all_polls.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # If the file is empty, write the header
            if f.tell() == 0:
                writer.writerow(["Poll ID", "Username", "Voted Option", "Winning Option"])
            for user_data in view.votes.values():
                writer.writerow([poll_id, user_data["username"], options[user_data["vote"]], winning_option])

    @commands.command(name="pollCorrection")
    async def poll_correction(self, ctx, poll_number: int, correct_answer: str):
        """Correct the winning answer for a specific poll by updating the CSV file."""
        
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
        # Role check
        allowed_roles = ["Admin", "Steward", "FIA Comissioner"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return        
        
        # Check if the poll number exists in the CSV
        if not os.path.exists("poll_results/all_polls.csv"):
            await ctx.send("No polls found to correct.")
            return

        # Read the CSV file and load the data
        with open("poll_results/all_polls.csv", "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))

        # Check if the CSV file is empty or doesn't contain any polls
        if len(reader) <= 1:
            await ctx.send("No poll data available to correct.")
            return

        # Find and modify rows corresponding to the specified poll number
        poll_found = False
        for i, row in enumerate(reader):
            if i == 0:  # Skip the header row
                continue
            poll_id = int(row[0])
            if poll_id == poll_number:
                # MODIFY the existing winning option (4th column) instead of appending
                if len(row) >= 4:  # Ensure row has enough columns
                    row[3] = correct_answer  # Change the winning option
                    poll_found = True

        if not poll_found:
            await ctx.send(f"Poll number {poll_number} not found.")
            return

        # Rewrite the CSV file with the updated data
        with open("poll_results/all_polls.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(reader)

        await ctx.send(f"Winning option for poll #{poll_number} has been updated to '{correct_answer}'.")

    @commands.command(name="getPollLogs")
    async def get_poll_logs(self, ctx):
        """Send the poll logs CSV file."""
        poll_logs_file = "poll_results/all_polls.csv"
        
        if os.path.exists(poll_logs_file):
            await ctx.send(file=discord.File(poll_logs_file))
        else:
            await ctx.send("Poll logs file not found.")

def setup(bot):
    bot.add_cog(Poll(bot))
    cog = Poll(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.load_ongoing_polls())
