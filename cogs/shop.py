import asyncio
import time
import discord
import os

from discord.ext import commands
from utils import default


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command(aliases=['magmaenergy', 'energy', 'balance'])
    @commands.guild_only()
    async def mag(self, ctx):
        """ Displays your total magma energy (server points spent on fun things, you get these by being active) """

        mag = self.bot.server_data.get_energy(str(ctx.message.guild.id), str(ctx.message.author.id))
        await ctx.send(f"{ctx.message.author.name}'s magma energy: **{mag}**" + self.config.mag_emoji)

    async def purchase(self, ctx):
        user = ctx.message.author
        command = ctx.command
        price = self.bot.server_data.get_shop_price(str(ctx.message.guild.id), command.name)
        if price == 0:
            return True
        balance = self.bot.server_data.get_energy(str(ctx.message.guild.id), str(ctx.message.author.id))
        if price > balance:
            await ctx.send(f"**{user.display_name}**, you don't have enough energy to buy *{command.name}* (Price: {str(price) + self.config.mag_emoji} Balance: {str(balance) + self.config.mag_emoji})")
            return False
        prompt = await ctx.send(f"**{user.display_name}**, do you want to buy *{command.name}* for {str(price) + self.config.mag_emoji}? (Balance: {str(balance) + self.config.mag_emoji})")
        check_emoji = chr(0x2705)
        cross_emoji = chr(0x274C)
        await prompt.add_reaction(check_emoji)
        await prompt.add_reaction(cross_emoji)

        def check(rct, usr):
            return usr == user and (rct.emoji == check_emoji or rct.emoji == cross_emoji) and rct.message == prompt

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            prompt = None
        else:
            prompt = None
            if reaction.emoji == check_emoji:
                self.bot.server_data.give_energy(str(ctx.message.guild.id), str(ctx.message.author.id), -price)
                return True
        return False


def setup(bot):
    bot.add_cog(Shop(bot))
