import os
import signal
import asyncio
import setproctitle
import psutil

from bot import Bot
from omegaconf import OmegaConf

import nest_asyncio
nest_asyncio.apply()

bots = {}
profiles = {}

def load_profiles():
	dir = os.listdir("profiles")

	for file in dir:
		profile_data = OmegaConf.load("profiles/" + file)
		profile_name = file.removesuffix('.yml')
		profiles[profile_name] = profile_data

def shutdown(loop):
	for task in asyncio.Task.all_tasks():
		task.cancel()

def is_process_running(name):
	for process in psutil.process_iter(['name']):
		if process.info['name'] == name:
			return True
	return False

async def main():
	load_profiles()

	loop = asyncio.get_event_loop()

	for name, data in profiles.items():
		bots[name] = Bot()
		loop.create_task(bots[name].run(name, data))

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		print("closing bots...")

		for name, bot in bots.items():
			await bot.close()

if __name__ == "__main__":
	if is_process_running('prymia'):
		print("already running")
	else:
		setproctitle.setproctitle('prymia')
		asyncio.run(main())
