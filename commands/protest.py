import discord
from discord.ext import commands
import json
import os
from datetime import datetime

ALLOWED_SERVER_IDS = set(
    int(id.strip()) for id in os.getenv("ALLOWED_SERVER_IDS", "").split(",") if id.strip()
)

PROTESTS_FILE = "protests.json"
MAX_PROTESTS = 3

F2_F3_TEAMS = {"ART", "CAM", "DAM", "HIT", "MP", "PRE", "TRI", "VAR", "AIX", "ROD", "INV"}
F1_TEAMS = {"ALP", "AST", "FER", "HAA", "MCL", "MER", "RCB", "RED", "SAU", "WIL"}
ALLOWED_TEAMS = F1_TEAMS.union(F2_F3_TEAMS)


def load_protests():
    if os.path.exists(PROTESTS_FILE):
        with open(PROTESTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_protests(data):
    with open(PROTESTS_FILE, "w") as f:
        json.dump(data, f, indent=4)


class ProtestView(discord.ui.View):
    def __init__(self, ctx, team):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.team = team

    @discord.ui.button(label="F2", style=discord.ButtonStyle.green)
    async def f2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.log_protest(interaction, "F2")

    @discord.ui.button(label="F3", style=discord.ButtonStyle.blurple)
    async def f3_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.log_protest(interaction, "F3")

    async def log_protest(self, interaction, division):
        team_key = f"{division}-{self.team}"
        protests = load_protests()

        if team_key not in protests:
            protests[team_key] = []

        if len(protests[team_key]) >= MAX_PROTESTS:
            await interaction.response.send_message(
                f"⚠️ {team_key} has already used all {MAX_PROTESTS} protest points.",
                ephemeral=True
            )
            return

        protest_entry = {
            "user": self.ctx.author.name,
            "user_id": self.ctx.author.id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        protests[team_key].append(protest_entry)
        save_protests(protests)

        embed = discord.Embed(
            title="📣 Protest Submitted",
            description=(
                f"✅ **{team_key} has submitted a protest.**\n\n"
                f"👉 **[🟨 CLICK HERE TO CREATE A TICKET 🟨](https://discord.com/channels/843175947304960020/982599539414413332/1003349125699477574)**\n\n"
                f"Please provide all evidence and context in the ticket channel for stewards to review."
            ),
            color=discord.Color.gold()
        )

        await interaction.response.edit_message(embed=embed, view=None)

        if isinstance(self.ctx.channel, discord.Thread):
            import re
            match = re.match(r"(?:✅\s*)?([A-Z0-9]+)\s+(\d+)\)", self.ctx.channel.name)
            if match:
                league = match.group(1)
                counter = match.group(2)
                new_name = f"{league} {counter}) PROTEST ONGOING"
                try:
                    await self.ctx.channel.edit(name=new_name)
                except discord.errors.HTTPException:
                    await self.ctx.send("⚠️ Could not rename the thread due to rate limits or permissions.")


@commands.command(name="protest", help="Submit a protest for a team.")
async def protest_command(ctx, team: str):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return

    allowed_roles = {"Academy CEO", "F2 Team Principal", "F3 Team Principal", "Academy Manager"}
    user_roles = {role.name for role in ctx.author.roles}

    if not allowed_roles.intersection(user_roles):
        embed = discord.Embed(
            description="❌ You do not have permission to use this command. Only Academy Manager, F2 Team Principal and F3 Team Principal can submit protests.\n\n Ping and ask your manager to open a protest for you.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    team = team.upper()

    if team not in ALLOWED_TEAMS:
        embed = discord.Embed(
            description=f"❌ Invalid team name! Allowed teams: {', '.join(ALLOWED_TEAMS)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # F1 teams are logged directly
    if team in F1_TEAMS:
        protests = load_protests()

        if team not in protests:
            protests[team] = []

        if len(protests[team]) >= MAX_PROTESTS:
            embed = discord.Embed(
                description=f"⚠️ {team} has already used all {MAX_PROTESTS} protest points.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        protest_entry = {
            "user": ctx.author.name,
            "user_id": ctx.author.id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        protests[team].append(protest_entry)
        save_protests(protests)

        embed = discord.Embed(
            title="📣 Protest Submitted",
            description=(
                f"✅ **{team} has submitted a protest.**\n\n"
                f"👉 **[🟨 CLICK HERE TO CREATE A TICKET 🟨](https://discord.com/channels/843175947304960020/982599539414413332/1003349125699477574)**\n\n"
                f"Please provide all evidence and context in the ticket channel for stewards to review."
            ),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    else:
        # For F2/F3, ask division via button
        embed = discord.Embed(
            title="Select Division",
            description=f"🔍 You are protesting for `{team}`.\n\nPlease select whether this team is in **F2** or **F3**.",
            color=discord.Color.blue()
        )
        view = ProtestView(ctx, team)
        await ctx.send(embed=embed, view=view)


@commands.command(name="revertProtest", help="Revert the last protest for a team (Head Stewards only).")
async def revert_protest_command(ctx, team: str):
    if ctx.guild.id not in ALLOWED_SERVER_IDS:
        await ctx.send("❌ This command is only allowed on the Formula V or test servers.")
        return

    allowed_roles = {"Admin", "Owner", "Steward"}
    user_roles = {role.name for role in ctx.author.roles}

    if not allowed_roles.intersection(user_roles):
        embed = discord.Embed(
            description="❌ Only Head Stewards or Admins can revert protests.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    team = team.upper()

    possible_keys = [team]
    if team in F2_F3_TEAMS:
        possible_keys = [f"F2-{team}", f"F3-{team}"]

    # Ask the user to select the division if the team is in F2 or F3
    if team in F2_F3_TEAMS:
        view = discord.ui.View(timeout=60)

        # Create division selection buttons
        async def on_button_click(interaction: discord.Interaction):
            division = interaction.data['custom_id']
            key = f"{division}-{team}"

            protests = load_protests()
            found = False

            if key in protests and protests[key]:
                last_protest = protests[key].pop()
                save_protests(protests)
                embed = discord.Embed(
                    title="Protest Reverted",
                    description=f"✅ A protest for {key} has been reverted.\n\n**Removed protest by:** {last_protest['user']} on {last_protest['timestamp']}",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
                found = True
                return

            if not found:
                embed = discord.Embed(
                    description=f"⚠️ No protests found to revert for {key}.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed)

        f2_button = discord.ui.Button(label="F2", style=discord.ButtonStyle.green, custom_id="F2")
        f3_button = discord.ui.Button(label="F3", style=discord.ButtonStyle.blurple, custom_id="F3")

        f2_button.callback = on_button_click
        f3_button.callback = on_button_click

        view.add_item(f2_button)
        view.add_item(f3_button)

        embed = discord.Embed(
            description=f"❓ Select the division for the {team} protest to revert.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

    else:
        protests = load_protests()
        found = False

        for key in possible_keys:
            if key in protests and protests[key]:
                last_protest = protests[key].pop()
                save_protests(protests)
                embed = discord.Embed(
                    title="Protest Reverted",
                    description=f"✅ A protest for {key} has been reverted.\n\n**Removed protest by:** {last_protest['user']} on {last_protest['timestamp']}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                found = True
                break

        if not found:
            embed = discord.Embed(
                description=f"⚠️ No protests found to revert for {team}.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)


@commands.command(name="protests", help="Show the current protest standings.")
async def protests_command(ctx):
    protests = load_protests()

    if not protests:
        embed = discord.Embed(
            description="No protests have been submitted yet.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        return

    f1_embed = discord.Embed(title="📊 F1 Protest Standings", color=discord.Color.red())
    f2_embed = discord.Embed(title="📊 F2 Protest Standings", color=discord.Color.green())
    f3_embed = discord.Embed(title="📊 F3 Protest Standings", color=discord.Color.blue())

    for team_key, entries in protests.items():
        value = "\n".join(
            [f"- {entry['user']} ({entry['timestamp']})" for entry in entries]
        )

        if "-" in team_key:
            division, team = team_key.split("-", 1)
            if division == "F2":
                f2_embed.add_field(name=f"{team} - {len(entries)}/{MAX_PROTESTS}", value=value, inline=False)
            elif division == "F3":
                f3_embed.add_field(name=f"{team} - {len(entries)}/{MAX_PROTESTS}", value=value, inline=False)
        else:
            f1_embed.add_field(name=f"{team_key} - {len(entries)}/{MAX_PROTESTS}", value=value, inline=False)

    await ctx.send(embed=f1_embed)
    await ctx.send(embed=f2_embed)
    await ctx.send(embed=f3_embed)
