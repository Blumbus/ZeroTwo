import asyncio
import time
import json
import discord
import os

from discord.ext import commands
from utils.data import Bot
from utils import default


class Shop(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command(aliases=['magmaenergy', 'energy', 'balance'])
    @commands.guild_only()
    async def mag(self, ctx):
        """ Displays your total magma energy (server points spent on fun things, you get these by being active) """

        mag = self.bot.server_data.get_energy(str(ctx.message.guild.id), str(ctx.message.author.id))
        await ctx.send(f"{ctx.message.author.name}'s magma energy: **{mag}**" + self.config.mag_emoji)

    @commands.command(aliases=["top"])
    @commands.guild_only()
    async def leaderboard(self, ctx, page: int = None):
        """ Displays a leaderboard of total mag for the current server """

        server = str(ctx.guild.id)
        self_id = str(ctx.message.author.id)
        server_name = str(ctx.guild.name)
        server_icon = ctx.guild.icon_url
        server_link = self.bot.server_data.get_invite_link(server)

        spots = 10
        if page is None:
            page = 1
        start = (page - 1) * spots

        users = self.bot.server_data.get_users(server)
        users.sort(key=lambda u: u.xp, reverse=True)

        self_rank = 0
        self_xp = 0
        for i in range(len(users)):
            user = users[i]
            if user.user_id == self_id:
                self_rank = i + 1
                self_xp = user.xp

        embed = discord.Embed(
            title=server_name + " Leaderboard",
            url=server_link,
            color=discord.Color.red())
        embed.set_thumbnail(url=server_icon)
        for index in range(start, min(start + spots, len(users))):
            user = users[index]
            user_name = user.user_id
            member = None
            try:
                member = await self.bot.fetch_user(user.user_id)
            except:
                member = None
            if member is not None:
                user_name = member.name
            embed.add_field(name=f'**Rank {index + 1}**', value=f'{user_name}: {user.xp} {self.config.mag_emoji}',
                            inline=False)
        embed.set_footer(text=f"You are rank {self_rank} with {self_xp} xp")

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def rank(self, ctx):
        """ Displays your ranking of total mag in the server """
        server = str(ctx.guild.id)
        self_id = str(ctx.message.author.id)

        users = self.bot.server_data.get_users(server)
        users.sort(key=lambda u: u.xp, reverse=True)

        self_rank = 0
        for i in range(len(users)):
            user = users[i]
            if user.user_id == self_id:
                self_rank = i + 1

        if self_rank == 1:
            await ctx.send("You have the most total mag in this server :crown: ")
        else:
            await ctx.send(f"Your all time mag rank is **{str(self_rank)}**")

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
