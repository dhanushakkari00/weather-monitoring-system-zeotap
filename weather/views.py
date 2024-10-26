import requests
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, redirect
from .models import Weather, Notification, AlertPreference
from .forms import AlertPreferenceForm
from django.db import models
import json
from .models import DailySummary
from datetime import datetime, timedelta
from .utils import get_current_weather
from background_task import background  # For scheduling periodic checks
from django.core.mail import send_mail
from django.db.models import Avg, Max, Min,Count
from .models import Weather, DailySummary



API_KEY = '472fb7d8ce67c61016bf5c807fbf1e31'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'http://api.openweathermap.org/data/2.5/forecast'
VISUAL_CROSSING_API_KEY = "LLXHSHFA7UXXC4HRFDRS9ZP6S"  # Replace with your API key
def alert_success(request):
    return render(request, 'weather/alert_success.html')
# Fetch past week's weather data for a city
def convert_temperature(temp, unit):
    if unit == 'Fahrenheit':
        return round(temp * 9/5 + 32)
    elif unit == 'Kelvin':
        return round(temp + 273.15)
    else:  # Celsius as default
        return round(temp)
def fetch_past_week_weather_vc(city):
    # Get today's date and the date 7 days ago
    today = datetime.now()
    past_date = today - timedelta(days=7)

    # Format the dates in the required format (yyyy-MM-dd)
    start_date = past_date.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # URL for Visual Crossing API (past weather data for a specific time range)
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start_date}/{end_date}?unitGroup=metric&key={VISUAL_CROSSING_API_KEY}&include=days"

    # Make API request
    response = requests.get(url)

    # Check for successful response
    if response.status_code == 200:
        data = response.json()

        # Extract only relevant weather information for the past 7 days
        past_week_weather = []
        for day in data['days']:
            past_week_weather.append({
                'date': day['datetime'],  # Date
                'avg_temperature': day.get('temp', None),  # Average temperature
                'max_temperature': day.get('tempmax', None),  # Max temperature
                'min_temperature': day.get('tempmin', None),  # Min temperature
                'avg_humidity': day.get('humidity', None),  # Average humidity
                'avg_wind_speed': day.get('windspeed', None),  # Wind speed
            })

        return past_week_weather
    else:
        print(f"Error fetching data: {response.status_code}")
        return None
def delete_alert(request, alert_id):
    alert = get_object_or_404(AlertPreference, id=alert_id)
    alert.delete()
    messages.success(request, 'Alert deleted successfully!')
    return redirect('view_alerts')
def edit_alert(request, alert_id):
    alert = get_object_or_404(AlertPreference, id=alert_id)
    if request.method == 'POST':
        form = AlertPreferenceForm(request.POST, instance=alert)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alert updated successfully!')
            return redirect('view_alerts')
    else:
        form = AlertPreferenceForm(instance=alert)
    return render(request, 'weather/edit_alert.html', {'form': form})
# View for analytics page
def analytics_view(request):
    city = request.GET.get('city', 'Delhi')  # Default city is Delhi
    weather_data = fetch_past_week_weather_vc(city)

    daily_summaries = weather_data if weather_data else []

    # List of cities for the dropdown
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']

    return render(request, 'weather/analytics.html', {
        'daily_summaries': daily_summaries,
        'selected_city': city,
        'cities': cities
    })
