import discord
import re
import asyncio
import random

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
    async def enablerandomscramble(self, ctx, enabled: bool = True):
        """ Allows occasional random scrambles in this channel. Use enablerandomscramble false to disable """

        self.bot.server_data.enable_random_scramble(str(ctx.message.guild.id), str(ctx.message.channel.id), enabled)
        set_string = 'Enabled'
        if not enabled:
            set_string = 'Disabled'
        await ctx.send(f"{set_string} random scrambles for this channel")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setinvitelink(self, ctx, invite_link: str):
        """ Set the invite link the bot should use for the server """

        self.bot.server_data.set_invite_link(str(ctx.message.guild.id), invite_link)
        await ctx.send(f"Set this server's invite link to {invite_link}")

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

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def startraffle(self, ctx, *, raffle_name: str):
        """ Starts a new raffle in the current server (This will ERASE any current raffle data!)  """

        self.bot.server_data.clear_raffle_userdata(str(ctx.message.guild.id))
        self.bot.server_data.set_raffle_active(str(ctx.message.guild.id), True)
        self.bot.server_data.set_raffle_name(str(ctx.message.guild.id), raffle_name)
        await ctx.send(f"**{raffle_name}** raffle has started!!")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setrafflefreebieid(self, ctx, freebie_message_id: int):
        """ Sets the raffle's freebie react message  """

        self.bot.server_data.set_raffle_freebie_message_id(str(ctx.message.guild.id), freebie_message_id)
        await ctx.send(f"Set the raffle's freebie message to id {freebie_message_id}")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def setrafflerarity(self, ctx, raffle_rarity: float):
        """ Sets the rarity of a random raffle message in the current server  """

        self.bot.server_data.set_raffle_rarity(str(ctx.message.guild.id), raffle_rarity)
        await ctx.send(f"Set the raffle's random message rarity to {raffle_rarity}")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def rafflewinner(self, ctx):
        """ Picks a random winner for the active raffle  """

        raffle_map = self.bot.server_data.get_raffle_map(str(ctx.message.guild.id))
        total = 0
        for user_id in raffle_map:
            total += raffle_map[user_id]
        windex = random.randrange(1, total)
        sum = 0
        winner_id = ""
        for user_id in raffle_map:
            sum += raffle_map[user_id]
            if windex <= sum:
                winner_id = user_id
                break

        await ctx.send(f"The raffle winner is <@{winner_id}>!!!")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    async def stopraffle(self, ctx):
        """ Stops the active raffle in the current server  """

        self.bot.server_data.set_raffle_active(str(ctx.message.guild.id), False)
        raffle_name = self.bot.server_data.get_raffle_name(str(ctx.message.guild.id))
        await ctx.send(f"**{raffle_name}** raffle has closed! Please wait for the winners to be drawn!")


def setup(bot):
    bot.add_cog(Moderator(bot))
