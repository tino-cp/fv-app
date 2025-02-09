import discord
from discord.ext import commands

@commands.command(name="regs")
async def regs(ctx):
    embed = discord.Embed(
        title="Formula V - FIA",
        description="[Sporting Regulations](https://docs.google.com/document/d/10aT4ssU5WCBUexdzDpRqCX8nC56W-_CC/edit?usp=sharing&ouid=100666205706563869979&rtpof=true&sd=true)",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/FIA_logo.svg/1200px-FIA_logo.svg.png")  # FIA logo
    await ctx.send(embed=embed)
