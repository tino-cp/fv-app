import discord
from discord.ext import commands

"""

@commands.command(name="nuke", help="Send a funny nuke GIF.")
async def nuke_command(ctx):
    with open("gif/idk-angry-emoji.gif", "rb") as gif_file:
        file = discord.File(gif_file, filename="idk-angry-emoji.gif")
        embed = discord.Embed(
            title="Care to explain yourself?",
            description="are you from GTR? 🤔",
            color=discord.Color.red()
        )
        embed.set_image(url=f"attachment://{file.filename}")
        await ctx.send(embed=embed, file=file)
"""

@commands.command()
async def delta(ctx):
    with open("gif/revive-hes-alive.gif", "rb") as gif_file:
        file = discord.File(gif_file, filename="revive-hes-alive.gif")
        embed = discord.Embed(
            title="Delta",
            description="Coming soon...",
            color=discord.Color.blue()
        )
        embed.set_image(url=f"attachment://{file.filename}")
        await ctx.send(embed=embed, file=file)
