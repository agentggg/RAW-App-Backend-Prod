# Generated by Django 3.2.13 on 2024-06-07 00:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_backend', '0021_alter_surveyviewed_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='reoccuringInfo',
        ),
    ]
