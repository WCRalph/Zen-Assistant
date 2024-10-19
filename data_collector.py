import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get_registry

class DataCollector:
    def __init__(self, hass: HomeAssistant, config):
        self.hass = hass
        self.config = config
        self.entity_registry = None

    async def setup(self):
        self.entity_registry = await async_get_registry(self.hass)

    async def collect(self):
        """Collect data from Home Assistant entities."""
        data = {}

        # Collect traffic data
        traffic_entity_id = self.config.get('data_sources.traffic')
        if traffic_entity_id:
            traffic_state = self.hass.states.get(traffic_entity_id)
            if traffic_state:
                data['traffic_intensity'] = self._normalize_value(traffic_state.state, 0, 100)

        # Collect energy usage data
        energy_entity_id = self.config.get('data_sources.energy')
        if energy_entity_id:
            energy_state = self.hass.states.get(energy_entity_id)
            if energy_state:
                data['energy_usage'] = self._normalize_value(energy_state.state, 0, 10000)  # Assuming kWh

        # Collect weather data
        weather_entity_id = self.config.get('data_sources.weather')
        if weather_entity_id:
            weather_state = self.hass.states.get(weather_entity_id)
            if weather_state:
                data['temperature'] = float(weather_state.attributes.get('temperature', 20))
                data['humidity'] = float(weather_state.attributes.get('humidity', 50))

        # Collect custom entities
        custom_entities = self.config.get('data_sources.custom', [])
        for entity_config in custom_entities:
            entity_id = entity_config['entity_id']
            name = entity_config['name']
            state = self.hass.states.get(entity_id)
            if state:
                data[name] = self._normalize_value(state.state, 
                                                   entity_config.get('min', 0),
                                                   entity_config.get('max', 100))

        return data

    def _normalize_value(self, value, min_value, max_value):
        """Normalize a value to a 0-100 scale."""
        try:
            value = float(value)
            return ((value - min_value) / (max_value - min_value)) * 100
        except ValueError:
            return 50  # Default to middle value if conversion fails

    async def get_available_entities(self):
        """Get a list of available entities in Home Assistant."""
        entities = []
        for entity in self.entity_registry.entities.values():
            entities.append({
                'entity_id': entity.entity_id,
                'name': entity.name or entity.original_name,
                'domain': entity.domain
            })
        return entities
