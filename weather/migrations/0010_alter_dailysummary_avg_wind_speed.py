# Generated by Django 5.1.2 on 2024-10-26 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0009_remove_alertpreference_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailysummary',
            name='avg_wind_speed',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
