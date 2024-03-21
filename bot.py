import os
import random
import asyncio
from omegaconf import OmegaConf

import discord
from PyCharacterAI import Client

class Bot:

	def __init__(self):
		self.data = {}
		self.chats = {}

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

		return str(answer.text)
	
	async def handle_message(self, message):
		if message.author.id == self.client.user.id:
			return

		if not message.channel.type is discord.ChannelType.private:
			return

		sender = message.author

		if not sender.bot:
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

		self.data = OmegaConf.load("data/" + self.name + ".yml")

		@self.client.event
		async def on_ready():
			print(self.name + " has started")

		@self.client.event
		async def on_message(message):
			await self.handle_message(message)

		self.client.run(profile["token"])