def get_weather_data(city):
    """ Fetch current weather data from OpenWeatherMap API """
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'  # Get temperature in Celsius
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_forecast_data(city):
    """ Fetch forecast weather data from OpenWeatherMap API """
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'  # Get temperature in Celsius
    }
    response = requests.get(FORECAST_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def home(request):
    # Get the selected city from the dropdown, default to Delhi
    selected_city = request.GET.get('city', 'Delhi')

    # Get the selected temperature unit, default to Celsius
    temperature_unit = request.GET.get('unit', 'Celsius')

    # Fetch current weather data
    weather_data = get_weather_data(selected_city)

    # Convert temperatures based on the selected unit
    if weather_data:
        current_weather = {
            'weather_condition': weather_data['weather'][0]['description'],
            'temperature': convert_temperature(weather_data['main']['temp'], temperature_unit),
            'feels_like': convert_temperature(weather_data['main']['feels_like'], temperature_unit),
            'humidity': weather_data['main']['humidity'],
            'wind_speed': weather_data['wind']['speed'],
            'precipitation': weather_data.get('rain', {}).get('1h', 0),  # Precipitation in the last hour (if available)
            'timestamp': weather_data['dt']
        }
    else:
        current_weather = None

    # Fetch forecast data
    forecast_data = get_forecast_data(selected_city)

    forecast = []
    if forecast_data:
        # Process the forecast for the next 5 upcoming hours
        for item in forecast_data['list'][:5]:
            forecast.append({
                'weather_condition': item['weather'][0]['description'],
                'temperature': convert_temperature(item['main']['temp'], temperature_unit),
                'feels_like': convert_temperature(item['main']['feels_like'], temperature_unit),
                'precipitation': item.get('rain', {}).get('3h', 0),  # Precipitation in the forecast (3 hours)
                'timestamp': item['dt_txt'],  # The forecast time
            })

    # List of cities for the dropdown
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']

    return render(request, 'weather/home.html', {
        'selected_city': selected_city,
        'temperature_unit': temperature_unit,
        'current_weather': current_weather,
        'forecast': forecast,  # Pass forecast data to the template
        'cities': cities
    })

def set_alerts_view(request):
    if request.method == 'POST':
        form = AlertPreferenceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_alerts')  # Redirect to view alerts page after saving
    else:
        form = AlertPreferenceForm()

    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']  # Your list of cities

    return render(request, 'weather/set_alerts.html', {
        'form': form,
        'cities': cities
    })
def set_alert_preference(request):
    if request.method == 'POST':
        form = AlertPreferenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alert has been successfully set!')
            return redirect('set_alert_preference')
        else:
            messages.error(request, 'Please fill in all required fields.')
    else:
        form = AlertPreferenceForm()

    # Clear messages related to other actions like 'Alert deleted successfully'
    if messages:
        storage = messages.get_messages(request)
        storage.used = True  # Clear all messages before rendering

    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']
    return render(request, 'weather/set_alerts.html', {'form': form, 'cities': cities})

def notifications(request):
    user = request.user
    user_notifications = Notification.objects.filter(user=user, is_read=False)
    return render(request, 'weather/notifications.html', {'notifications': user_notifications})


def fetch_weather_data(request):
    api_key = settings.OPENWEATHER_API_KEY
    city = "Delhi"  # Example city
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4))  # Print the entire JSON response to the console
        
        if 'main' in data:
            return render(request, 'weather/weather_data.html', {'data': data, 'city': city})
        else:
            return HttpResponse(f"Unexpected response format: {json.dumps(data)}", status=500)
    else:
        return HttpResponse(f"Error fetching data from API: {response.status_code} - {response.text}", status=500)
def daily_summary_view(request):
    summaries = DailySummary.objects.all()  # Correct model name is DailySummary
    return render(request, 'weather/daily_summary.html', {'summaries': summaries})
def view_alerts(request):
    alerts = AlertPreference.objects.all()  # Fetch all alerts from the database
    return render(request, 'weather/view_alerts.html', {'alerts': alerts})
import logging

logger = logging.getLogger(__name__)
def get_current_weather(city):
    """
    Fetch current weather data from the OpenWeatherMap API
    """
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'  # Fetch in Celsius
    }
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        logger.info(f"API response for {city}: {data}")
        return {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'weather_condition': data['weather'][0]['main'] if 'weather' in data and data['weather'] else 'Unknown'
        }
    else:
        logger.error(f"Failed to fetch weather data for {city}. Status code: {response.status_code}")
        return None

