"""
Weather plugin for PennyGPT
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from ..base_plugin import BasePlugin


class WeatherPlugin(BasePlugin):
    """Plugin to handle weather queries"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = os.getenv('OPENWEATHER_API_KEY') or self.config.get('api_key')
        self.default_city = self.config.get('default_city', 'San Francisco')
        
        if not self.api_key:
            print("Warning: No OpenWeatherMap API key found. Weather plugin will be limited.")
    
    def can_handle(self, intent: str, query: str) -> bool:
        """Check if this plugin can handle the weather request"""
        # If intent is already classified as weather, we handle it
        if intent == 'weather':
            return True
            
        # Otherwise, check for weather-specific patterns in the query
        query_lower = query.lower().strip()
        
        # Weather query patterns (more precise than just keywords)
        weather_patterns = [
            r"what'?s? the weather",
            r"how'?s? the weather",
            r"what'?s? the temperature",
            r"how'?s? the temp",
            r"weather in",
            r"weather for",
            r"temperature in",
            r"temperature for",
            r"is it (raining|sunny|cloudy|hot|cold)",
            r"will it (rain|snow)",
            r"weather forecast"
        ]
        
        import re
        return any(re.search(pattern, query_lower) for pattern in weather_patterns)
    
    async def execute(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute weather lookup"""
        if not self.api_key:
            return {
                'success': False,
                'response': "I need an OpenWeatherMap API key to check the weather. Please set OPENWEATHER_API_KEY environment variable.",
                'error': 'missing_api_key'
            }
        
        try:
            # Extract city from query (simple approach)
            city = self._extract_city_from_query(query) or self.default_city
            
            # Get weather data
            weather_data = await self._get_weather_data(city)
            
            if weather_data:
                response = self._format_weather_response(weather_data, city)
                return {
                    'success': True,
                    'response': response,
                    'data': weather_data
                }
            else:
                return {
                    'success': False,
                    'response': f"Sorry, I couldn't get weather information for {city}.",
                    'error': 'api_error'
                }
                
        except Exception as e:
            return {
                'success': False,
                'response': "Sorry, I encountered an error getting the weather.",
                'error': str(e)
            }
    
    def _extract_city_from_query(self, query: str) -> Optional[str]:
        """Extract city name from user query (basic implementation)"""
        # Simple approach - look for "in [city]" or "for [city]"
        query_lower = query.lower().strip('?.,!')
        
        for preposition in [' in ', ' for ']:
            if preposition in query_lower:
                parts = query_lower.split(preposition)
                if len(parts) > 1:
                    city = parts[1].strip().split()[0]  # First word after preposition
                    return city.title()
        
        return None
    
    async def _get_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch weather data from OpenWeatherMap API"""
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'  # Celsius
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Weather API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Weather API request failed: {e}")
            return None
    
    def _format_weather_response(self, data: Dict[str, Any], city: str) -> str:
        """Format weather data into a natural response"""
        try:
            temp = round(data['main']['temp'])
            feels_like = round(data['main']['feels_like'])
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            
            response = f"The weather in {city} is currently {temp}°C with {description}. "
            response += f"It feels like {feels_like}°C with {humidity}% humidity."
            
            return response
            
        except KeyError as e:
            return f"Got weather data for {city}, but couldn't parse it properly."
    
    def get_help_text(self) -> str:
        return "Ask me about the weather! Try: 'What's the weather?' or 'How's the weather in Paris?'"
    
    def get_supported_intents(self) -> List[str]:
        return ['weather']


# Usage example / test
if __name__ == "__main__":
    async def test_weather():
        plugin = WeatherPlugin()
        result = await plugin.execute("What's the weather in London?")
        print(result)
    
    asyncio.run(test_weather())
