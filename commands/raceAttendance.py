import discord
from discord.ext import commands

# ATTENDANCE BOT COMMAND

attendance_data = {}


TEAMS_F1 = {
    "Aston Martin": "🟢",
    "Alpha Tauri": "🔵",
    "Alfa Romeo": "🔴",
    "Alpine": "🟠",
    "Ferrari": "🔴",
    "Haas": "⚫",
    "McLaren": "🟠",
    "Mercedes": "⚪",
    "RedBull": "🔵",
    "Williams": "🔵",
    "FIA Official": "🟡",
    "Spectator": "👀"
}

TEAMS_F2 = {
    "Invicta": "🟢",
    "MP": "🔵",
    "Hitech": "🔴",
    "Campos": "🟠",
    "PREMA": "🔴",
    "DAMS": "⚫",
    "ART": "🟠",
    "Rodin": "⚪",
    "AIX": "🔵",
    "Trident": "🔵",
    "VaR": "⭕",
    "FIA Official": "🟡",
    "Spectator": "👀"
}
'''

TEAMS_F1 = {
    "Aston Martin": "<:ast:1274844727757246586>",
    "RCB": "<:rcb:1234603336162869320>",
    "Sauber": "<:sau:1234528088222597131>",
    "Alpine": "<:alp:844275251440910387>",
    "Ferrari": "<:fer:1233936232409468958>",
    "Haas": "<:haas:1039894365994221568>",
    "McLaren": "<:mcl:980541416591724644>",
    "Mercedes": "<:merc:844262871071195147>",
    "RedBull": "<:red:1275285685431177289>",
    "Williams": "<:wlms:844277423914745906>",
    "FIA Official": "<:fia:927351199387234386>",
    "Spectator": "👀"
}

TEAMS_F2 = {
    "Invicta": "<:invicta:1275285922266742926>",
    "MP": "<:mp:1275285923785080946>",
    "Hitech": "<:hitech:1275285920639221807>",
    "Campos": "<:campos:1275285917187178539>",
    "PREMA": "<:prema:1275285925206818836>",
    "DAMS": "<:dams:1275285918743265362>",
    "ART": "<:ART:1275285915366985788>",
    "Rodin": "<:rodin:1275285926792400926>",
    "AIX": "<:aix:1275285913685065759>",
    "Trident": "<:Trident:1272194719778213889>",
    "VaR": "<:var:1275285966894010419>",
    "FIA Official": "<:fia:927351199387234386>",
    "Spectator": "👀"
}
'''
# Global variable to store the previous attendance message ID
previous_attendance_message_id = None

class RaceAttendanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="RAF1")
    async def race_attendance_f1(self, ctx):
        """
        Sends a message for F1 race attendance.
        """
        await send_race_attendance(ctx, TEAMS_F1, "Formula 1")

    @commands.command(name="RAF2")
    async def race_attendance_f2(self, ctx):
        """
        Sends a message for F2 race attendance.
        """
        await send_race_attendance(ctx, TEAMS_F2, "Formula 2")

@commands.Cog.listener()
async def on_raw_reaction_remove(self, payload):
    if payload.user_id == self.bot.user.id:
        return  # Ignore bot's own reactions

    guild = self.bot.get_guild(payload.guild_id)
    user = None

    if guild:
        user = guild.get_member(payload.user_id)

    # Fallback in case the user is not cached (large server issue)
    if user is None:
        try:
            user = await self.bot.fetch_user(payload.user_id)
        except discord.NotFound:
            print(f"User {payload.user_id} not found.")
            return
        except discord.HTTPException as e:
            print(f"Failed to fetch user {payload.user_id}: {e}")
            return

    if payload.message_id not in attendance_data:
        return

    event_type = attendance_data[payload.message_id]["event_type"]
    teams = TEAMS_F1 if event_type == "Formula 1" else TEAMS_F2

    for team, emoji in teams.items():
        if str(payload.emoji.name) == emoji:
            user_name = user.name  # Use `.name` instead of `.display_name` for consistency
            if user_name in attendance_data[payload.message_id]["teams"][team]:
                attendance_data[payload.message_id]["teams"][team].remove(user_name)
            break  # Exit loop early if we find a match

    # Fetch the channel and message, handle permission errors
    channel = self.bot.get_channel(payload.channel_id)
    if channel:
        try:
            message = await channel.fetch_message(payload.message_id)
            await update_attendance_message(message, teams)
        except discord.NotFound:
            print(f"Message {payload.message_id} not found.")
        except discord.Forbidden:
            print("Bot does not have permission to fetch messages.")
        except discord.HTTPException as e:
            print(f"Failed to fetch message {payload.message_id}: {e}")


async def send_race_attendance(ctx, teams, event_type):
    """
    Sends a message for race attendance and handles reactions.
    Deletes the previous attendance message if it exists.
    """
    global previous_attendance_message_id

    # Delete the previous attendance message if it exists
    if previous_attendance_message_id:
        try:
            previous_message = await ctx.channel.fetch_message(previous_attendance_message_id)
            await previous_message.delete()
        except discord.NotFound:
            print("Previous attendance message not found. It may have been deleted manually.")
        except discord.Forbidden:
            print("Bot does not have permission to delete the previous message.")
        except Exception as e:
            print(f"Error deleting previous message: {e}")

    # Create the initial attendance message
    message_content = f"**{event_type} Race Check-in**\n\n"
    message_content += "Please react with the emoji corresponding to your team:\n\n"

    # Send the message
    message = await ctx.send(message_content)

    # Add reactions for each team
    for emoji in teams.values():
        await message.add_reaction(emoji)

    # Store the message ID, initialize attendance data, and store the event type
    attendance_data[message.id] = {
        "teams": {team: [] for team in teams},
        "event_type": event_type
    }

    # Update the message to show the table format immediately
    await update_attendance_message(message, teams)

    # Update the global variable with the new message ID
    previous_attendance_message_id = message.id

async def update_attendance_message(message, teams):
    """
    Updates the attendance message with the latest data in an embed format.
    """
    data = attendance_data[message.id]

    # Create the embed
    embed = discord.Embed(
        title=f"{data['event_type']} Race Check-in",
        description="Please react with the emoji corresponding to your team:",
        color=discord.Color.blue()  # You can change the color as needed
    )

    # Add each team and its drivers to the embed
    for team, emoji in teams.items():
        drivers = ", ".join(data["teams"][team]) if data["teams"][team] else "No drivers yet"
        embed.add_field(
            name=f"{emoji} {team}",
            value=drivers,
            inline=False  # Set to True if you want fields to appear side by side
        )

    # Edit the message with the updated embed
    await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(RaceAttendanceCog(bot))