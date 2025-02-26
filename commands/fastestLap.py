import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load fastest lap data from JSON
def load_lap_data():
    with open("fastest_laps.json", "r") as file:
        return json.load(file)

@commands.command(name="fastestLap")
async def fastest_lap(ctx, *, track_name: str):  # '*' allows multi-word track names
    lap_data = load_lap_data()  # Load lap times from JSON

    if track_name.lower() == "map":  # Show available tracks
        track_list = ", ".join(lap_data.keys())  
        embed = discord.Embed(
            title="📍 Available Tracks",
            description=f"**{track_list}**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    # Normalize input and find the correct track name regardless of case sensitivity
    normalized_track_name = next((key for key in lap_data if key.lower() == track_name.lower()), None)

    if normalized_track_name:
        fastest_time = lap_data[normalized_track_name]
        
        # Create an embed message
        embed = discord.Embed(
            title=f"🏁 Fastest Lap - {normalized_track_name}",
            description=f"**{fastest_time:.4f} seconds**",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Track Not Found",
            description=f"Track '**{track_name}**' was not found in the database.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
