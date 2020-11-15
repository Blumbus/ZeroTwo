import datetime
import json
import shutil
from shutil import copy
from functools import reduce
import operator

from discord import client, Role

from utils import default


user_js = {
	"xp": 0,
	"coins": 0,
	"last_active": None
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
					self.data['servers'][server_id]['users'][user_id][key] = user_js[key].copy()

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

	def give_coins(self, server_id: str, user_id: str, coins: int):
		self.try_update_user(server_id, user_id)
		prev = self.data['servers'][server_id]['users'][user_id]['coins']
		post = prev + coins
		self.data['servers'][server_id]['users'][user_id]['coins'] = post
		return prev, post

	def get_coins(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		ret = self.data['servers'][server_id]['users'][user_id]['coins']
		return ret

	def set_last_active(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		self.data['servers'][server_id]['users'][user_id]['last_active'] = datetime.datetime.now()

	def get_last_active(self, server_id: str, user_id: str):
		self.try_update_user(server_id, user_id)
		return self.data['servers'][server_id]['users'][user_id]['last_active']

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
