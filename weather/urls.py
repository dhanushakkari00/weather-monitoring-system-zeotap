# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('data/', views.fetch_weather_data, name='fetch_weather_data'),
    path('notifications/', views.notifications, name='notifications'),
    path('set-alerts/', views.set_alert_preference, name='set_alert_preference'),  # Correct the name here
    path('alert-success/', views.alert_success, name='alert_success'),
    path('daily-summary/', views.daily_summary_view, name='daily_summary'),
    path('weather-analytics/', views.weather_analytics_view, name='weather_analytics'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('view-alerts/', views.view_alerts, name='view_alerts'),
    path('edit-alert/<int:alert_id>/', views.edit_alert, name='edit_alert'),
    path('delete-alert/<int:alert_id>/', views.delete_alert, name='delete_alert'),


    
]
