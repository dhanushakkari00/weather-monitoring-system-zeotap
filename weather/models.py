from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta


# Model to store individual weather updates with a timestamp
class Weather(models.Model):
    city = models.CharField(max_length=100)
    temperature = models.FloatField()
    humidity = models.FloatField()  # Field for humidity
    wind_speed = models.FloatField()  # Field for wind speed
    weather_condition = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically add the timestamp when data is saved

    def __str__(self):
        return f"{self.city} - {self.temperature}°C - {self.humidity}% - {self.wind_speed}m/s at {self.timestamp}"


# Model to store daily summaries
class DailySummary(models.Model):
    city = models.CharField(max_length=100)
    date = models.DateField()
    avg_temperature = models.FloatField()
    max_temperature = models.FloatField()
    min_temperature = models.FloatField()
    avg_humidity = models.FloatField()  # Average humidity for the day
    avg_wind_speed = models.FloatField(null=True, blank=True)  # Make avg_wind_speed optional
    max_wind_speed = models.FloatField(null=True, blank=True)  # Max wind speed for the day
    dominant_weather_condition = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.city} - {self.date} - {self.avg_temperature}°C"

    @classmethod
    def calculate_daily_summary(cls, city):
        """
        Calculate and store the daily summary for a city.
        This method fetches the weather data stored in the `Weather` model and calculates the required daily summary.
        """
        # Get all weather data for the city on the current day
        start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        weather_data = Weather.objects.filter(city=city, timestamp__range=(start_of_day, end_of_day))

        if weather_data.exists():
            # Extract temperature, humidity, wind_speed and conditions
            temperatures = [entry.temperature for entry in weather_data]
            humidities = [entry.humidity for entry in weather_data]
            wind_speeds = [entry.wind_speed for entry in weather_data]
            weather_conditions = [entry.weather_condition for entry in weather_data]

            # Calculate averages, max, and min
            avg_temp = sum(temperatures) / len(temperatures)
            max_temp = max(temperatures)
            min_temp = min(temperatures)
            avg_humidity = sum(humidities) / len(humidities)
            avg_wind_speed = sum(wind_speeds) / len(wind_speeds)
            max_wind_speed = max(wind_speeds)
            dominant_condition = max(set(weather_conditions), key=weather_conditions.count)

            # Save the daily summary
            summary, created = cls.objects.update_or_create(
                city=city,
                date=start_of_day.date(),
                defaults={
                    'avg_temperature': avg_temp,
                    'max_temperature': max_temp,
                    'min_temperature': min_temp,
                    'avg_humidity': avg_humidity,
                    'avg_wind_speed': avg_wind_speed,
                    'max_wind_speed': max_wind_speed,
                    'dominant_weather_condition': dominant_condition
                }
            )
            return summary
        return None


# Model to store alert preferences
class AlertPreference(models.Model):
    city = models.CharField(max_length=100)
    email = models.EmailField()
    weather_condition = models.CharField(max_length=100)
    temperature_threshold = models.FloatField()
    humidity_threshold = models.FloatField(null=True, blank=True)  # Add this line

    def __str__(self):
        return f"{self.city} - {self.weather_condition} - {self.temperature_threshold}"



# Model to store notifications for users
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who receives the notification
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # Mark whether the notification has been read
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message}"

