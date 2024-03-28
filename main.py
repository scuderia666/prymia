import os
import signal
import asyncio
import functools

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

async def main():
	load_profiles()

	loop = asyncio.get_running_loop()
	loop.add_signal_handler(signal.SIGHUP, functools.partial(shutdown, loop))
	loop.add_signal_handler(signal.SIGTERM, functools.partial(shutdown, loop))

	for name, data in profiles.items():
		bots[name] = Bot()
		loop.create_task(bots[name].run(name, data))

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		print("Process interrupted")
	finally:
		for name, bot in bots.items():
			bot.save_data()

		loop.stop()

if __name__ == "__main__":
    asyncio.run(main())
