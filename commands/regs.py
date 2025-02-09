import discord
from discord.ext import commands

@commands.command(name="regs")
async def regs(ctx):
    embed = discord.Embed(
        title="Formula V - FIA",
        description="[Sporting Regulations](https://docs.google.com/document/d/10aT4ssU5WCBUexdzDpRqCX8nC56W-_CC/edit?usp=sharing&ouid=100666205706563869979&rtpof=true)",
        color=discord.Color.gold()
    )

    file_path = "src/LogoFia.png"  # Ensure this file exists
    file = discord.File(file_path, filename="LogoFia.png")  # Attach file
    embed.set_thumbnail(url="attachment://LogoFia.png")  # Use attachment

    await ctx.send(embed=embed, file=file)  # Attach the file here