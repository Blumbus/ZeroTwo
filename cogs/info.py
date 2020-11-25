import time
import discord
import os

from datetime import datetime
from discord.ext import commands
from utils import default


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command()
    async def ping(self, ctx):
        """ Pong! """
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("🏓 Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {int(ping)}ms")

    @commands.command()
    @commands.guild_only()
    async def homechannel(self, ctx):
        """ Shows the server's home channel (where welcome messages get sent) """

        home = self.bot.server_data.get_home_channel(str(ctx.message.guild.id))
        if home is None:
            await ctx.send("No home channel found for this server")
        else:
            await ctx.send(f"Home channel: **#{home.name}** ({str(home.id)})")


def setup(bot):
    bot.add_cog(Information(bot))
