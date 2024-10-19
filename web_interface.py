from aiohttp import web
import voluptuous as vol
from homeassistant.components.http import HomeAssistantView
import json

class ZenAssistantView(HomeAssistantView):
    url = "/api/zen_assistant"
    name = "api:zen_assistant"
    requires_auth = True

    def __init__(self, zen_assistant):
        self.zen_assistant = zen_assistant

    @staticmethod
    def _boolean_validator(value):
        return value.lower() in ('true', 'yes', 'on', 'y', '1')

    async def get(self, request):
        """Handle GET requests."""
        return web.json_response({
            "config": self.zen_assistant.config.get_all(),
            "available_entities": await self.zen_assistant.data_collector.get_available_entities(),
            "available_output_devices": await self.zen_assistant.audio_output.get_available_output_devices(),
            "available_media_players": await self.zen_assistant.audio_output.get_available_media_players()
        })

    async def post(self, request):
        """Handle POST requests."""
        data = await request.json()
        
        schema = vol.Schema({
            vol.Optional('data_sources'): {
                vol.Optional('traffic'): str,
                vol.Optional('energy'): str,
                vol.Optional('weather'): str,
                vol.Optional('custom'): [
                    {
                        'entity_id': str,
                        'name': str,
                        vol.Optional('min'): float,
                        vol.Optional('max'): float
                    }
                ]
            },
            vol.Optional('audio_output'): {
                'type': vol.In(['local', 'media_player']),
                vol.Optional('device_index'): int,
                vol.Optional('media_player_entity_id'): str
            },
            vol.Optional('sounds'): {
                vol.Optional('cricket'): str,
                vol.Optional('bird'): str,
                vol.Optional('wave'): str
            },
            vol.Optional('update_interval'): int
        })

        try:
            config = schema(data)
        except vol.Invalid as e:
            return web.json_response({"error": str(e)}, status=400)

        # Update configuration
        await self.zen_assistant.config.update(config)
        
        # Restart components with new configuration
        await self.zen_assistant.restart()

        return web.json_response({"status": "ok"})

class WebInterface:
    def __init__(self, hass, zen_assistant):
        self.hass = hass
        self.zen_assistant = zen_assistant
        self.view = ZenAssistantView(zen_assistant)

    async def start(self):
        self.hass.http.register_view(self.view)
        
    async def stop(self):
        # If needed, perform cleanup here
        pass

# Main ZenAssistant class (updated to include WebInterface)
class ZenAssistant:
    def __init__(self, hass):
        self.hass = hass
        self.config = Config()
        self.data_collector = DataCollector(self.hass, self.config)
        self.sound_generator = SoundGenerator(self.config)
        self.audio_output = AudioOutput(self.hass, self.config)
        self.web_interface = WebInterface(self.hass, self)

    async def start(self):
        await self.config.load()
        await self.data_collector.setup()
        await self.audio_output.setup()
        await self.web_interface.start()
        asyncio.create_task(self.run())

    async def run(self):
        while True:
            data = await self.data_collector.collect()
            sound = await self.sound_generator.generate(data)
            await self.audio_output.play(sound)
            await asyncio.sleep(self.config.get('update_interval', 60))

    async def stop(self):
        await self.web_interface.stop()
        await self.audio_output.stop()

    async def restart(self):
        await self.stop()
        await self.start()

# Setup function for Home Assistant
async def setup(hass):
    zen = ZenAssistant(hass)
    await zen.start()
    return True
