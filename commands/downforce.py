import discord
from discord.ext import commands

@commands.command(name="df")
async def downforce(ctx):
    embed = discord.Embed(
        title="Downforce Levels for OpenWheel Wings",
        color=discord.Color.red()
    )
    file = discord.File("src\df.png", filename="downforce.png")  # Change path to the correct one if needed
    embed.set_image(url="attachment://downforce.png")
    await ctx.send(embed=embed, file=file)
