import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import json
import os

# The dictionary of teams and the corresponding emoji for each (add more as needed)
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
    "Spectator": "👀",
    "Reserve drivers": "<:reserve:1335001794719518830>"
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
    "VAR": "<:var:1275285966894010419>",
    "FIA Official": "<:fia:927351199387234386>",
    "Spectator": "👀",
    "Reserve drivers": "<:reserve:1335001794719518830>"
}

class RaceAttendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refresh_views.start()
        self.attendance_files = {"F1": "attendance_f1.json", "F2": "attendance_f2.json"}

    def load_attendance(self, category):
        if os.path.exists(self.attendance_files[category]):
            with open(self.attendance_files[category], 'r') as f:
                return json.load(f)
        return {}

    def save_attendance(self, category, data):
        with open(self.attendance_files[category], 'w') as f:
            json.dump(data, f, indent=4)

    @commands.command(name="RAF1")
    async def race_attendance_f1(self, ctx):
        self.save_attendance("F1", {})
        await self.send_attendance_message(ctx, "F1")

    @commands.command(name="RAF2")
    async def race_attendance_f2(self, ctx):
        self.save_attendance("F2", {})
        await self.send_attendance_message(ctx, "F2")

    async def send_attendance_message(self, ctx, category):
        message = await self.create_attendance_message(ctx, category)
        return message

    async def create_attendance_message(self, ctx, category):
        view = self.create_view(category)
        embed = self.create_embed(category, ctx.guild)
        message = await ctx.send(embed=embed, view=view)
        return message

    def create_embed(self, category, guild=None):
        teams = TEAMS_F1 if category == "F1" else TEAMS_F2
        attendance_data = self.load_attendance(category)
        embed = discord.Embed(
            title=f"Race Attendance {category}",
            description='Click the button to confirm your participation.',
            color=discord.Color.green() if category == "F1" else discord.Color.yellow()
        )
        for team, emoji in teams.items():
            driver_list = self.get_driver_list(attendance_data.get(team, {}), guild)
            embed.add_field(name=f"{team} {emoji}", value=f"```{driver_list}```", inline=True)
        return embed

    def get_driver_list(self, drivers, guild):
        if not drivers:
            return "No drivers yet"
        return " | ".join(drivers.values())

    async def button_callback(self, interaction: discord.Interaction):
        user = interaction.user
        custom_id = interaction.data["custom_id"]
        category, team = custom_id.split("_", 1)

        attendance_data = self.load_attendance(category)
        if team == "Leave":
            for team_name in attendance_data:
                if str(user.id) in attendance_data[team_name]:
                    del attendance_data[team_name][str(user.id)]
                    if not attendance_data[team_name]:
                        attendance_data[team_name] = {}
            self.save_attendance(category, attendance_data)
        else:
            for team_name in attendance_data:
                if str(user.id) in attendance_data[team_name]:
                    del attendance_data[team_name][str(user.id)]
                    if not attendance_data[team_name]:
                        attendance_data[team_name] = {}
            attendance_data.setdefault(team, {})[str(user.id)] = user.display_name
            self.save_attendance(category, attendance_data)

        await self.update_race_attendance_message(interaction.message, category)
        await interaction.response.defer()

    async def update_race_attendance_message(self, message, category):
        guild = message.guild
        embed = self.create_embed(category, guild)
        view = self.create_view(category)
        await message.edit(embed=embed, view=view)

    @tasks.loop(minutes=14)
    async def refresh_views(self):
        pass

    @refresh_views.before_loop
    async def before_refresh_views(self):
        await self.bot.wait_until_ready()

    def create_view(self, category):
        view = View()
        teams = TEAMS_F1 if category == "F1" else TEAMS_F2
        for team in teams:
            button = Button(label=team, style=discord.ButtonStyle.primary, custom_id=f"{category}_{team}")
            button.callback = self.button_callback
            view.add_item(button)
        leave_button = Button(label="Leave", style=discord.ButtonStyle.danger, custom_id=f"{category}_Leave")
        leave_button.callback = self.button_callback
        view.add_item(leave_button)
        return view


def setup(bot):
    bot.add_cog(RaceAttendance(bot))