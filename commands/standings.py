import discord
from discord.ext import commands
import pandas as pd
import os

@commands.command(name="standings", help="Get current F1 F2 or F3 standings. Usage: !standings F1, F2, F1C, or F2C")
async def standings_command(ctx, category: str = None):
    if category is None:
        embed = discord.Embed(
            description="❌ **Usage:** `!standings F1`, `!standings F2`, `!standings F1C`, or `!standings F2C`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    category = category.upper()
    is_constructor = category.endswith("C")
    league = category[:-1] if is_constructor else category

    # Define ranges for both drivers and constructors
    STANDINGS_RANGES = {
        "F1": {
            "driver": (46, 77, 20, 22),   # U47:V77
            "constructor": (29, 40, 20, 22)  # U30:V39
        },
        "F2": {
            "driver": (46, 77, 35, 37),   # AJ47:AK77
            "constructor": (29, 40, 35, 37)  # AJ30:AK40
        },
        "F3": {
            "driver": (46, 77, 48, 49),   # AJ47:AK77
            "constructor": (29, 40, 48, 49)  # AJ30:AK40
        }
    }

    if league not in STANDINGS_RANGES:
        embed = discord.Embed(
            description="❌ Invalid league! Use `F1`, `F2`, `F1C`, `F2C`, `F3C` or `F3`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    try:
        # Load Excel
        excel_path = "Formula V SuperLicense.xlsx"
        df = pd.read_excel(excel_path, sheet_name="Calendar and Standings")

        # Select correct range
        range_type = "constructor" if is_constructor else "driver"
        start_row, end_row, start_col, end_col = STANDINGS_RANGES[league][range_type]
        standings = df.iloc[start_row:end_row, start_col:end_col]

        # Set appropriate column names
        standings.columns = ["Team" if is_constructor else "Driver", "Points"]
        standings = standings.dropna()

        # Convert Points to int
        standings["Points"] = standings["Points"].astype(int)
        standings = standings.sort_values(by="Points", ascending=False)

        # Format output
        standings_text = "\n".join(
            [f"**{row['Team' if is_constructor else 'Driver']}** - {row['Points']} pts"
             for _, row in standings.iterrows()]
        )

        # Create embed
        embed = discord.Embed(
            title=f"{league} {'Constructors' if is_constructor else 'Drivers'} Standings",
            description=standings_text,
            color=discord.Color.blue() if is_constructor else discord.Color.gold()
        )
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            description=f"❌ Error fetching standings: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
