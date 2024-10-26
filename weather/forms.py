from django import forms
from .models import AlertPreference

class AlertPreferenceForm(forms.ModelForm):
    class Meta:
        model = AlertPreference
        fields = ['city', 'email', 'weather_condition', 'temperature_threshold']  # Add other necessary fields here