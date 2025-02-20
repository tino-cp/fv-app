import discord
from discord.ext import commands
import pandas as pd
import requests
import io

ONEDRIVE_LINK = "https://1drv.ms/x/c/9c4419a56c87af87/EcWEZzJck3BJjL6mBqoLV18B4yHpFpphqMnLTIkg2yOraA?download=1"

@commands.command(name="results", help="Get race results for a specific race (e.g., !results F1_R1)")
async def results_command(ctx, race: str):
    try:
        # Download the Excel file
        response = requests.get(ONEDRIVE_LINK)
        response.raise_for_status()

        # Read the Excel file
        excel_data = pd.ExcelFile(io.BytesIO(response.content))

        # Check if the requested race sheet exists
        if race not in excel_data.sheet_names:
            embed = discord.Embed(
                description=f"❌ Race `{race}` not found in the spreadsheet.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Read race results (AQ78:AW97 -> zero-indexed: 77:97, 42:49)
        df = excel_data.parse(race)
        race_results = df.iloc[76:97, 42:49]  # 7 columns expected

        # Define expected column names
        expected_columns = ["Position", "Driver", "Team", "Pts", "Race Time", "Fast Lap", "Penalty"]
        if race_results.shape[1] == 6:  
            expected_columns.remove("Penalty")  # Adjust if missing

        race_results.columns = expected_columns
        race_results = race_results.dropna(subset=["Driver", "Team"])  # Keep all valid drivers

        # Handle NaN values & conversion issues
        race_results["Position"] = race_results["Position"].fillna(0).astype(int)
        race_results["Pts"] = race_results["Pts"].fillna(0).astype(int)

        # Format time correctly (remove 00: if present)
        def format_time(time_value):
            if pd.isna(time_value):
                return "N/A"
            time_str = str(time_value)
            return time_str[3:] if time_str.startswith("00:") else time_str  # Remove "00:" prefix

        # Format race results
        results_text = "\n".join([
            f"**{row['Position']}. {row['Driver']}** ({row['Team']}) - {row['Pts']} pts | ⏱ {format_time(row['Race Time'])} | Fast Lap: {format_time(row['Fast Lap'])}" +
            (f" | ⚠️ Penalty: {row['Penalty']}" if "Penalty" in race_results.columns and pd.notna(row['Penalty']) else "")
            for _, row in race_results.iterrows()
        ])

        # Send embedded results
        embed = discord.Embed(
            title=f"🏁 Race Results: {race}",
            description=results_text,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            description=f"❌ Error fetching race results: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
