# Register your models here.
from django.contrib import admin
from .models import Weather, DailySummary

# Register your models here
admin.site.register(Weather)
admin.site.register(DailySummary)
