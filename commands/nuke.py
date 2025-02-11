import discord
from discord.ext import commands

@commands.command(name="nuke", help="Send a funny nuke GIF.")
async def nuke_command(ctx):
    gif_url = "https://media1.tenor.com/m/aH1MG0AZMBsAAAAC/sabrina-the-teenage-witch-salem.gif"  # Funny nuke GIF

    embed = discord.Embed(
        title="Care to explain yourself?",
        description="are you from GTR? 🤔",
        color=discord.Color.red()
    )
    embed.set_image(url=gif_url)

    await ctx.send(embed=embed)
