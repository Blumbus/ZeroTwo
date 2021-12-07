import datetime
import json
import discord
import shutil
from shutil import copy
from functools import reduce
import operator

import typing
from discord import client, Role

from utils import default


server_js = {
	"name": "",
	"main_channel": 0,
	"join_message": "",
	"leave_message": "",
	"raffle_active": False,
	"raffle_name": "",
	"raffle_rarity": 0.002,
	"raffle_random_message_id": 0,
	"raffle_random_amount": 1,
	"raffle_freebie_message_id": 0,
	"users": {},
	"shop": {},
	"ranks": {},
	"channels": {},
	"flex_role": 0
}

user_js = {
	"xp": 0,
	"energy": 0,
	"last_active": None,
	"raffle_freebie": False,
	"raffle_tickets": 0,
	"last_react_id": 0
}

channel_js = {
	"words": [],
	"random_scramble": False,
	"allow_scramble": False,
	"normal_name": ""
}

rank_js = {
	"xp": 99999999999
}

# Max activity time (in seconds)
MAX_TIME = 600


def json_converter(o):
	if isinstance(o, datetime.datetime):
		return None


class User:
	def __init__(self, user_id, xp, energy):
		self.user_id = user_id
		self.xp = xp
		self.energy = energy


class ServerData:
	def __init__(self, bot):
		self.bot = bot
		self.data = None

	def load_data(self):
		self.data = default.get_json('serverdata.json')

	def save_data(self):
		try:
			with open('serverdata_staging.json', 'w') as outfile:
				json.dump(self.data, outfile, indent=2, default=json_converter)
		except Exception as e:
			print("ERROR: Unable to save data, keeping original data file")
			raise e
		else:
			shutil.copyfile('serverdata_staging.json', 'serverdata.json')

	def try_update_server(self, server_id: str):
		if 'servers' not in self.data:
			self.data['servers'] = {}
		if server_id not in self.data['servers']:
			self.data['servers'][server_id] = server_js.copy()
		else:
			for key in server_js:
				if key not in self.data['servers'][server_id]:
					if isinstance(server_js[key], bool) or isinstance(server_js[key], int) or isinstance(server_js[key], str) or isinstance(server_js[key], float):
						new_val = server_js[key]
					else:
						new_val = server_js[key].copy()
					self.data['servers'][server_id][key] = new_val

	def try_update_user(self, server_id: str, user_id: str):
		self.try_update_server(server_id)
		if user_id not in self.data['servers'][server_id]['users']:
			self.data['servers'][server_id]['users'][user_id] = user_js.copy()
		else:
			for key in user_js:
				if key not in self.data['servers'][server_id]['users'][user_id]:
					if isinstance(user_js[key], bool) or isinstance(user_js[key], int) or isinstance(user_js[key], str) or isinstance(server_js[key], float):
						new_val = user_js[key]
					else:
						new_val = user_js[key].copy()
					self.data['servers'][server_id]['users'][user_id][key] = new_val

	def try_update_channel(self, server_id: str, channel_id: str):
		self.try_update_server(server_id)
		if 'channels' not in self.data['servers'][server_id]:
			self.data['servers'][server_id]['channels'] = {}
		if channel_id not in self.data['servers'][server_id]['channels']:
			self.data['servers'][server_id]['channels'][channel_id] = channel_js.copy()
		else:
			for key in channel_js:
				if key not in self.data['servers'][server_id]['channels'][channel_id]:
					if isinstance(channel_js[key], bool) or isinstance(channel_js[key], int) or isinstance(channel_js[key], str) or isinstance(server_js[key], float):
						new_val = channel_js[key]
					else:
						new_val = channel_js[key].copy()
					self.data['servers'][server_id]['channels'][channel_id][key] = new_val

	def set_data_value(self, path: str, value):
		keys = path.split('.')
		tempdic = self.data
		for key in keys[:-1]:
			tempdic = tempdic.setdefault(key, {})
		tempdic[keys[-1]] = value

	def delete_data_key(self, path: str):
		keys = path.split('.')
		tempdic = self.data
		for key in keys[:-1]:
			tempdic = tempdic.setdefault(key, {})
		del tempdic[keys[-1]]

	def set_home_channel(self, server_id: str, channel_id):
		self.data['servers'][str(server_id)]['main_channel'] = channel_id

	def get_home_channel(self, server_id):
		home_id = self.data['servers'][str(server_id)]['main_channel']
		ret = self.bot.get_channel(id=home_id)
		return ret

	def set_join_message(self, server_id, message: str):
		if message.lower() == 'none':
			message = ''
		self.data['servers'][str(server_id)]['join_message'] = message

	def get_join_message(self, server_id):
		ret = self.data['servers'][str(server_id)]['join_message']
		return ret

	def set_leave_message(self, server_id, message: str):
		if message.lower() == 'none':
			message = ''
		self.data['servers'][str(server_id)]['leave_message'] = message

	def get_leave_message(self, server_id):
		ret = self.data['servers'][str(server_id)]['leave_message']
		return ret

	def try_update_rank(self, server_id: str, role_id: str):
		if role_id not in self.data['servers'][server_id]['ranks']:

			self.data['servers'][server_id]['ranks'][role_id] = rank_js.copy()
		else:
			for key in rank_js:
				if key not in self.data['servers'][server_id]['ranks'][role_id]:
					self.data['servers'][server_id]['ranks'][role_id][key] = rank_js[key]

	def set_rank_xp(self, server_id: str, role: Role, xp: int):
		self.set_rank_id_xp(server_id, str(role.id), xp)

	def set_rank_id_xp(self, server_id: str, role_id: str, xp: int):
		self.try_update_rank(server_id, role_id)
		self.data['servers'][server_id]['ranks'][role_id]['xp'] = xp

	def give_xp(self, server_id: str, user_id: str, xp: int):
		self.try_update_user(server_id, user_id)
		prev = self.data['servers'][server_id]['users'][user_id]['xp']
		post = prev + xp
		self.data['servers'][server_id]['users'][user_id]['xp'] = post
		return prev, post

	def get_xp(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		ret = self.data['servers'][server_id]['users'][user_id]['xp']
		return ret

	def give_energy(self, server_id: str, user_id: str, energy: int):
		self.try_update_user(server_id, user_id)
		prev = self.data['servers'][server_id]['users'][user_id]['energy']
		post = prev + energy
		self.data['servers'][server_id]['users'][user_id]['energy'] = post
		return prev, post

	def get_energy(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		ret = self.data['servers'][server_id]['users'][user_id]['energy']
		return ret

	def set_energy(self, server_id: str, user_id: str, energy: int):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['energy'] = energy

	def set_last_active(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['last_active'] = datetime.datetime.now()

	def get_last_active(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		return self.data['servers'][server_id]['users'][user_id]['last_active']

	def enable_scramble(self, server_id: str, channel_id: str, enabled: bool):
		self.try_update_channel(server_id, channel_id)
		self.data['servers'][server_id]['channels'][channel_id]['allow_scramble'] = enabled

	def enable_random_scramble(self, server_id: str, channel_id: str, enabled: bool):
		self.try_update_channel(server_id, channel_id)
		self.data['servers'][server_id]['channels'][channel_id]['random_scramble'] = enabled

	def get_normal_name(self, server_id: str, channel_id: str):
		self.try_update_channel(server_id, channel_id)
		return self.data['servers'][server_id]['channels'][channel_id]['normal_name']

	def set_normal_name(self, server_id: str, channel_id: str, normal_name: str):
		self.try_update_channel(server_id, channel_id)
		self.data['servers'][server_id]['channels'][channel_id]['normal_name'] = str(normal_name)
		print(normal_name)

	def get_shop_price(self, server_id: str, name: str):
		if name not in self.data['servers'][server_id]['shop']:
			return 0
		return self.data['servers'][server_id]['shop'][name]

	def set_shop_price(self, server_id: str, name: str, price: int):
		self.data['servers'][server_id]['shop'][name] = price

	def get_flex_role_id(self, server_id: str):
		if 'flex_role' not in self.data['servers'][server_id]:
			return None
		return self.data['servers'][server_id]['flex_role']

	def set_flex_role_id(self, server_id: str, role_id: str):
		self.data['servers'][server_id]['flex_role'] = role_id

	def get_invite_link(self, server_id: str):
		if 'invite_link' not in self.data['servers'][server_id]:
			return None
		return self.data['servers'][server_id]['invite_link']

	def set_invite_link(self, server_id: str, invite_link: str):
		self.data['servers'][server_id]['invite_link'] = invite_link

	def set_raffle_active(self, server_id: str, is_active: bool):
		self.data['servers'][server_id]['raffle_active'] = is_active

	def get_raffle_active(self, server_id: str):
		return self.data['servers'][server_id]['raffle_active']

	def set_raffle_name(self, server_id: str, raffle_name: str):
		self.data['servers'][server_id]['raffle_name'] = raffle_name

	def get_raffle_name(self, server_id: str):
		return self.data['servers'][server_id]['raffle_name']

	def set_raffle_random_message_id(self, server_id: str, message_id: int):
		self.data['servers'][server_id]['raffle_random_message_id'] = message_id

	def get_raffle_random_message_id(self, server_id: str):
		return self.data['servers'][server_id]['raffle_random_message_id']

	def set_raffle_rarity(self, server_id: str, rarity: float):
		self.data['servers'][server_id]['raffle_rarity'] = rarity

	def get_raffle_rarity(self, server_id: str):
		return self.data['servers'][server_id]['raffle_rarity']

	def set_raffle_random_amount(self, server_id: str, amount: int):
		self.data['servers'][server_id]['raffle_random_amount'] = amount

	def get_raffle_random_amount(self, server_id: str):
		return self.data['servers'][server_id]['raffle_random_amount']

	def set_raffle_freebie_message_id(self, server_id: str, message_id: int):
		self.data['servers'][server_id]['raffle_freebie_message_id'] = message_id

	def get_raffle_freebie_message_id(self, server_id: str):
		return self.data['servers'][server_id]['raffle_freebie_message_id']

	def clear_raffle_userdata(self, server_id: str):
		users = self.data['servers'][server_id]['users']
		for user_id in users:
			if 'raffle_freebie' in self.data['servers'][server_id]['users'][user_id]:
				self.data['servers'][server_id]['users'][user_id]['raffle_freebie'] = False
			if 'raffle_freebie' in self.data['servers'][server_id]['users'][user_id]:
				self.data['servers'][server_id]['users'][user_id]['raffle_tickets'] = 0

	def set_user_raffle_freebie(self, server_id: str, user_id: str, has_freebie: bool):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['raffle_freebie'] = has_freebie

	def get_user_raffle_freebie(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		return self.data['servers'][server_id]['users'][user_id]['raffle_freebie']

	def give_user_raffle_tickets(self, server_id: str, user_id: str, num_tickets: int):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['raffle_tickets'] += num_tickets

	def set_user_last_react_id(self, server_id: str, user_id: str, react_id: int):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['last_react_id'] = react_id

	def get_user_last_react_id(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		return self.data['servers'][server_id]['users'][user_id]['last_react_id']

	def get_raffle_map(self, server_id: str):
		raffle_map = {}
		users = self.data['servers'][server_id]['users']
		for user_id in users:
			raffle_map[user_id] = self.get_user_raffle_amount(server_id, user_id)
		return raffle_map

	def get_user_raffle_amount(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		return (5 if self.data['servers'][server_id]['users'][user_id]['raffle_freebie'] else 0) + self.data['servers'][server_id]['users'][user_id]['raffle_tickets']

	def time_since_active(self, server_id: str, user_id: str):
		last = self.get_last_active(server_id, user_id)
		if last is None:
			return MAX_TIME
		now = datetime.datetime.now()
		diff = now - last
		secs = min(diff.total_seconds(), MAX_TIME)
		return secs

	def get_users(self, server_id: str) -> typing.List[User]:
		users = []
		for user in self.data['servers'][server_id]['users']:
			xp = self.data['servers'][server_id]['users'][user]['xp']
			energy = self.data['servers'][server_id]['users'][user]['energy']
			users.append(User(user, xp, energy))
		return users

	def get_rank_xps(self, server_id):
		ret = {}
		for rank in self.data['servers'][server_id]['ranks']:
			ret[rank] = self.data['servers'][server_id]['ranks'][rank]["xp"]
		return ret

	def allowed_scramble(self, channel: discord.TextChannel):
		if str(channel.id) not in self.data['servers'][str(channel.guild.id)]['channels']:
			return False
		chan_data = self.data['servers'][str(channel.guild.id)]['channels'][str(channel.id)]
		if 'allow_scramble' not in chan_data or chan_data['allow_scramble'] is not True:
			return False
		return True

	def can_random_scramble(self, channel: discord.TextChannel):
		if str(channel.id) not in self.data['servers'][str(channel.guild.id)]['channels']:
			return False
		chan_data = self.data['servers'][str(channel.guild.id)]['channels'][str(channel.id)]
		if 'random_scramble' not in chan_data or chan_data['random_scramble'] is not True:
			return False
		return True

