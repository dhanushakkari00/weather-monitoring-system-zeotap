from django.db.models.signals import post_migrate
from django.dispatch import receiver
from background_task.models import Task
from weather.tasks import check_weather_alerts  # Import the task

@receiver(post_migrate)
def schedule_weather_alerts(sender, **kwargs):
    print("post_migrate signal triggered, scheduling weather alerts...")

    # Check if the task already exists before scheduling it
    if not Task.objects.filter(task_name='weather.tasks.check_weather_alerts').exists():
        check_weather_alerts(repeat=60*60)  # Schedule to run every hour
        print("Weather alert task scheduled.")
    else:
        print("Weather alert task already scheduled.")
