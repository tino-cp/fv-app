import discord
from discord.ext import commands
import os

# Get server IDs as a set of integers
ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)

class GetLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="getLogs")
    async def get_logs(self, ctx):
        # ✅ Role check
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return

        log_file_path = "penalty_log.csv"

        if not os.path.exists(log_file_path):
            await ctx.send("❌ Log file not found.")
            return

        try:
            await ctx.send(file=discord.File(log_file_path))
        except Exception as e:
            await ctx.send(f"❌ Failed to send file: {e}")

    @commands.command(name="clearLogs")
    async def clear_logs(self, ctx):

        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return    
        
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return

        log_file_path = "penalty_log.csv"

        if not os.path.exists(log_file_path):
            await ctx.send("❌ Log file not found.")
            return

        try:
            open(log_file_path, "w").close()  # Clears the contents of the file
            await ctx.send("🧹 Penalty log has been cleared.")
        except Exception as e:
            await ctx.send(f"❌ Failed to clear log file: {e}")

    @commands.command(name="filterLogs")
    async def filter_logs(self, ctx):
        
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return    
        
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return

        log_file_path = "penalty_log.csv"

        if not os.path.exists(log_file_path):
            await ctx.send("❌ Log file not found.")
            return

        try:
            with open(log_file_path, "r") as file:
                lines = file.readlines()

            # Parse logs and filter out duplicates, keeping only the latest penalty for each league/thread counter
            filtered_logs = {}
            for line in lines:
                parts = line.strip().split(",")
                league_counter = (parts[0], parts[1])  # Tuple (League, Counter)
                penalty = ",".join(parts[2:])

                if league_counter not in filtered_logs:
                    filtered_logs[league_counter] = penalty
                else:
                    # If a penalty for the same league and counter exists, replace it (i.e., keep the most recent one)
                    filtered_logs[league_counter] = penalty

            # Sort the filtered logs by League (F3 > F2 > F1) and then by thread counter
            sorted_logs = sorted(filtered_logs.items(), key=lambda x: (x[0][0], int(x[0][1])))

            # Write the sorted logs back into the CSV file
            with open(log_file_path, "w") as file:
                for league_counter, penalty in sorted_logs:
                    file.write(f"{league_counter[0]},{league_counter[1]},{penalty}\n")

            await ctx.send("✅ Logs have been filtered and sorted.")
        except Exception as e:
            await ctx.send(f"❌ Failed to filter and sort logs: {e}")

async def setup(bot):
    await bot.add_cog(GetLogs(bot))
