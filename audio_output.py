import asyncio
import pyaudio
import numpy as np
from pydub import AudioSegment
from homeassistant.components import media_player

class AudioOutput:
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        self.is_playing = False

    async def setup(self):
        output_type = self.config.get('audio_output.type', 'local')
        if output_type == 'local':
            self._setup_local_audio()
        elif output_type == 'media_player':
            await self._setup_media_player()

    def _setup_local_audio(self):
        self.stream = self.pyaudio.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=44100,
            output=True,
            stream_callback=self._audio_callback
        )

    async def _setup_media_player(self):
        self.media_player_entity_id = self.config.get('audio_output.media_player_entity_id')
        if not self.media_player_entity_id:
            raise ValueError("Media player entity ID not specified in config")

    async def play(self, audio_segment):
        if isinstance(audio_segment, AudioSegment):
            audio_array = np.array(audio_segment.get_array_of_samples())
            normalized_array = audio_array.astype(np.float32) / 32768.0  # Normalize to [-1.0, 1.0]
            self.audio_buffer = normalized_array

        output_type = self.config.get('audio_output.type', 'local')
        if output_type == 'local':
            self._play_local()
        elif output_type == 'media_player':
            await self._play_media_player()

    def _play_local(self):
        if not self.is_playing:
            self.stream.start_stream()
            self.is_playing = True

    async def _play_media_player(self):
        # This is a simplified example. In a real implementation, you'd need to:
        # 1. Convert the AudioSegment to a suitable format (e.g., MP3)
        # 2. Save it to a file or stream it to a URL
        # 3. Use the media_player.play_media service to play it
        audio_url = "http://example.com/path/to/audio.mp3"  # Placeholder URL
        await self.hass.services.async_call(
            'media_player', 'play_media',
            {
                "entity_id": self.media_player_entity_id,
                "media_content_id": audio_url,
                "media_content_type": "music"
            }
        )

    def _audio_callback(self, in_data, frame_count, time_info, status):
        if not hasattr(self, 'audio_buffer') or len(self.audio_buffer) == 0:
            return (np.zeros(frame_count * 2, dtype=np.float32), pyaudio.paContinue)

        if len(self.audio_buffer) >= frame_count * 2:
            output_data = self.audio_buffer[:frame_count * 2]
            self.audio_buffer = self.audio_buffer[frame_count * 2:]
        else:
            output_data = np.pad(self.audio_buffer, (0, frame_count * 2 - len(self.audio_buffer)))
            self.audio_buffer = np.array([])

        return (output_data, pyaudio.paContinue)

    async def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()
        self.is_playing = False

    async def get_available_output_devices(self):
        devices = []
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            if device_info['maxOutputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxOutputChannels']
                })
        return devices

    async def get_available_media_players(self):
        media_players = []
        entities = self.hass.states.async_all()
        for entity in entities:
            if entity.domain == 'media_player':
                media_players.append({
                    'entity_id': entity.entity_id,
                    'name': entity.name
                })
        return media_players
