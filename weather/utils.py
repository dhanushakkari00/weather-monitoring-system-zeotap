import requests

def get_current_weather(city):
    """ Fetch current weather data from OpenWeatherMap API """
    API_KEY = '472fb7d8ce67c61016bf5c807fbf1e31'
    BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'  # Get temperature in Celsius
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None
