import discord
from discord.ext import commands
import pandas as pd

@commands.command(name="pp", help="Get penalty points. Usage: !pp or !pp F1/F2/F3")
async def penalty_points(ctx, league: str = None):
    try:
        # Define league-specific slicing info (start row is 86 for U87 etc.)
        leagues = {
            "F1": {"cols": [20, 21], "rows": (86, 105)},  # U87:V105
            "F2": {"cols": [35, 36], "rows": (86, 105)},  # AJ87:AK105
            "F3": {"cols": [48, 49], "rows": (86, 105)},  # AW87:AX105
        }

        excel_path = "Formula V SuperLicense.xlsx"
        messages = []

        # Load entire sheet once
        df_all = pd.read_excel(excel_path, sheet_name="Calendar and Standings", header=None)

        if league:
            league = league.upper()
            if league not in leagues:
                await ctx.send(embed=discord.Embed(
                    description="❌ Invalid league! Use `F1`, `F2`, or `F3`.",
                    color=discord.Color.red()
                ))
                return

            info = leagues[league]
            start_row, end_row = info["rows"]
            cols = info["cols"]
            df = df_all.iloc[start_row:end_row + 1, cols[0]:cols[1] + 1]

            df.columns = ["Driver", "Points"]
            df = df.dropna()
            df["Points"] = df["Points"].astype(int)
            df = df.sort_values(by="Points", ascending=False)

            embed = discord.Embed(
                title=f"{league} Penalty Points",
                color=discord.Color.red()
            )
            for _, row in df.iterrows():
                embed.add_field(name=row["Driver"], value=f"{row['Points']} points", inline=True)
                if row["Points"] >= 12:
                    messages.append(f"🚨 {league}: **{row['Driver']}** SHOULD BE BANNED FOR THIS WEEK!")

            await ctx.send(embed=embed)
            for msg in messages:
                await ctx.send(msg)

        else:
            for lg, info in leagues.items():
                start_row, end_row = info["rows"]
                cols = info["cols"]
                df = df_all.iloc[start_row:end_row + 1, cols[0]:cols[1] + 1]

                df.columns = ["Driver", "Points"]
                df = df.dropna()
                df["Points"] = df["Points"].astype(int)
                df = df.sort_values(by="Points", ascending=False)

                embed = discord.Embed(
                    title=f"{lg} Penalty Points",
                    color=discord.Color.red()
                )
                for _, row in df.iterrows():
                    embed.add_field(name=row["Driver"], value=f"{row['Points']} points", inline=True)
                    if row["Points"] >= 12:
                        messages.append(f"🚨 {lg}: **{row['Driver']}** SHOULD BE BANNED FOR THIS WEEK!")

                await ctx.send(embed=embed)

            for msg in messages:
                await ctx.send(msg)

    except Exception as e:
        await ctx.send(embed=discord.Embed(
            description=f"❌ Error reading penalty points: {str(e)}",
            color=discord.Color.red()
        ))
