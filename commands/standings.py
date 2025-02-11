import discord
from discord.ext import commands
import pandas as pd
import requests
import io

# Direct download link from OneDrive
ONEDRIVE_LINK = "https://1drv.ms/x/c/9c4419a56c87af87/EcWEZzJck3BJjL6mBqoLV18B4yHpFpphqMnLTIkg2yOraA?download=1"

@commands.command(name="standings", help="Get current F1 or F2 standings. Usage: !standings F1 or !standings F2")
async def standings_command(ctx, category: str = None):
    if category is None:
        embed = discord.Embed(
            description="❌ **Usage:** `!standings F1` or `!standings F2`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return  

    category = category.upper()

    # Updated standings ranges
    STANDINGS_RANGES = {
        "F1": (46, 77, 20, 22),  # U47:V77
        "F2": (46, 77, 35, 37)   # AJ47:AK77
    }

    if category not in STANDINGS_RANGES:
        embed = discord.Embed(
            description="❌ Invalid category! Use `!standings F1` or `!standings F2`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        # Download the Excel file
        response = requests.get(ONEDRIVE_LINK)
        response.raise_for_status()  

        # Load Excel file
        excel_data = pd.ExcelFile(io.BytesIO(response.content))
        df = excel_data.parse("Calendar and Standings")

        # Extract the relevant standings
        start_row, end_row, start_col, end_col = STANDINGS_RANGES[category]
        standings = df.iloc[start_row:end_row, start_col:end_col]

        # Rename columns
        standings.columns = ["Driver", "Points"]
        standings = standings.dropna()  

        # Convert Points to integer for sorting
        standings["Points"] = standings["Points"].astype(int)
        standings = standings.sort_values(by="Points", ascending=False)

        # Format standings
        standings_text = "\n".join(
            [f"**{row['Driver']}** - {row['Points']} pts"
             for i, row in standings.iterrows()]
        )

        # Send response in an embedded message
        embed = discord.Embed(
            title=f"{category} Standings",
            description=standings_text,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            description=f"❌ Error fetching standings: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
