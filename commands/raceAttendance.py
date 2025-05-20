import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import json
import os

# Get server IDs as a set of integers
ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)


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
    "FIA Race director": "<:fia:927351199387234386>",
    "FIA Safety car": "<:fia:927351199387234386>",
    "Not attending": "❌",
    "Dont know yet": "❓",
    "Spectator": "👀",
    "Media": "🔴",
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
    "AIX": "<:aix:1275285913685065759>",
    "Trident": "<:Trident:1272194719778213889>",
    "VAR": "<:var:1275285966894010419>",
    "FIA Race director": "<:fia:927351199387234386>",
    "FIA safety car": "<:fia:927351199387234386>",
    "Not attending": "❌",
    "Dont know yet": "❓",
    "Spectator": "👀",
    "Media": "🔴",
    "Reserve drivers": "<:reserve:1335001794719518830>"
}

TEAMS_F3 = {
    "Invicta": "<:invicta:1275285922266742926>",
    "MP": "<:mp:1275285923785080946>",
    "Hitech": "<:hitech:1275285920639221807>",
    "Campos": "<:campos:1275285917187178539>",
    "PREMA": "<:prema:1275285925206818836>",
    "DAMS": "<:dams:1275285918743265362>",
    "ART": "<:ART:1275285915366985788>",
    "AIX": "<:aix:1275285913685065759>",
    "Trident": "<:Trident:1272194719778213889>",
    "VAR": "<:var:1275285966894010419>",
    "FIA Race director": "<:fia:927351199387234386>",
    "FIA safety car": "<:fia:927351199387234386>",
    "Not attending": "❌",
    "Dont know yet": "❓",
    "Spectator": "👀",
    "Media": "🔴",
    "Reserve drivers": "<:reserve:1335001794719518830>"
    
}

TEAMS_HYPERCAR = {
    "Ferrari AF Corse": "<:fer:1233936232409468958>",
    "BMW Team WRT": "<:bmw_wrt:1373353457553113238>",
    "Alpine Endurance": "<:alp:844275251440910387>",
    "Toyota Gazoo Racing": "<:toyota:1373353454419972107>",
    "Porsche Penske": "<:porsche:1373353763473199208>",
    "Cadillac Hertz Team Jota": "<:cadillac:1373353449705570364>",
    "Aston Martin": "<:ast:1274844727757246586>",
    "Reserve drivers": "<:reserve:1335001794719518830>"
}

TEAMS_LMGT3 = {
    "Vista AF Corse": "<:af_corse1:1373353447163957418>",
    "Team WRT": "<:wrt:1373353443770634412>",
    "McLaren United Autosports": "<:mcl:980541416591724644>",
    "TF Sport Corvette": "<:corvette:1373353736079937586>",
    "Manthey Porsche": "<:manthey:1373353439739773030>",
    "Mercedes Iron Lynx": "<:merc:844262871071195147>",
    "Ford Proton Competition": "<:ford:1373353437403676762>",
    "Reserve drivers": "<:reserve:1335001794719518830>"
}

category_colors = {
    "HYPERCAR": 0xdf2115,  
    "LMGT3": 0x01814f,     
    "F1": 0xff0202,  
    "F2": 0x0000ff,  
    "F3": 0x8c8c8c  
}

class RaceAttendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refresh_views.start()
        self.attendance_files = {
    "F1": "attendance_f1.json",
    "F2": "attendance_f2.json",
    "F3": "attendance_f3.json",
    "HYPERCAR": "attendance_hypercar.json",
    "LMGT3": "attendance_lmgt3.json"
}


    def load_attendance(self, category):
        if os.path.exists(self.attendance_files[category]):
            with open(self.attendance_files[category], 'r') as f:
                return json.load(f)
        return {}

    def save_attendance(self, category, data):
        with open(self.attendance_files[category], 'w') as f:
            json.dump(data, f, indent=4)

    @commands.command(name="RA")    
    async def race_attendance(self, ctx, *, track_name: str):
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        
    # ✅ Role check
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return        
        
        """Handles race attendance for both F1 and F2 with the track name."""
        
        # Send first title message for F1
        emoji_f1 = "<:FV1:1070246742693531688>"
        await ctx.send(f"# {emoji_f1} {track_name} {emoji_f1}")
        
        # Call the RAF1 command
        await self.race_attendance_f1(ctx)
        
        # Send second title message for F2
        emoji_f2 = "<:FV2:1070247024588492901>"
        await ctx.send(f"# {emoji_f2} {track_name} {emoji_f2}")
        
        # Call the RAF2 command
        await self.race_attendance_f2(ctx)

        # F3 Section
        emoji_f3 = "<:FV3:1070247353916870668>"  # Replace with your F3 emoji
        await ctx.send(f"# {emoji_f3} {track_name} {emoji_f3}")
        
        # Call the RAF3 command
        await self.race_attendance_f3(ctx)

    @commands.command(name="RAF1")
    async def race_attendance_f1(self, ctx):
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return     
            
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return        
        self.save_attendance("F1", {})
        await self.send_attendance_message(ctx, "F1")

    @commands.command(name="RAF2")
    async def race_attendance_f2(self, ctx):

        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return     
                
        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        self.save_attendance("F2", {})
        await self.send_attendance_message(ctx, "F2")

    @commands.command(name="RAF3")
    async def race_attendance_f3(self, ctx):

        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return     

        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return    
        self.save_attendance("F3", {})
        await self.send_attendance_message(ctx, "F3")

    @commands.command(name="RAFVEC")
    async def race_attendance_fvec(self, ctx):
        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return

        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return

        emoji_hypercar = "<:hypercar:1368181951420432514>"
        await ctx.send(f"# {emoji_hypercar} HyperCar Attendance {emoji_hypercar}")

        self.save_attendance("HYPERCAR", {})
        await self.send_attendance_message(ctx, "HYPERCAR")

        emoji_lmgt3 = "<:lmgt3:1368181949516222494>"
        await ctx.send(f"# {emoji_lmgt3} LMGT3 Attendance {emoji_lmgt3}")

        self.save_attendance("LMGT3", {})
        await self.send_attendance_message(ctx, "LMGT3")

    @commands.command(name="reset")
    async def reset_attendance(self, ctx, category: str):

        allowed_roles = ["Admin", "Steward"]
        user_roles = [role.name for role in ctx.author.roles]

        if not any(role in user_roles for role in allowed_roles):
            await ctx.send("🚫 You do not have permission to use this command.")
            return     

        if ctx.guild.id not in ALLOWED_SERVER_IDS:
            await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
            return
        """Resets the attendance for the given category (F1 or F2)."""
        if category not in ["F1", "F2", "F3"]:
            await ctx.send("Invalid category! Use `F1`, `F2`, or `F3`.")
            return
        
        # Clear the attendance file
        self.save_attendance(category, {})

        # Try to reload and update the existing attendance message
        try:
            with open(f"attendance_{category}_message.json", "r") as f:
                data = json.load(f)
                channel = self.bot.get_channel(data["channel_id"])
                if channel:
                    message = await channel.fetch_message(data["message_id"])
                    await self.update_race_attendance_message(message, category)
                    await ctx.send(f"Attendance for {category} has been reset.")
                    return
        except (FileNotFoundError, discord.NotFound):
            await ctx.send(f"No saved attendance message found for {category}.")

    async def send_attendance_message(self, ctx, category):
        message = await self.create_attendance_message(ctx, category)
        with open(f"attendance_{category}_message.json", "w") as f:
            json.dump({"message_id": message.id, "channel_id": ctx.channel.id}, f, indent=4)
        return message

    async def create_attendance_message(self, ctx, category):
        view = self.create_view(category)
        embed = self.create_embed(category, ctx.guild)
        message = await ctx.send(embed=embed, view=view)
        return message

    def create_embed(self, category, guild=None):
        if category == "F1":
            teams = TEAMS_F1
        elif category == "F2":
            teams = TEAMS_F2
        elif category == "F3":
            teams = TEAMS_F3
        elif category == "HYPERCAR":
            teams = TEAMS_HYPERCAR
        elif category == "LMGT3":
            teams = TEAMS_LMGT3
        else:
            teams = {}

        attendance_data = self.load_attendance(category)
        color = category_colors.get(category, discord.Color.default())

        embed = discord.Embed(
            title=f"Race Attendance {category}",
            description='Click the button to confirm your participation.',
            color=color
        )
        for team, emoji in teams.items():
                driver_list = self.get_driver_list(attendance_data.get(team, {}), guild)
                embed.add_field(name=f"{emoji} {team}", value=driver_list or "No response yet", inline=True)
        return embed

    def get_driver_list(self, drivers, guild):
        if not drivers:
            return "-"
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

    @tasks.loop(minutes=2)
    async def refresh_views(self):
        await self.bot.wait_until_ready()
        for category in ["F1", "F2", "F3", "HYPERCAR", "LMGT3"]:
            try:
                with open(f"attendance_{category}_message.json", "r") as f:
                    data = json.load(f)
                    channel = self.bot.get_channel(data["channel_id"])
                    if channel:
                        message = await channel.fetch_message(data["message_id"])
                        await self.update_race_attendance_message(message, category)
            except (FileNotFoundError, discord.NotFound):
                print(f"No saved attendance message for {category} or message was deleted.")

    @refresh_views.before_loop
    async def before_refresh_views(self):
        await self.bot.wait_until_ready()

    def create_view(self, category):
        view = View(timeout=None)  # Prevent view from expiring
        if category == "F1":
            teams = TEAMS_F1
        elif category == "F2":
            teams = TEAMS_F2
        elif category == "F3":
            teams = TEAMS_F3
        elif category == "HYPERCAR":
            teams = TEAMS_HYPERCAR
        elif category == "LMGT3":
            teams = TEAMS_LMGT3
        else:
            teams = {}
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