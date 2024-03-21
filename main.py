import os
import signal
import asyncio

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

def main():
	def sigterm_handler(_signo, _stack_frame):
		sys.exit(0)

	signal.signal(signal.SIGTERM, sigterm_handler)

	load_profiles()

	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

	for name, data in profiles.items():
		bots[name] = Bot()
		loop.create_task(bots[name].run(name, data))

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass
	finally:
		for name, bot in bots.items():
			bot.save_data()

		loop.stop()

main()
