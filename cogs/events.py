import math
import random

import discord
from discord.ext import tasks, commands
import os

from datetime import datetime

from discord.ext import commands
from discord.ext.commands import errors
from utils import default


class Events(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.config = default.get("config.json")

	@commands.Cog.listener()
	async def on_command_error(self, ctx, err):
		if isinstance(err, errors.MissingRequiredArgument) or isinstance(err, errors.BadArgument):
			helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
			await ctx.send_help(helper)

		elif isinstance(err, errors.CommandInvokeError):
			error = default.traceback_maker(err.original)

			if "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
				return await ctx.send(
					f"You attempted to make the command display more than 2,000 characters...\n"
					f"Both error and command will be ignored."
				)

			await ctx.send(f"There was an error processing the command ;-;\n{error}")

		elif isinstance(err, errors.CheckFailure):
			pass

		elif isinstance(err, errors.MaxConcurrencyReached):
			await ctx.send(f"You've reached max capacity of command usage at once, please finish the previous one...")

		elif isinstance(err, errors.CommandOnCooldown):
			await ctx.send(f"This command is on cooldown... try again in {err.retry_after:.2f} seconds.")

		elif isinstance(err, errors.CommandNotFound):
			pass

	@commands.Cog.listener()
	async def on_command(self, ctx):
		try:
			print(f"{ctx.guild.name} > {ctx.author} > {ctx.message.clean_content}")
		except AttributeError:
			print(f"Private message > {ctx.author} > {ctx.message.clean_content}")

	@commands.Cog.listener()
	async def on_ready(self):
		""" The function that actiavtes when boot was completed """
		self.bot.server_data.load_data()

		if not hasattr(self.bot, 'uptime'):
			self.bot.uptime = datetime.utcnow()

		# Indicate that the bot has successfully booted up
		print(f'Ready: {self.bot.user} | Servers: {len(self.bot.guilds)}')

		await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=">help"))

		self.autosave.start()

	@tasks.loop(seconds=60.0)
	async def autosave(self):
		self.bot.server_data.save_data()

	@commands.Cog.listener()
	async def on_member_join(self, member):
		server = member.guild
		print(server.id)
		if str(server.id) in self.bot.server_data.data['servers']:
			message = self.bot.server_data.get_join_message(str(server.id))
			print(message)
			if message.strip() != '':
				message = message.replace('%USER%', '<@' + str(member.id) + '>')
				channel = self.bot.server_data.get_home_channel(str(server.id))
				await channel.send(message)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		server = member.guild
		if str(server.id) in self.bot.server_data.data['servers']:
			message = self.bot.server_data.get_leave_message(str(server.id))
			if message.strip() != '':
				message = message.replace('%USER%', '<@' + str(member.id) + '>')
				channel = self.bot.server_data.get_home_channel(str(server.id))
				await channel.send(message)

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author is not None and message.author.id is not None and message.author.id != self.bot.user.id and message.guild is not None:
			user_id = str(message.author.id)
			server_id = str(message.guild.id)
			since = self.bot.server_data.time_since_active(server_id, user_id)
			xp = int(math.log((since + 5) / 5, since + 2) * 25)
			prev, post = self.bot.server_data.give_xp(server_id, user_id, xp)
			prev_coins, post_coins = self.bot.server_data.give_energy(server_id, user_id, int(xp / 2))
			self.bot.server_data.set_last_active(server_id, user_id)
			rank_xps = self.bot.server_data.get_rank_xps(server_id)
			for rank in rank_xps:
				if rank_xps[rank] <= post:
					# Award the rank
					role = message.guild.get_role(int(rank))
					if role is not None and role not in message.author.roles:
						await message.author.add_roles(role)
						await message.channel.send(
							f"**{message.author.name}** advanced to the **{role.name}** role!")

			if self.bot.server_data.can_random_scramble(message.channel):
				rand = random.random()
				if rand < 0.001:
					fun = self.bot.get_cog('Fun_Commands')
					scramb = await fun.get_scramble(message.channel)
					await message.channel.send(scramb)


def setup(bot):
	bot.add_cog(Events(bot))
