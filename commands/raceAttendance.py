import discord
from discord.ext import commands
from discord.ui import Button, View

# The dictionary of teams and the corresponding emoji for each (add more as needed)

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
# This will store the user reactions by team (in memory, could be a database if you need persistence)
team_drivers_f1 = {team: [] for team in TEAMS_F1}
team_drivers_f2 = {team: [] for team in TEAMS_F2}
last_message_f1 = None  # To store the last F1 race attendance message
last_message_f2 = None  # To store the last F2 race attendance message

class RaceAttendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="RAF1")
    async def race_attendance_f1(self, ctx):
        global last_message_f1  # Access the global variable for the last F1 message

        # If there was a previous attendance message, delete it
        if last_message_f1:
            await last_message_f1.delete()

        # Create a view with buttons for each team
        view = View()
        for team, emoji in TEAMS_F1.items():
            button = Button(style=discord.ButtonStyle.primary, label=team, emoji=emoji, custom_id=f"F1_{team}")
            button.callback = self.button_callback
            view.add_item(button)

        # Create the embed message
        embed = discord.Embed(
            title="Race Attendance F1",
            description="Click the button to confirm your participation in the race.",
            color=discord.Color.green()
        )

        # Add the team fields to the embed (inline)
        for team, emoji in TEAMS_F1.items():
            driver_list = "\n".join(team_drivers_f1[team]) if team_drivers_f1[team] else "No drivers yet"
            embed.add_field(name=f"{team} {emoji}", value=f"```{driver_list}```", inline=True)

        # Send the message with the buttons and store it as the last message
        message = await ctx.send(embed=embed, view=view)
        last_message_f1 = message

    @commands.command(name="RAF2")
    async def race_attendance_f2(self, ctx):
        global last_message_f2  # Access the global variable for the last F2 message

        # If there was a previous attendance message, delete it
        if last_message_f2:
            await last_message_f2.delete()

        # Create a view with buttons for each team
        view = View()
        for team, emoji in TEAMS_F2.items():
            button = Button(style=discord.ButtonStyle.primary, label=team, emoji=emoji, custom_id=f"F2_{team}")
            button.callback = self.button_callback
            view.add_item(button)

        # Create the embed message
        embed = discord.Embed(
            title="Race Attendance F2",
            description="Click the button to confirm your participation in the race.",
            color=discord.Color.blue()
        )

        # Add the team fields to the embed (inline)
        for team, emoji in TEAMS_F2.items():
            driver_list = "\n".join(team_drivers_f2[team]) if team_drivers_f2[team] else "No drivers yet"
            embed.add_field(name=f"{team} {emoji}", value=f"```{driver_list}```", inline=True)

        # Send the message with the buttons and store it as the last message
        message = await ctx.send(embed=embed, view=view)
        last_message_f2 = message

    async def button_callback(self, interaction: discord.Interaction):
        user = interaction.user
        custom_id = interaction.data["custom_id"]
        category, team = custom_id.split("_", 1)  # Split into F1/F2 and team name

        # Determine which team list to update
        if category == "F1":
            team_drivers = team_drivers_f1
        elif category == "F2":
            team_drivers = team_drivers_f2
        else:
            return  # Invalid category

        # Get the user's nickname (or username if no nickname is set)
        nickname = user.nick or user.name

        # Toggle user participation
        if nickname in team_drivers[team]:
            team_drivers[team].remove(nickname)
            print(f"Driver {nickname} removed from {team} ({category})")
        else:
            team_drivers[team].append(nickname)
            print(f"Driver {nickname} added to {team} ({category})")

        # Update the message to show the new drivers
        await self.update_race_attendance_message(interaction.message, category)
        await interaction.response.defer()

    async def update_race_attendance_message(self, message, category):
        # Determine which team list and teams to use
        if category == "F1":
            teams = TEAMS_F1
            team_drivers = team_drivers_f1
            title = "Race Attendance F1"
            color = discord.Color.green()
        elif category == "F2":
            teams = TEAMS_F2
            team_drivers = team_drivers_f2
            title = "Race Attendance F2"
            color = discord.Color.blue()
        else:
            return  # Invalid category

        # Create a new embed
        embed = discord.Embed(
            title=title,
            description="Click the button to confirm your participation in the race.",
            color=color
        )

        # Clear existing fields and add updated team fields to the embed (inline)
        for team, emoji in teams.items():
            driver_list = " ".join(team_drivers[team]) if team_drivers[team] else "No drivers yet"
            embed.add_field(name=f"{team} {emoji}", value=f"```{driver_list}```", inline=True)

        # Update the message with the new embed
        await message.edit(embed=embed)

def setup(bot):
    bot.add_cog(RaceAttendance(bot))