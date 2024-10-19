import asyncio
from homeassistant.core import HomeAssistant

from .config import Config
from .data_collector import DataCollector
from .sound_generator import SoundGenerator
from .audio_output import AudioOutput
from .web_interface import WebInterface

class ZenAssistant:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.config = Config()
        self.data_collector = DataCollector(self.hass, self.config)
        self.sound_generator = SoundGenerator(self.config)
        self.audio_output = AudioOutput(self.config)
        self.web_interface = WebInterface(self.hass, self.config)

    async def start(self):
        await self.config.load()
        await self.web_interface.start()
        asyncio.create_task(self.run())

    async def run(self):
        while True:
            data = await self.data_collector.collect()
            sound = await self.sound_generator.generate(data)
            await self.audio_output.play(sound)
            await asyncio.sleep(self.config.update_interval)

    async def stop(self):
        await self.web_interface.stop()
        await self.audio_output.stop()

async def setup(hass: HomeAssistant):
    zen = ZenAssistant(hass)
    await zen.start()
    return True
