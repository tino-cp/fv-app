import discord
from discord.ext import commands
import json
import os
from datetime import datetime

PROTESTS_FILE = "protests.json"  # File where protests are stored
MAX_PROTESTS = 3  # Maximum protests per team

def load_protests():
    """Loads protests from a JSON file."""
    if os.path.exists(PROTESTS_FILE):
        with open(PROTESTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_protests(data):
    """Saves protests to a JSON file."""
    with open(PROTESTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

@commands.command(name="protest", help="Submit a protest for a team.")
async def protest_command(ctx, team: str):  # Type hint should just be `str`
    team = team.upper()  # Convert the input to uppercase
    protests = load_protests()

    # Ensure team exists in protests.json
    if team not in protests:
        protests[team] = []

    # Check if max protests reached
    if len(protests[team]) >= MAX_PROTESTS:
        embed = discord.Embed(
            description=f"{team} has already used all {MAX_PROTESTS} protest points.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Add protest with username and timestamp
    protest_entry = {
        "user": ctx.author.name,
        "user_id": ctx.author.id,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    protests[team].append(protest_entry)
    save_protests(protests)

    # Send protest confirmation + link
    embed = discord.Embed(
        title="Protest Submitted",
        description=f"✅ {team} has submitted a protest.\n\n[Create a ticket here](https://discord.com/channels/843175947304960020/982599539414413332/1003349125699477574)",
        color=discord.Color.gold()
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

    embed = discord.Embed(
        title="Protest Standings",
        description="Teams and their protest usage:",
        color=discord.Color.gold()
    )

    for team, entries in protests.items():
        protest_info = "\n".join(
            [f"- {entry['user']} ({entry['timestamp']})" for entry in entries]
        )
        embed.add_field(
            name=f"{team} - {len(entries)}/{MAX_PROTESTS} protests used",
            value=protest_info,
            inline=False
        )

    await ctx.send(embed=embed)
