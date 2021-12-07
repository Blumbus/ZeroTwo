import random
import discord
import aiohttp
import asyncio

from io import BytesIO

from discord import Member, Role
from discord.ext import commands
from utils import lists, permissions, http, default


class Fun_Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command(aliases=['8ball'])
    async def eightball(self, ctx, *, question: commands.clean_content):
        """ Consult 8ball to receive an answer """
        answer = random.choice(lists.ballresponse)
        await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {answer}")

    async def randomimageapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except aiohttp.ClientConnectorError:
            return await ctx.send("The API seems to be down...")
        except aiohttp.ContentTypeError:
            return await ctx.send("The API returned an error or didn't return JSON...")

        await ctx.send(r[endpoint])

    @commands.command()
    @commands.guild_only()
    async def raffle(self, ctx):
        """ Shows your info for the server's current raffle """
        raffle_active = self.bot.server_data.get_raffle_active(str(ctx.message.guild.id))
        if raffle_active:
            tickets = self.bot.server_data.get_user_raffle_amount(str(ctx.message.guild.id), str(ctx.author.id))
            raffle_name = self.bot.server_data.get_raffle_name(str(ctx.message.guild.id))
            await ctx.send(f"You have **{str(tickets)}** tickets entered for the *{raffle_name}* raffle. React to my random ticket messages in time to earn more. Good luck!")
        else:
            await ctx.send(f"There is no current active raffle")

    async def randomimageapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except aiohttp.ClientConnectorError:
            return await ctx.send("The API seems to be down...")
        except aiohttp.ContentTypeError:
            return await ctx.send("The API returned an error or didn't return JSON...")

        await ctx.send(r[endpoint])

    async def api_img_creator(self, ctx, url, filename, content=None):
        async with ctx.channel.typing():
            req = await http.get(url, res_method="read")

            if req is None:
                return await ctx.send("I couldn't create the image ;-;")

            bio = BytesIO(req)
            bio.seek(0)
            await ctx.send(content=content, file=discord.File(bio, filename=filename))

    @commands.command()
    async def rate(self, ctx, *, thing: commands.clean_content):
        """ Rates what you desire """
        random.seed(str(thing))
        rate_amount = random.uniform(0.0, 100.0)
        await ctx.send(f"I'd rate `{thing}` a **{round(rate_amount)} / 100**")

    @commands.command()
    @commands.guild_only()
    async def displayrole(self, ctx, *, role):
        """ Sets your display role (prioritizes the color of a role you have) """
        if role not in map(lambda x: x.name, ctx.author.roles):
            await ctx.send(f"You do not have the role \"{role}\"")
        else:
            if role + ' (display)' not in map(lambda x: x.name, ctx.guild.roles):
                await ctx.send(f"There is no display role for \"{role}\"")
            else:
                try:
                    for r in ctx.author.roles:
                        if '(display)' in r.name:
                            await ctx.author.remove_roles(r)
                    adding = None
                    for r in ctx.guild.roles:
                        if r.name == role + ' (display)':
                            adding = r
                            break
                    await ctx.author.add_roles(adding)
                    await ctx.send(f"Updated display role to be **{role}**")
                except discord.Forbidden:
                    await ctx.send("Cannot modify roles for this user (Forbidden)")

    async def __add_role(self, member: Member, role: Role):
        await member.add_roles(role)

    @commands.command()
    @commands.guild_only()
    async def renamechannel(self, ctx, *, new_name):
        """ Lets you name the current channel to whatever you want for 1 hour """

        channel: discord.TextChannel
        channel = ctx.message.channel
        oldname = ctx.message.channel.name
        hours = 1
        seconds = hours * 3600

        normal_name = self.bot.server_data.get_normal_name(str(ctx.message.guild.id), str(ctx.message.channel.id))
        if normal_name != '':
            await ctx.send("The channel is already renamed right now, wait for it to reset first")
            return

        shop = self.bot.get_cog('Shop')
        purchased = await shop.purchase(ctx)

        if not purchased:
            return
        try:
            await asyncio.wait_for(channel.edit(name=new_name), timeout=1.0)
        except asyncio.TimeoutError:
            await ctx.send("I couldn't rename... that shouldn't happen. Maybe the channel rename was on cooldown?")
            return
        self.bot.server_data.set_normal_name(str(ctx.message.guild.id), str(ctx.message.channel.id), oldname)
        await ctx.send("Channel name has been changed to **" + new_name + "** for " + str(hours) + " hour" if hours == 1 else " hours")
        await asyncio.sleep(seconds)
        await channel.edit(name=oldname)
        self.bot.server_data.set_normal_name(str(ctx.message.guild.id), str(ctx.message.channel.id), '')

    @commands.command()
    @commands.guild_only()
    async def scramble(self, ctx, channel: discord.TextChannel = None, member: Member = None):
        """ Scrambles a random message from the channel's content """

        thos = 'that'
        if channel is None:
            channel = ctx.message.channel
            thos = 'this'
        allowed = self.bot.server_data.allowed_scramble(channel)
        if permissions.has_permissions(manage_roles=True):
            allowed = True
        if allowed is not True:
            await ctx.send(f"You're not allowed to scramble {thos} channel!")
            return
        shop = self.bot.get_cog('Shop')
        purchased = await shop.purchase(ctx)
        if not purchased:
            return
        async with ctx.typing():
            scramb = await self.get_scramble(channel, member)
        await ctx.send(scramb)

    async def get_scramble(self, channel: discord.TextChannel, member: Member = None):
        is_bot = member is not None and member.id == self.bot.user.id
        chain = {}
        found = 0
        async for message in channel.history(limit=7000):
            if (member is None or message.author.id == member.id) and not message.mention_everyone and (is_bot or message.author.id != self.bot.user.id):
                words = message.clean_content.split()
                if len(words) > 1:
                    for i in range(len(words) - 1):
                        word1 = words[i]
                        word2 = words[i + 1]
                        if word1 not in chain:
                            chain[word1] = {}
                        if word2 not in chain[word1]:
                            chain[word1][word2] = 1
                        else:
                            chain[word1][word2] += 1
                        found += 1
                if found > 2000:
                    break

        sentence_prob = 0.98
        num_makes = random.randint(50, 60)
        sent_chain = 0
        res = ''
        last_word = None
        if len(chain) == 0:
            return f"I couldn't find any recent messages matching what you want {self.config.sad_emoji} Try scrambling something with more recent messages"
        for i in range(num_makes):
            new_word = ''
            if last_word is None or last_word not in chain or chain[last_word] is None or len(chain[last_word]) == 0:
                new_word = random.choice(list(chain.keys()))
            else:
                cands = chain[last_word]
                cand_sum = 0
                for cand in cands:
                    cand_sum += cands[cand]
                dial = random.randrange(0, cand_sum)
                curr_sum = 0
                for cand in cands:
                    curr_sum += cands[cand]
                    if dial <= curr_sum:
                        new_word = cand
                        break
            res += new_word
            sent_chain += 1
            if random.random() > sentence_prob - 0.01 * sent_chain:
                last_word = None
                res += '. '
                sent_chain = 0
            else:
                last_word = new_word
                res += ' '
        res = res[:-1]
        res += '.'
        return res

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author is not None and message.author.id is not None and message.author.id != self.bot.user.id and message.guild is not None and message.channel is not None:
            if self.bot.server_data.can_random_scramble(message.channel):
                if random.random() < 0.0005:
                    async with message.context.typing():
                        scramb = await self.get_scramble(message.channel)
                    await message.context.send(scramb)


    @commands.command()
    @commands.guild_only()
    async def flexrole(self, ctx):
        """ Puts you at the top of the server list for a day so you can flex on everyone """

        flex_role = None
        server = ctx.message.guild
        flex_id = self.bot.server_data.get_flex_role_id(str(server.id))
        if flex_id is not None:
            flex_role = server.get_role(flex_id)

        if flex_role is None:
            return await ctx.send("There is no flex role configured for this server")

        try:
            shop = self.bot.get_cog('Shop')
            purchased = await shop.purchase(ctx)
            if not purchased:
                return
            await ctx.author.add_roles(flex_role)
            await ctx.send(f"Nice, flex on them **{ctx.author.display_name}**!")
            await asyncio.sleep(86400)
            await ctx.author.remove_roles(flex_role)
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Fun_Commands(bot))
