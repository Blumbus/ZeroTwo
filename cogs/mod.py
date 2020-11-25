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
    async def lock(self, ctx):
        """ Locks the current channel """

        lock_emoji = chr(0x1F512)
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"{lock_emoji} This channel is now locked! {lock_emoji}")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def unlock(self, ctx):
        """ Unlocks the current channel """

        lock_emoji = chr(0x1F513)
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send(f"{lock_emoji} This channel is now unlocked! {lock_emoji}")

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

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setflexrole(self, ctx, role_id: int):
        """ Sets the flex role id for the current server """

        self.bot.server_data.set_flex_role_id(str(ctx.message.guild.id), role_id)
        role = ctx.message.guild.get_role(role_id)
        if role is None:
            await ctx.send(f"Set the flex role id to {str(role_id)} (No corresponding role!)")
        else:
            await ctx.send(f"Set the flex role id to {str(role_id)} (role **{role.name}**)")

    def get_server_path(self, server: discord.Guild):
        return "servers." + str(server.id)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setrankxp(self, ctx, xp: int, *, role: Role):
        """ Sets the required xp to reach a rank  """

        self.bot.server_data.set_rank_xp(str(ctx.message.guild.id), role, xp)
        await ctx.send(f"Set xp requirement for **{role.name}** to **{str(xp)}**")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def enablescramble(self, ctx, enabled: bool = True):
        """ Allows scrambling of/in this channel. Use enablescramble false to disable """

        self.bot.server_data.enable_scramble(str(ctx.message.guild.id), str(ctx.message.channel.id), enabled)
        set_string = 'Enabled'
        if not enabled:
            set_string = 'Disabled'
        await ctx.send(f"{set_string} scramble permissions for this channel")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setshopprice(self, ctx, name: str, price: int):
        """ Sets the price of a shop item  """

        self.bot.server_data.set_shop_price(str(ctx.message.guild.id), name, price)
        await ctx.send(f"Set price for **{name}** to **{str(price)}**")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def giveuserenergy(self, ctx, user: discord.User, energy: int):
        """ Adds energy to a user's total balance  """

        prev, post = self.bot.server_data.give_energy(str(ctx.message.guild.id), str(user.id), energy)
        await ctx.send(f"Updated **{user.display_name}**'s magma energy from **{str(prev)}** to **{str(post)}**")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setuserenergy(self, ctx, user: discord.User, energy: int):
        """ Sets a user's energy  """

        self.bot.server_data.set_energy(str(ctx.message.guild.id), str(user.id), energy)
        await ctx.send(f"Updated **{user.display_name}**'s magma energy to **{str(energy)}**")


def setup(bot):
    bot.add_cog(Moderator(bot))
