import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch the Sporting Regulations link from the .env file
Sporting_Regulation_Link = os.getenv("Sporting_Regulation_Link")

@commands.command(name="regs")
async def regs(ctx):
    embed = discord.Embed(
        title="Formula V - FIA",
        description=f"**[Sporting Regulations]({Sporting_Regulation_Link})**",
        color=discord.Color.gold()
    )

    file_path = "src/LogoFia.png"  # Ensure this file exists
    file = discord.File(file_path, filename="LogoFia.png")  # Attach file
    embed.set_thumbnail(url="attachment://LogoFia.png")  # Use attachment

    await ctx.send(embed=embed, file=file)  # Attach the file here
