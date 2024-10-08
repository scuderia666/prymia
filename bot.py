import os
import re
import random
import asyncio
from omegaconf import OmegaConf
import logging

logging.basicConfig(level=logging.INFO)

import discord
from PyCharacterAI import Client

class Bot:

	def __init__(self):
		self.data = {}
		self.sessions = {}
		self.chats = {}

	async def send_guild_message(self, guild, channel, message):
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

		if "chat_id" not in self.data[sender.name].keys():
			chat, _ = await self.cai_client.chat.create_chat(self.character_id, False)
			self.data[sender.name]["chat_id"] = chat.chat_id
			self.chats[sender.name] = chat

		if sender.name not in self.chats.keys():
			chat = await self.cai_client.chat.fetch_chat(self.data[sender.name]["chat_id"])
			self.chats[sender.name] = chat

		request = await self.cai_client.chat.send_message(self.character_id, self.chats[sender.name].chat_id, message)
		answer = request.get_primary_candidate()

		answer2 = None

		if answer.is_filtered == True:
			message_id = answer.turn_id
			while answer2.is_filtered == False:
				new_request = await self.cai_client.chat.another_response(self.character_id, self.chats[sender.name].chat_id, message_id)
				answer2 = new_request.get_primary_candidate()
			else:
				return answer2.text
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

		# ghost alitura
		if str(sender.id) == "582694915733979149":
			return

		if not message.channel.type is discord.ChannelType.private:
			if self.client.user.mentioned_in(message) and not "@everyone" in message.content and not "@here" in message.content and not sender.bot:
				msg = re.sub(r'<@!*&*[0-9]+>', '', message.content).strip()

				if msg == '':
					msg = self.client.user.display_name

				text = await self.ai_chat(sender, msg)

				array = text.split("\n")

				index = 0

				for line in array:
					if line == "":
						continue
					async with message.channel.typing():
						await asyncio.sleep(2)
					if index == 0:
						await message.reply(line)
					else:
						await self.send_guild_message(message.guild, message.channel, line)
					index += 1
			return

		if message.content[:1] == "!":
			body = message.content[1:].split(None, 1)

			if body == "":
				return

			cmd = body[0]

			content = ""
			args = []

			if len(body) == 2:
				content = body[1]
				args = content.split()

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
				await self.error(sender, "you are not logged in. please use !login <pin> to login.")
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
				if content != "":
					args = content.split(None, 1)

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
				if content != "":
					args = content.split(None, 1)
				
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

			if cmd == "chmsg":
				if content != "":
					args = content.split(None, 2)

				if len(args) < 1:
					await self.error(sender, "specify a server id")
					return

				if len(args) < 2:
					await self.error(sender, "specify a channel id")
					return

				if len(args) < 3:
					await self.error(sender, "specify message")
					return

				guild_id = int(args[0])
				channel_id = int(args[1])
				message = args[2]
				
				guild = self.client.get_guild(guild_id)
				channel = guild.get_channel(channel_id)

				await self.send_guild_message(guild, channel, message)
		elif sender.name in self.sessions.keys():
			await self.broadcast("[chat] " + sender.name + ": " + message.content, sender.name)
		else:
			text = await self.ai_chat(sender, message.content)

			array = text.split("\n")

			for line in array:
				if line == "":
					continue
				async with message.channel.typing():
					await asyncio.sleep(2)
				await message.channel.send(line)

	def save_data(self):
			with open("data/" + self.name + ".yml", 'w') as fp:
				OmegaConf.save(config=self.data, f=fp.name)

	async def close(self):
		self.save_data()
		await self.client.close()

	async def run(self, name, profile):
		self.name = name
		self.client = discord.Client()
		self.pin = random.randint(999, 9999)

		self.character_id = profile["character_id"]
		
		token = os.getenv('CAI_TOKEN')
		print("cai token: " + token)

		self.cai_client = Client()
		await self.cai_client.authenticate(token)

		me = await self.cai_client.account.fetch_me()
		print(f"Authenticated as @{me.username}")

		if not os.path.exists("data/" + self.name + ".yml"):
			self.save_data()

		self.data = OmegaConf.load("data/" + self.name + ".yml")

		@self.client.event
		async def on_ready():
			print(self.name + " has started with pin " + str(self.pin))

		@self.client.event
		async def on_message(message):
			await self.handle_message(message)

		await self.client.start(profile["token"])
