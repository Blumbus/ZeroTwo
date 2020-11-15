import random
import discord
import urllib
import secrets
import asyncio
import aiohttp
import re

from io import BytesIO

from discord import Member, Role
from discord.ext import commands
from utils import lists, permissions, http, default, argparser


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



def setup(bot):
    bot.add_cog(Fun_Commands(bot))
