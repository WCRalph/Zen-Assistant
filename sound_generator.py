import asyncio
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
import numpy as np

class SoundGenerator:
    def __init__(self, config):
        self.config = config
        self.sound_library = self._load_sound_library()
        self.current_mix = AudioSegment.silent(duration=10000)  # 10 second base loop

    def _load_sound_library(self):
        # Load sound samples based on configuration
        library = {
            'cricket': AudioSegment.from_wav(self.config.get('sounds.cricket')),
            'bird': AudioSegment.from_wav(self.config.get('sounds.bird')),
            'wave': AudioSegment.from_wav(self.config.get('sounds.wave')),
        }
        return library

    async def generate(self, data):
        # Create a new mix based on the input data
        new_mix = AudioSegment.silent(duration=10000)  # 10 second base loop

        # Generate traffic sound (cricket chirps)
        traffic_sound = self._generate_traffic_sound(data['traffic_intensity'])
        new_mix = new_mix.overlay(traffic_sound)

        # Generate energy usage sound (bird calls)
        energy_sound = self._generate_energy_sound(data['energy_usage'])
        new_mix = new_mix.overlay(energy_sound)

        # Generate weather sound (waves)
        weather_sound = self._generate_weather_sound(data['temperature'], data['humidity'])
        new_mix = new_mix.overlay(weather_sound)

        # Smoothly transition from the current mix to the new mix
        self.current_mix = self._crossfade(self.current_mix, new_mix)

        return self.current_mix

    def _generate_traffic_sound(self, intensity):
        cricket = self.sound_library['cricket']
        chirp = cricket[:500]  # Use first 500ms of cricket sound
        silence = AudioSegment.silent(duration=500)
        
        # Adjust volume based on intensity (0-100)
        chirp = chirp - (20 - (intensity / 5))  # Adjust volume from -20dB to 0dB
        
        # Create a loop of chirps, with frequency based on intensity
        loop_count = int(intensity / 10) + 1
        return (chirp + silence) * loop_count

    def _generate_energy_sound(self, usage):
        bird = self.sound_library['bird']
        call = bird[:1000]  # Use first 1000ms of bird sound
        silence = AudioSegment.silent(duration=1000)
        
        # Adjust pitch based on usage (0-100)
        pitch_shift = usage - 50  # Shift pitch up or down based on usage
        call = call._spawn(call.raw_data, overrides={
            "frame_rate": int(call.frame_rate * (2.0 ** (pitch_shift / 12.0)))
        })
        
        # Create a sequence of calls, with frequency based on usage
        loop_count = int(usage / 20) + 1
        return (call + silence) * loop_count

    def _generate_weather_sound(self, temperature, humidity):
        wave = self.sound_library['wave']
        
        # Adjust wave sound based on temperature and humidity
        wave = wave - (30 - temperature / 3)  # Louder when warmer
        
        # Add some white noise for humidity
        humidity_noise = WhiteNoise().to_audio_segment(duration=10000)
        humidity_noise = humidity_noise - (60 - humidity / 2)  # Louder when more humid
        
        return wave.overlay(humidity_noise)

    def _crossfade(self, sound1, sound2, duration=1000):
        # Implement a smooth crossfade between two sounds
        return sound1.append(sound2, crossfade=duration)
