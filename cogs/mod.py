import discord
import re
import asyncio

from discord import Role
from discord.ext import commands
from utils import default, permissions


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            return m.id


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = argument

        if len(ret) > 512:
            reason_max = 512 - len(ret) - len(argument)
            raise commands.BadArgument(f'reason is too long ({len(argument)}/{reason_max})')
        return ret


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """ Kicks a user from the current server. """
        if await permissions.check_priv(ctx, member):
            return

        try:
            await member.kick(reason=default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("kicked"))
        except Exception as e:
            await ctx.send(e)

    @commands.command(aliases=["nick"])
    @commands.guild_only()
    @permissions.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, name: str = None):
        """ Nicknames a user from the current server. """
        if await permissions.check_priv(ctx, member):
            return

        try:
            await member.edit(nick=name, reason=default.responsible(ctx.author, "Changed by command"))
            message = f"Changed **{member.name}'s** nickname to **{name}**"
            if name is None:
                message = f"Reset **{member.name}'s** nickname"
            await ctx.send(message)
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberID, *, reason: str = None):
        """ Bans a user from the current server. """
        m = ctx.guild.get_member(member)
        if m is not None and await permissions.check_priv(ctx, m):
            return

        try:
            await ctx.guild.ban(discord.Object(id=member), reason=default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("banned"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    async def unban(self, ctx, member: MemberID, *, reason: str = None):
        """ Unbans a user from the current server. """
        try:
            await ctx.guild.unban(discord.Object(id=member), reason=default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("unbanned"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """ Mutes a user from the current server. """
        if await permissions.check_priv(ctx, member):
            return

        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"), None)

        if not muted_role:
            return await ctx.send("Are you sure you've made a role called **Muted**? Remember that it's case sensetive too...")

        try:
            await member.add_roles(muted_role, reason=default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("muted"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        """ Unmutes a user from the current server. """
        if await permissions.check_priv(ctx, member):
            return

        muted_role = next((g for g in ctx.guild.roles if g.name == "Muted"), None)

        if not muted_role:
            return await ctx.send("Are you sure you've made a role called **Muted**? Remember that it's case sensetive too...")

        try:
            await member.remove_roles(muted_role, reason=default.responsible(ctx.author, reason))
            await ctx.send(default.actionmessage("unmuted"))
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def sethomechannel(self, ctx):
        """ Sets the default (greet) channel to the current channel """

        self.bot.server_data.set_home_channel(str(ctx.message.guild.id), ctx.message.channel.id)
        await ctx.send(f"Set the default channel to **{ctx.message.channel.name}**")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setjoinmessage(self, ctx, *, message: str):
        """ Sets the join message for the server (use %USER% for user name, or "none" for no message) """

        self.bot.server_data.set_join_message(str(ctx.message.guild.id), message)
        await ctx.send(f"Set the join message to \"{message.replace('%USER%', 'Username')}\"")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setleavemessage(self, ctx, *, message: str):
        """ Sets the leave message for the server (use %USER% for user name, or "none" for no message) """

        self.bot.server_data.set_leave_message(str(ctx.message.guild.id), message)
        await ctx.send(f"Set the leave message to \"{message.replace('%USER%', 'Username')}\"")

    def get_server_path(self, server: discord.Guild):
        return "servers." + str(server.id)

    @commands.command()
    @permissions.has_permissions(manage_roles=True)
    async def setdatavalue(self, ctx, path: str, *, value: str):
        """ Sets a specific value in the serverdata ex: servers.777102021425233932.name 'cool server'
            the value is evaluated as python code """

        if ctx.message.guild != None:
            path = path.replace('%SERVER%', self.get_server_path(ctx.message.guild))
        try:
            ob = eval(value)
        except (SyntaxError, NameError):
            await ctx.send(f"Could not evaluate {value}")
        else:
            self.bot.server_data.set_data_value(path, ob)
            await ctx.send(f"Updated value at {path} to {value}")

    @commands.command()
    @permissions.has_permissions(manage_roles=True)
    async def deletedatakey(self, ctx, path: str):
        """ Deletes a specific value in the serverdata ex: 777102021425233932.users.85931152363249664 removes that user """

        if ctx.message.guild != None:
            path = path.replace('%SERVER%', self.get_server_path(ctx.message.guild))
        self.bot.server_data.delete_data_key(path)
        await ctx.send(f"Deleted key at {path}")

    @commands.command()
    @permissions.has_permissions(manage_roles=True)
    async def savedata(self, ctx):
        """ Saves all server data to disk """

        await ctx.send("Saving server data...")
        try:
            self.bot.server_data.save_data()
        except Exception as e:
            await ctx.send("Unable to save data, keeping original data file")
            raise e
        else:
            await ctx.send("Saved data for all servers")

    @commands.command()
    @permissions.has_permissions(manage_roles=True)
    async def getdata(self, ctx):
        """ First saves all data, then DMs a copy of the JSON """

        try:
            await self.savedata(ctx)
        except Exception as e:
            raise e
        else:
            with open('serverdata.json', 'rb') as outfile:
                await ctx.message.author.send(file=discord.File(outfile, 'serverdata.json'))
                await ctx.message.add_reaction(chr(0x2709))


    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setrankxp(self, ctx, xp: int, *, role: Role):
        """ Sets the required xp to reach a rank  """

        self.bot.server_data.set_rank_xp(str(ctx.message.guild.id), role, xp)
        await ctx.send(f"Set xp requirement for **{role.name}** to **{str(xp)}**")


def setup(bot):
    bot.add_cog(Moderator(bot))
