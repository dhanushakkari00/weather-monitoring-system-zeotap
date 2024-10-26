from background_task import background
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count
from .models import Weather, DailySummary
from .models import Notification
from django.contrib.auth.models import User
from .forms import AlertPreferenceForm
from .models import AlertPreference
from django.core.mail import send_mail
from background_task import background
from .models import Weather, DailySummary
from .views import get_current_weather, update_daily_summary
from datetime import datetime
# Define the cities you want to fetch weather data for
CITIES = ['Mumbai', 'Delhi', 'Chennai', 'Kolkata', 'Bangalore']

@background(schedule=60)  # Schedule the task to run every 60 seconds
def fetch_weather_data_task():
    """
    Task to fetch and store weather data for each city every minute.
    """
    for city in CITIES:
        weather_data = get_current_weather(city)  # Fetch current weather data

        if weather_data:
            # Save the current weather data in the Weather model
            Weather.objects.create(
                city=city,
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                weather_condition=weather_data.get('weather_condition', 'Unknown'),
                timestamp=datetime.now()
            )

            # Update the daily summary with new data
            update_daily_summary(city, weather_data['temperature'], weather_data['humidity'], weather_data['wind_speed'])

def update_daily_summary(city, temperature, humidity, wind_speed):
    """
    Update the daily summary (avg, max, min temperatures) for the city.
    """
    today = datetime.now().date()

    # Get all weather records for today
    records = Weather.objects.filter(city=city, timestamp__date=today)

    # Calculate average, max, and min temperatures
    avg_temperature = records.aggregate(Avg('temperature'))['temperature__avg']
    max_temperature = records.aggregate(Max('temperature'))['temperature__max']
    min_temperature = records.aggregate(Min('temperature'))['temperature__min']

    # Calculate average humidity and wind speed
    avg_humidity = records.aggregate(Avg('humidity'))['humidity__avg']
    avg_wind_speed = records.aggregate(Avg('wind_speed'))['wind_speed__avg']

    # Get the most frequent weather condition for today
    dominant_weather = records.values('weather_condition').annotate(count=Count('weather_condition')).order_by('-count').first()
    dominant_weather_condition = dominant_weather['weather_condition'] if dominant_weather else 'Unknown'

    # Update or create the DailySummary for today
    DailySummary.objects.update_or_create(
        city=city,
        date=today,
        defaults={
            'avg_temperature': avg_temperature,
            'max_temperature': max_temperature,
            'min_temperature': min_temperature,
            'avg_humidity': avg_humidity,
            'avg_wind_speed': avg_wind_speed,
            'dominant_weather_condition': dominant_weather_condition
        }
    )

# Add @background decorator to schedule this task
@background(schedule=60)  # Task will run every 24 hours
def calculate_daily_summary():
    today = timezone.now().date()
    cities = Weather.objects.values_list('city', flat=True).distinct()

    for city in cities:
        weather_data = Weather.objects.filter(city=city, timestamp__date=today)
        
        if weather_data.exists():
            avg_temp = weather_data.aggregate(Avg('temperature'))['temperature__avg']
            max_temp = weather_data.aggregate(Max('temperature'))['temperature__max']
            min_temp = weather_data.aggregate(Min('temperature'))['temperature__min']
            avg_humidity = weather_data.aggregate(Avg('humidity'))['humidity__avg']  # New
            avg_wind_speed = weather_data.aggregate(Avg('wind_speed'))['wind_speed__avg']  # New

            # Calculate dominant weather condition
            dominant_condition = weather_data.values('weather_condition').annotate(count=Count('weather_condition')).order_by('-count')[0]['weather_condition']

            # Save the daily summary to the database
            DailySummary.objects.create(
                city=city,
                date=today,
                avg_temperature=avg_temp,
                max_temperature=max_temp,
                min_temperature=min_temp,
                avg_humidity=avg_humidity,  # New
                avg_wind_speed=avg_wind_speed,  # New
                dominant_weather_condition=dominant_condition
            )
@background(schedule=60*60)  # Run every hour
def check_weather_alerts():
    preferences = AlertPreference.objects.all()

    for pref in preferences:
        recent_weather = Weather.objects.filter(city=pref.city).order_by('-timestamp')[:1]

        if recent_weather.exists():
            current_weather = recent_weather[0]

            # Check if the temperature exceeds the threshold
            if current_weather.temperature > pref.temperature_threshold:
                send_mail(
                    f"Temperature Alert for {pref.city}",
                    f"The temperature in {pref.city} has exceeded {pref.temperature_threshold}°C.",
                    'from@example.com',
                    [pref.email],
                    fail_silently=False,
                )
            
            # Check if humidity exceeds the threshold
            if current_weather.humidity > pref.humidity_threshold:
                send_mail(
                    f"Humidity Alert for {pref.city}",
                    f"The humidity in {pref.city} has exceeded {pref.humidity_threshold}%.",
                    'from@example.com',
                    [pref.email],
                    fail_silently=False,
                )

            # Check if wind speed exceeds the threshold
            if current_weather.wind_speed > pref.wind_speed_threshold:
                send_mail(
                    f"Wind Speed Alert for {pref.city}",
                    f"The wind speed in {pref.city} has exceeded {pref.wind_speed_threshold} m/s.",
                    'from@example.com',
                    [pref.email],
                    fail_silently=False,
                )