import discord
from discord.ext import commands
import pandas as pd
import datetime
import os

@commands.command(name="results", help="Get race results for a specific race (e.g., !results F1_R1)")
async def results_command(ctx, race: str):
    try:
        # Load the Excel file directly
        excel_path = "Formula V SuperLicense.xlsx"
        excel_data = pd.ExcelFile(excel_path, engine='openpyxl')

        # Check if the requested race sheet exists
        if race not in excel_data.sheet_names:
            embed = discord.Embed(
                description=f"❌ Race `{race}` not found in the spreadsheet.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Read race results (AQ78:AW97 -> zero-indexed: 76:97, 42:49)
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

        # Function to format time correctly
        def format_time(time_value):
            if pd.isna(time_value):
                return "N/A"
            try:
                if isinstance(time_value, datetime.time):
                    # Convert to string and extract MM:SS.sss
                    time_str = time_value.strftime("%H:%M:%S.%f")[:-3]  # Remove extra decimals
                    return time_str[3:] if time_str.startswith("00:") else time_str  # Remove "00:"
                elif isinstance(time_value, (pd.Timestamp, pd.Timedelta)):
                    total_seconds = time_value.total_seconds()
                    minutes = int(total_seconds // 60)
                    seconds = total_seconds % 60
                    return f"{minutes}:{seconds:06.3f}"  # MM:SS.sss format
                elif isinstance(time_value, str) and ":" in time_value:
                    parts = time_value.split(":")
                    minutes, seconds = parts[-2], parts[-1]  # Keep last two parts
                    return f"{minutes}:{float(seconds):06.3f}"
                return f"{float(time_value):.3f}"  # Ensure three decimal places
            except ValueError:
                return str(time_value)  # Fallback for unexpected values

        # Find the driver with the fastest lap
        fastest_lap_driver = None
        fastest_lap_time = float("inf")  # Set to a very high value to find the minimum

        for _, row in race_results.iterrows():
            if pd.notna(row['Fast Lap']) and row['Fast Lap'] != 'N/A' and row['Fast Lap'] != 'DNF':
                # If the fast lap is a datetime.time object, convert it to total seconds
                if isinstance(row['Fast Lap'], datetime.time):
                    lap_time = row['Fast Lap'].minute * 60 + row['Fast Lap'].second + (row['Fast Lap'].microsecond / 1_000_000)
                else:
                    # Otherwise, it's already a string, so we handle it as before
                    lap_time = float(row['Fast Lap'].split(":")[1]) + (float(row['Fast Lap'].split(":")[0]) * 60)  # Convert time to seconds
                
                if lap_time < fastest_lap_time:
                    fastest_lap_time = lap_time
                    fastest_lap_driver = row['Driver']

        # Format race results with the star emoji for the fastest lap
        results_text = "\n\n".join([
            f"**{row['Position']}. {row['Driver']} ({row['Team']})**\n"
            f"{row['Pts']} pts | ⏱ {format_time(row['Race Time'])} | Fast Lap: {format_time(row['Fast Lap'])}"
            + (f" ⭐" if row['Driver'] == fastest_lap_driver else "")
            + (f" | ⚠️ Penalty: {row['Penalty']}" if "Penalty" in race_results.columns and pd.notna(row['Penalty']) and str(row['Penalty']).strip() else "")
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