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

<<<<<<< Updated upstream
=======
    @commands.command()
    @commands.guild_only()
    async def leaderboardthing(self,ctx, page: int = None):
        "Displays a leaderboard of total mag for the current server"

        file = open('serverdata.json')
        data = json.load(file)


        server = str(ctx.message.guild.id)
        servername = data['servers'][server]["name"]
        servericon = ctx.guild.icon_url
        serverlink = data['servers'][server]['invite_link']

        if page is None:
            page = 1
        math = (page - 1) * 10
        users = ["", "", "", "", "", "", "", "", "", "", ]
        xpamounts = ["", "", "", "", "", "", "", "", "", "", ]
        rankswanted = [math + 1, math + 2, math + 3, math + 4, math + 5, math + 6, math + 7, math + 8, math + 9,
                       math + 10]

        for user in data['servers'][server]["users"]:
            userrank = data['servers'][server]["users"][user]["rank"]
            userxp = data['servers'][server]["users"][user]["xp"]

            if userrank in rankswanted:
                spot = rankswanted.index(userrank)

                usertogetname: discord.Member
                userid = int(user)
                usertogetname = self.bot.get_user(userid)
                try:
                    users[spot] = usertogetname.name
                except AttributeError:
                    users[spot] = user
                xpamounts[spot] = userxp

        embed = discord.Embed(
            title= servername + " Leaderboard",
            url=serverlink,
            color = discord.Color.red())
        embed.set_thumbnail(url = servericon)
        for slot in range(10):
            embed.add_field(name=f'**Rank {rankswanted[slot]}**', value=f'{users[slot]} with {xpamounts[slot]} mag',inline =False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def refreshranking(self,ctx):
        "Updates leaderboard with placement for the leaderboard"
        file = open('serverdata.json')
        data = json.load(file)

        server = str(ctx.message.guild.id)

        for user in data['servers'][server]["users"]:
            rank = 1

            currentmag = data['servers'][server]["users"][user]['xp']

            for rankingusers in data['servers'][server]["users"]:

                if user != rankingusers and data['servers'][server]["users"][rankingusers]['xp'] > currentmag:
                    rank += 1

            self.bot.server_data.set_placement(str(server),str(user),rank)

        await ctx.send("Leaderboard has been updated")

        file.close()



    @commands.command(aliases = ["leaderboard"])
    @commands.guild_only()
    async def rank(self,ctx):
        "Displays your ranking of how much magma you have compared to others"
        file = open('serverdata.json')
        data = json.load(file)

        server = str(ctx.message.guild.id)
        selfmag = self.bot.server_data.get_xp(str(ctx.message.guild.id), str(ctx.message.author.id))
        rank = 1
        for i in data['servers'][server]['users']:
            if data['servers'][server]['users'][i]['xp'] > selfmag:
                rank += 1
        if rank == 1:
            await ctx.send("You have made the most mag in this server :crown: ")
        else:
            await ctx.send("Your all time mag rank is " + str(rank))

        file.close()


>>>>>>> Stashed changes
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
