from django.apps import AppConfig

class WeatherConfig(AppConfig):
    name = 'weather'

    def ready(self):
        # Import the signal handlers to connect them
        import weather.signals
