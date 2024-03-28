import os
import re
import random
import asyncio
from omegaconf import OmegaConf

import discord
from PyCharacterAI import Client

class Bot:

	def __init__(self):
		self.data = {}
		self.sessions = {}
		self.chats = {}

	async def send_bot_guild_message(self, guild, channel, message):
		try:
			await channel.send(message)
		except discord.errors.Forbidden:
			return
		except discord.errors.CaptchaRequired:
			return
		except discord.errors.HTTPException as e:
			return

	async def ai_chat(self, sender, message):
		if sender.name not in self.data.keys():
			self.data[sender.name] = {}

		if "history_id" not in self.data[sender.name].keys():
			chat = await self.cai_client.create_chat(self.character_id)
			self.data[sender.name]["history_id"] = chat.history_id
			self.chats[sender.name] = chat

		if sender.name not in self.chats.keys():
			chat = await self.cai_client.continue_chat(self.data[sender.name]["history_id"])
			self.chats[sender.name] = chat

		answer = await self.chats[sender.name].send_message(message)

		answer2 = None

		if answer.text == None:
			message_id = answer.uuid
			while answer2 == None:
				new_message = await self.chats[sender.name].another_response(message_id)
				answer2 = new_message.text
			else:
				return answer2
		return answer.text

	async def fetch_user(self, id):
		try:
			return await self.client.fetch_user(id)
		except discord.errors.NotFound:
			return discord.errors.NotFound

	async def info(self, target, message):
		await target.send("[info] " + message)

	async def error(self, target, message):
		await target.send("[error] " + message)

	async def broadcast(self, message, exception = None):
		for name, user in self.sessions.items():
			if exception is not None and name == exception:
				continue
			await user.send(message)
		
	async def handle_message(self, message):
		if message.author.id == self.client.user.id:
			return

		sender = message.author

		if sender.bot:
			return

		if not message.channel.type is discord.ChannelType.private:
			if self.client.user.mentioned_in(message) and not sender.bot:
				msg = re.sub(r'<@!*&*[0-9]+>', '', message.content).strip()

				text = await self.ai_chat(sender, msg)
				await self.send_bot_guild_message(message.guild, message.channel, str(sender.mention) + " " + text)
			return

		if message.content[:1] == "!":
			content = message.content[1:].split(None, 1)
			cmd = content[0]

			args = []

			if len(content) == 2:
				args = content[1].split()

			if cmd == "login":
				if sender.name in self.sessions.keys():
					await self.error(sender, "you are already logged in.")
					return

				if len(args) < 1:
					await self.error(sender, "please provide a password.")
					return

				if args[0] == str(self.pin):
					self.sessions[sender.name] = sender

					await self.info(sender, "logged in successfully")
					await self.broadcast("[system] " + sender.name + " has logged in", sender.name)
				else:
					await self.error(sender, "wrong password")
			elif sender.name not in self.sessions.keys():
				await self.error(sender, "you are not logged in. please use !login <password> to login.")
				return

			if cmd == "logout":
				if sender.name not in self.sessions.keys():
					await self.error(sender, "you are not logged in.")
					return

				self.sessions.pop(sender.name)
	
				await self.info(sender, "you are successfully logged out")
				await self.broadcast("[system] " + sender.name + " has logged out", sender.name)

			if cmd == "frq":
				if len(args) < 1:
					await self.error(sender, "specify an id")
					return

				id = int(args[0])
				target = await self.fetch_user(id)
				if target == None:
					return

				await self.client.send_friend_request(target)
				await self.broadcast("[system] <" + sender.name + "> friend request has been successfully sent to " + target.name)

			if cmd == "msg":
				if len(args) < 1:
					await self.error(sender, "specify an id")
					return

				if len(args) < 2:
					await self.error(sender, "specify a message")
					return

				id = int(args[0])
				target = await self.fetch_user(id)
				if target == None:
					return

				await target.send(args[1])

			if cmd == "say":
				if len(args) < 1:
					await self.error(sender, "specify an id")
					return

				if len(args) < 2:
					await self.error(sender, "specify a message")
					return

				id = int(args[0])
				target = await self.fetch_user(id)
				if target == None:
					return

				await target.send(await self.ai_chat(target, args[1]))
		else:
			await message.channel.send(await self.ai_chat(sender, message.content))

	def save_data(self):
			with open("data/" + self.name + ".yml", 'w') as fp:
				OmegaConf.save(config=self.data, f=fp.name)

	async def run(self, name, profile):
		self.name = name
		self.client = discord.Client()
		self.pin = random.randint(999, 9999)

		print("starting " + self.name + " with pin " + str(self.pin))

		self.character_id = profile["character_id"]

		self.cai_client = Client()
		await self.cai_client.authenticate_with_token(os.getenv('CAI_TOKEN'))

		if not os.path.exists("data/" + self.name + ".yml"):
			self.save_data()

		self.data = OmegaConf.load("data/" + self.name + ".yml")

		@self.client.event
		async def on_ready():
			print(self.name + " has started")

		@self.client.event
		async def on_message(message):
			await self.handle_message(message)

		self.client.run(profile["token"], log_handler=None)
