import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Bot commands
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

from commands.lapchecks import LapChecks
from commands.weather import weather, rain
from commands.race import race
from commands.penalty import start_timer, cancel_timer, pen_command, pen_summary, PenaltyCog
from commands.help import show_help
from commands.raceAttendance import RaceAttendance
from commands.regs import regs
from commands.downforce import downforce
from commands.protest import protest_command
from commands.protest import protests_command

bot.add_command(weather)
bot.add_command(rain)
bot.add_command(race)
bot.add_command(start_timer)
bot.add_command(cancel_timer)
bot.add_command(show_help)
bot.add_command(pen_command)
bot.add_command(pen_summary)
bot.add_command(regs)
bot.add_command(downforce)
bot.add_command(protest_command)
bot.add_command(protests_command)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await bot.add_cog(LapChecks(bot))
    await bot.add_cog(PenaltyCog(bot))
    await bot.add_cog(RaceAttendance(bot))

# Start the bot with the token from your .env file
bot.run(os.getenv('DISCORD_TOKEN'))
