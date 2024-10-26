from .models import Weather
from django.core.mail import send_mail

def check_temperature_thresholds():
    threshold_temp = 35  # Example threshold
    recent_weather = Weather.objects.filter(temperature__gt=threshold_temp)

    for entry in recent_weather:
        send_mail(
            f'High Temperature Alert for {entry.city}',
            f'Temperature has exceeded {threshold_temp}°C. Current temperature is {entry.temperature}°C.',
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
