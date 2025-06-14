import discord
from discord.ext import commands

@commands.command(name="df")
async def downforce(ctx):
    embed = discord.Embed(
        title="Downforce Levels for OpenWheel Wings",
        color=discord.Color.gold()
    )
    file = discord.File("src\df.png", filename="downforce.png")  # Change path to the correct one if needed
    embed.set_image(url="attachment://downforce.png")
    await ctx.send(embed=embed, file=file)

@commands.command(name="spreadsheet", aliases=['ss'])
async def spreadsheet(ctx):
    embed = discord.Embed(
        title="Master spreadsheet",
        description="[Click here to open the spreadsheet](https://1drv.ms/x/c/9c4419a56c87af87/EeGS-7ifYeZMmBEuwePw4isBNTC79SLv--PKTPnrOE5uew?e=kLwSdn)",
        color=discord.Color.blue()
    )

    file = discord.File("src\\LogoFia.png", filename="LogoFia.png")
    embed.set_thumbnail(url="attachment://LogoFia.png")

    await ctx.send(embed=embed, file=file)

@commands.command(name="getStarted")
async def getStarted(ctx):
    embed = discord.Embed(
        title="✅ Approved for Racing",
        description=(
            "Now you can drive **Formula 3**, and reserve in **F2** and **F1** if a manager picks you. "
            "For now focus on **Formula 3** and if you do well, **F2**.\n\n"
            "At the top of the server you can find the **Events tab** — there you can see the date of the next race "
            "and the track links for the quali and race track.\n\n"
            "Keep in mind that in the normal league you **don't have to drive max downforce** like you did in the drivers test. "
            "Also, the tracks on the calendar have **KERS**, which you didn't have in the drivers test.\n\n"
            "Don't forget about track limits, during race and quali you can get a warning/time penalty for exceeding track limits.\n\n"
            "If you have any questions, feel free to ask in the **#general** channel or DM managers or staff\n\n"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@commands.command(name="signup")
async def signup(ctx):
    embed = discord.Embed(
        title="📝 How to get started",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="🏍️ Other Leagues (MotoVGP, Indy, etc.)",
        value=(
            "You can simply **show up** for events and join in.\n"
            "Make sure to pick up a role in <#1033365399682686997> "
            "so you’re notified when events happen.\n\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🏎️ Main Formula League (F1/F2/F3)",
        value=(
            "To drive in our main Formula league, you must first **pass the driver's test**.\n"
            "1. Open a ticket in <#1269926866131877900> and follow the instructions.\n"
            "2. After passing, you can join as a **reserve driver**, or become a **main driver** if picked by a manager.\n\n"
        ),
        inline=False
    )

    embed.set_footer(text="If you're ever unsure, just ask a staff member!")

    await ctx.send(embed=embed)    