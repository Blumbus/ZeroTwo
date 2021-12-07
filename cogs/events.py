import math
import random
import asyncio

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
	async def on_raw_reaction_add(self, reaction):
		server_id = reaction.guild_id
		if str(server_id) in self.bot.server_data.data['servers']:
			message_id = reaction.message_id
			user_id = reaction.user_id
			if user_id != self.bot.user.id:
				if message_id == self.bot.server_data.get_raffle_freebie_message_id(str(server_id)):
					if not self.bot.server_data.get_user_raffle_freebie(str(server_id), str(user_id)):
						self.bot.server_data.set_user_raffle_freebie(str(server_id), str(user_id), True)
						member = reaction.member
						if member is not None:
							new_amount = self.bot.server_data.get_user_raffle_amount(str(server_id), str(user_id))
							raffle_name = self.bot.server_data.get_raffle_name(str(server_id))
							await member.send(f"You successfully claimed your **{5}** freebie tickets! Your new amount for the *{raffle_name}* raffle is **{new_amount}**")
				elif message_id == self.bot.server_data.get_raffle_random_message_id(str(server_id)):
					if self.bot.server_data.get_user_last_react_id(str(server_id), str(user_id)) != message_id:
						num_tickets = self.bot.server_data.get_raffle_random_amount(str(server_id))
						self.bot.server_data.give_user_raffle_tickets(str(server_id), str(user_id), num_tickets)
						self.bot.server_data.set_user_last_react_id(str(server_id), str(user_id), message_id)
						member = reaction.member
						if member is not None:
							new_amount = self.bot.server_data.get_user_raffle_amount(str(server_id), str(user_id))
							raffle_name = self.bot.server_data.get_raffle_name(str(server_id))
							await member.send(f"You successfully claimed your **{num_tickets}** ticket{'' if num_tickets == 1 else 's'}! Your new amount for the *{raffle_name}* raffle is **{new_amount}**")

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
				if rand < 0.0005:
					fun = self.bot.get_cog('Fun_Commands')
					scramb = await fun.get_scramble(message.channel)
					await message.channel.send(scramb)

			if self.bot.server_data.get_raffle_active(server_id):
				rand = random.random()
				rarity = self.bot.server_data.get_raffle_rarity(server_id)
				if rand < rarity:
					await asyncio.sleep(random.randrange(30, 300))
					amount = 1
					if random.random() < 0.75:
						amount += 1
						if random.random() < 0.7:
							amount += 1
							if random.random() < 0.7:
								amount += 1
								if random.random() < 0.7:
									amount += 1
					text_options = [
						f"**{str(amount)}** raffle ticket{'' if amount == 1 else 's'} randomly fall{'s' if amount == 1 else ''} from the sky!",
						f"A passing van drops **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} on the ground!",
						f"A friendly crow lands next to you with **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} in its mouth!"
						f"You get hit by a truck and die. Your new isekai power is to gain **{str(amount)}** raffle ticket{'' if amount == 1 else 's'}!",
						f"You meet a friendly cat with **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} tucked into its collar!",
						f"A gust of wind blows **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} into your face!",
						f"You spot **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} caught in a tree's branches!",
						f"You save a cat that was stuck in a tree. Its owner rewards you with **{str(amount)}** raffle ticket{'' if amount == 1 else 's'}!",
						f"You spot **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} on the ground!",
						f"Mount Raffle has an enormous eruption, spraying raffle tickets everywhere! **10** of them fall in front of you!",
						f"A bottle washes ashore with **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} inside!",
						f"Your boss offers to pay you **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} instead of a living wage.",
						f"Everyone gets a stimulus check of **{str(amount)}** raffle ticket{'' if amount == 1 else 's'}!",
						f"An old pair of pants has **{str(amount)}** raffle ticket{'' if amount == 1 else 's'} in its pocket!",
					]
					pre = random.choice(text_options)
					if 'Mount Raffle' in pre:
						amount = 10
					text = f"{pre} React to this message within a minute to get {'it' if amount == 1 else 'them'}!"
					msg = await message.channel.send(text)
					self.bot.server_data.set_raffle_random_message_id(server_id, msg.id)
					self.bot.server_data.set_raffle_random_amount(server_id, amount)
					ticket_emoji = chr(0x1F39F)
					await msg.add_reaction(ticket_emoji)
					
					await asyncio.sleep(60)
					self.bot.server_data.set_raffle_random_message_id(server_id, 0)
					await msg.edit(content=(text + " *(This message has run out of time)*"))
					
					


def setup(bot):
	bot.add_cog(Events(bot))