@background(schedule=60)
def check_weather_alerts_task():
    alerts = AlertPreference.objects.all()  # Get all user-set alerts

    for alert in alerts:
        city = alert.city
        threshold = alert.temperature_threshold
        email = alert.email

        # Fetch current weather data for the city
        current_weather = get_current_weather(city)

        # Log or print the current weather data to see its structure
        if current_weather:
            print(f"Current weather data for {city}: {current_weather}")  # Debug print
            
            # Check if 'temperature' key exists in the current weather data
            if 'temperature' in current_weather:
                rounded_temperature = round(current_weather['temperature'])  # Round to nearest integer
                
                # Check if the rounded temperature matches or exceeds the threshold
                if rounded_temperature >= threshold:
                    # Send email notification
                    send_mail(
                        subject='Weather Alert: Temperature Threshold Reached',
                        message=f'The current temperature in {city} is {rounded_temperature}°C, which has reached or exceeded your threshold of {threshold}°C.',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                        fail_silently=False,
                    )
            else:
                print(f"Error: 'temperature' key not found in the current weather data for {city}")
        else:
            print(f"Failed to fetch weather data for {city}")
# Store weather data in the database
def store_weather_data(city, weather_data):
    if weather_data:
        temperature = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        weather_condition = weather_data['weather'][0]['description']

        # Create a new Weather record
        Weather.objects.create(
            city=city,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            weather_condition=weather_condition,
            timestamp=timezone.now()
        )

        # Update the daily summary after saving weather data
        update_daily_summary(city)
def weather_analytics_view(request):
    city = request.GET.get('city', 'Delhi')  # Default city if none selected

    # Fetch weather data from the database
    weather_data = DailySummary.objects.filter(city=city)

    if weather_data.exists():
        # Calculate average, max, and min temperature
        avg_temperature = weather_data.aggregate(Avg('avg_temperature'))['avg_temperature__avg']
        max_temperature = weather_data.aggregate(Max('max_temperature'))['max_temperature__max']
        min_temperature = weather_data.aggregate(Min('min_temperature'))['min_temperature__min']

        # Get dominant weather condition (based on most frequent condition)
        dominant_weather = weather_data.values('dominant_weather_condition').annotate(count=Count('dominant_weather_condition')).order_by('-count').first()['dominant_weather_condition']
    else:
        avg_temperature = max_temperature = min_temperature = dominant_weather = None

    # List of cities for dropdown
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']

    return render(request, 'weather/weather_analytics.html', {
        'avg_temperature': avg_temperature,
        'max_temperature': max_temperature,
        'min_temperature': min_temperature,
        'dominant_weather': dominant_weather,
        'selected_city': city,
        'cities': cities
    })

@background(schedule=60)
def fetch_and_store_weather_data():
    cities = ['Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore']
    for city in cities:
        weather_data = get_weather_data(city)
        if weather_data:
            store_weather_data(city, weather_data)
@background(schedule=60)
def fetch_weather_data_task():
    logger.info("Fetching weather data for all cities.")
    CITIES = ['Mumbai', 'Delhi', 'Chennai', 'Kolkata', 'Bangalore']
    for city in CITIES:
        weather_data = get_current_weather(city)

        if weather_data:
            logger.info(f"Storing weather data for {city}: {weather_data}")
            Weather.objects.create(
                city=city,
                temperature=weather_data['temperature'],
                humidity=weather_data['humidity'],
                wind_speed=weather_data['wind_speed'],
                weather_condition=weather_data['weather_condition'],
                timestamp=datetime.now()
            )
            # Update the daily summary
            update_daily_summary(city, weather_data['temperature'], weather_data['humidity'], weather_data['wind_speed'])

def update_daily_summary(city, temperature, humidity, wind_speed):
    today = datetime.now().date()
    
    # Get all weather records for today
    records = Weather.objects.filter(city=city, timestamp__date=today)

    # Ensure records exist
    if records.exists():
        logger.info(f"Updating daily summary for {city} with {records.count()} records")
        
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
        logger.info(f"Daily summary updated for {city}")

# Call this function to start the background task
def start_fetching_weather_data():
    fetch_and_store_weather_data(repeat=60)  # Repeat every 60 seconds
