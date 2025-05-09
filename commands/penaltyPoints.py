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

@commands.command(name="lw", aliases=["lagwarning"], help="Get lag warnings. Usage: !lw or !lw F1/F2/F3")
async def lag_warnings(ctx, league: str = None):
    try:
        leagues = {
            "F1": {"cols": [20, 21], "rows": (113, 131)},  # U114:V132
            "F2": {"cols": [35, 36], "rows": (113, 131)},  # AJ114:AK132
            "F3": {"cols": [48, 49], "rows": (113, 131)},   # AW114:AX132
        }

        excel_path = "Formula V SuperLicense.xlsx"
        messages = []
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

            df.columns = ["Driver", "Warnings"]
            df = df.dropna()
            df["Warnings"] = df["Warnings"].astype(int)
            df = df.sort_values(by="Warnings", ascending=False)

            embed = discord.Embed(
                title=f"{league} Lag Warnings",
                color=discord.Color.orange()
            )
            for _, row in df.iterrows():
                embed.add_field(name=row["Driver"], value=f"{row['Warnings']} warnings", inline=True)
                if row["Warnings"] >= 3:
                    messages.append(f"🚨 {league}: **{row['Driver']}** has {row['Warnings']} lag warnings!")

            await ctx.send(embed=embed)
            for msg in messages:
                await ctx.send(msg)

        else:
            for lg, info in leagues.items():
                start_row, end_row = info["rows"]
                cols = info["cols"]
                df = df_all.iloc[start_row:end_row + 1, cols[0]:cols[1] + 1]

                df.columns = ["Driver", "Warnings"]
                df = df.dropna()
                df["Warnings"] = df["Warnings"].astype(int)
                df = df.sort_values(by="Warnings", ascending=False)

                embed = discord.Embed(
                    title=f"{lg} Lag Warnings",
                    color=discord.Color.orange()
                )
                for _, row in df.iterrows():
                    embed.add_field(name=row["Driver"], value=f"{row['Warnings']} warnings", inline=True)
                    if row["Warnings"] >= 3:
                        messages.append(f"🚨 {lg}: **{row['Driver']}** has {row['Warnings']} lag warnings!")
                
                await ctx.send(embed=embed)
            
            for msg in messages:
                await ctx.send(msg)

    except Exception as e:
        await ctx.send(embed=discord.Embed(
            description=f"❌ Error reading lag warnings: {str(e)}",
            color=discord.Color.red()
        ))

@commands.command(name="rep", aliases=["reps", "reprimand", "reprimands"], help="Get reprimands. Usage: !rep or !rep F1/F2/F3")
async def reprimands(ctx, league: str = None):
    try:
        leagues = {
            "F1": {"cols": [20, 21], "rows": (140, 158)},  # U141:V159
            "F2": {"cols": [35, 36], "rows": (140, 158)},  # AJ141:AK159
            "F3": {"cols": [48, 49], "rows": (140, 158)},   # AW141:AX159
        }

        excel_path = "Formula V SuperLicense.xlsx"
        messages = []
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

            df.columns = ["Driver", "Reprimands"]
            df = df.dropna()
            df["Reprimands"] = df["Reprimands"].astype(int)
            df = df.sort_values(by="Reprimands", ascending=False)

            embed = discord.Embed(
                title=f"{league} Reprimands",
                color=discord.Color.purple()
            )
            for _, row in df.iterrows():
                embed.add_field(name=row["Driver"], value=f"{row['Reprimands']} reprimands", inline=True)
                if row["Reprimands"] >= 3:
                    messages.append(f"🚨 {league}: **{row['Driver']}** has {row['Reprimands']} reprimands!")

            await ctx.send(embed=embed)
            for msg in messages:
                await ctx.send(msg)

        else:
            for lg, info in leagues.items():
                start_row, end_row = info["rows"]
                cols = info["cols"]
                df = df_all.iloc[start_row:end_row + 1, cols[0]:cols[1] + 1]

                df.columns = ["Driver", "Reprimands"]
                df = df.dropna()
                df["Reprimands"] = df["Reprimands"].astype(int)
                df = df.sort_values(by="Reprimands", ascending=False)

                embed = discord.Embed(
                    title=f"{lg} Reprimands",
                    color=discord.Color.purple()
                )
                for _, row in df.iterrows():
                    embed.add_field(name=row["Driver"], value=f"{row['Reprimands']} reprimands", inline=True)
                    if row["Reprimands"] >= 3:
                        messages.append(f"🚨 {lg}: **{row['Driver']}** has {row['Reprimands']} reprimands!")
                
                await ctx.send(embed=embed)
            
            for msg in messages:
                await ctx.send(msg)

    except Exception as e:
        await ctx.send(embed=discord.Embed(
            description=f"❌ Error reading reprimands: {str(e)}",
            color=discord.Color.red()
        ))