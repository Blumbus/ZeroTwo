import os

import discord
from utils import default
from utils.data import Bot, HelpFormat
from utils.serverdata import ServerData

config = default.get("config.json")
token = default.get("token.json")
print("Logging in...")

intents = discord.Intents.default()
intents.reactions = True
intents.members = True

helper = HelpFormat()

bot = Bot(
    command_prefix=config.prefix,
    intents=intents,
    prefix=config.prefix,
    command_attrs=dict(hidden=True),
    help_command=helper
)

bot.server_data = ServerData(bot)

for file in os.listdir("cogs"):
    if file.endswith(".py") and not '__init__' in file:
        name = file[:-3]
        bot.load_extension(f"cogs.{name}")

bot.run(token.t1 + token.t2)
