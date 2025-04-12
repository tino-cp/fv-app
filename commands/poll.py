import discord
from discord.ext import commands
from discord.ui import View, Button
import csv
import os
import asyncio
from datetime import datetime, timedelta

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

        for idx, option in enumerate(options):
            button = Button(label=option, custom_id=f"poll_{poll_id}_{idx}", style=discord.ButtonStyle.primary)
            button.callback = self.vote
            self.add_item(button)

        # Add the End Poll button (red)
        end_poll_button = Button(label="End Poll", custom_id=f"end_poll_{poll_id}", style=discord.ButtonStyle.danger)
        end_poll_button.callback = self.end_poll
        self.add_item(end_poll_button)

    async def vote(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name  # Get the username
        option_index = int(interaction.data['custom_id'].split('_')[-1])

        if user_id in self.votes:
            # If the user already voted, update their vote
            previous_option = self.votes[user_id]["vote"]
            if previous_option == option_index:
                await interaction.response.send_message("You already voted for this option!", ephemeral=True)
                return
            else:
                # Update the vote to the new option
                self.votes[user_id] = {"username": username, "vote": option_index}
                await interaction.response.send_message(f"Your vote has been changed to **{self.options[option_index]}**!", ephemeral=True)
        else:
            # First-time vote
            self.votes[user_id] = {"username": username, "vote": option_index}
            await interaction.response.send_message(f"Your vote has been recorded anonymously! You voted for **{self.options[option_index]}**.", ephemeral=True)

        # Send a message saying "<Name> has voted" in the same channel
        await interaction.channel.send(f"{username} has voted! in poll #{self.poll_id}")

        # Send notification to the specified channel
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

        # Save to a single CSV file, appending the results
        os.makedirs("poll_results", exist_ok=True)
        with open("poll_results/all_polls.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # If the file is empty, write the header
            if f.tell() == 0:
                writer.writerow(["Poll ID", "Username", "Voted Option", "Winning Option"])
            for user_data in self.votes.values():
                writer.writerow([self.poll_id, user_data["username"], self.options[user_data["vote"]], winning_option])


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_counter = self.get_last_poll_id()  # Get the last poll ID from the CSV or set to 0

    def get_last_poll_id(self):
        # Check if the CSV exists and read the last poll ID
        if os.path.exists("poll_results/all_polls.csv"):
            with open("poll_results/all_polls.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header
                last_row = list(reader)[-1]  # Get the last row
                if last_row:
                    return int(last_row[0])  # Return the last poll ID
        return 0  # If no CSV or no polls, start with 0

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
        
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
        # ✅ Role check
        allowed_roles = ["Admin", "Steward", "FIA Comissioner"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return        
        
        """Correct the correct answer for a specific poll by updating the CSV file."""
        
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
                row.append(correct_answer)  # Add the new 'correct answer' to the row
                poll_found = True

        if not poll_found:
            await ctx.send(f"Poll number {poll_number} not found.")
            return

        # Rewrite the CSV file with the updated data
        with open("poll_results/all_polls.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            # Add the new header with 'Correct Answer' column
            if reader[0][0] != "Poll ID":
                reader[0].append("Correct Answer")  # Add new column header if not already there
            writer.writerows(reader)

        await ctx.send(f"Correct answer for poll #{poll_number} has been updated to '{correct_answer}'.")

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
