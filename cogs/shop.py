import time
import discord
import os

from discord.ext import commands
from utils import default


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command(aliases=['magmaenergy', 'energy'])
    @commands.guild_only()
    async def mag(self, ctx):
        mag = self.bot.server_data.get_coins(str(ctx.message.guild.id), str(ctx.message.author.id))
        await ctx.send(f"{ctx.message.author.name}'s magma energy: **{mag}**" + self.config.mag_emoji)


def setup(bot):
    bot.add_cog(Shop(bot))
