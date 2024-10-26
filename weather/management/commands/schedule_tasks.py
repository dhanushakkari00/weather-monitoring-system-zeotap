from django.core.management.base import BaseCommand
from background_task.models import Task
from weather.tasks import check_weather_alerts

class Command(BaseCommand):
    help = 'Schedule weather alert tasks'

    def handle(self, *args, **kwargs):
        # Check if the task is already scheduled
        if not Task.objects.filter(task_name='weather.tasks.check_weather_alerts').exists():
            check_weather_alerts(repeat=60*60)  # Schedule the task to run every hour
            self.stdout.write(self.style.SUCCESS('Weather alert task scheduled.'))
        else:
            self.stdout.write(self.style.WARNING('Weather alert task already scheduled.'))
