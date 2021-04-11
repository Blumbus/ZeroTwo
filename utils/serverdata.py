import datetime
import json
import discord
import shutil
from shutil import copy
from functools import reduce
import operator

from discord import client, Role

from utils import default


user_js = {
	"xp": 0,
	"energy": 0,
	"last_active": None
}

channel_js = {
	"words": [],
	"random_scramble": False,
	"allow_scramble": False
}

rank_js = {
	"xp": 99999999999
}

# Max activity time (in seconds)
MAX_TIME = 600


def json_converter(o):
	if isinstance(o, datetime.datetime):
		return None


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

	def try_update_user(self, server_id: str, user_id: str):
		if user_id not in self.data['servers'][server_id]['users']:
			self.data['servers'][server_id]['users'][user_id] = user_js.copy()
		else:
			for key in user_js:
				if key not in self.data['servers'][server_id]['users'][user_id]:
					if isinstance(user_js[key], bool):
						new_val = user_js[key]
					else:
						new_val = user_js[key].copy()
					self.data['servers'][server_id]['users'][user_id][key] = new_val

	def try_update_channel(self, server_id: str, channel_id: str):
		if 'channels' not in self.data['servers'][server_id]:
			self.data['servers'][server_id]['channels'] = {}
		if channel_id not in self.data['servers'][server_id]['channels']:
			self.data['servers'][server_id]['channels'][channel_id] = channel_js.copy()
		else:
			for key in channel_js:
				if key not in self.data['servers'][server_id]['channels'][channel_id]:
					if isinstance(channel_js[key], bool):
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

	def set_invite_link(self,server_id,invite_link:str):
		self.data['servers'][str(server_id)]["invite_link"] = invite_link

	def get_invite_link(self,server_id):
		return self.data['servers'][str(server_id)]["invite_link"]

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

	def set_placement(self,server_id: str,user_id: str, rank: int):
		self.try_update_user(server_id,user_id)
		self.data['servers'][server_id]['users'][user_id]['rank'] = rank

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

	def time_since_active(self, server_id: str, user_id: str):
		last = self.get_last_active(server_id, user_id)
		if last is None:
			return MAX_TIME
		now = datetime.datetime.now()
		diff = now - last
		secs = min(diff.total_seconds(), MAX_TIME)
		return secs

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
