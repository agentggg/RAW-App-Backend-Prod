# Generated by Django 4.2.9 on 2024-01-17 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_backend', '0032_rename_project_details_name_projectnotes_project_deliverable_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='flag',
            field=models.CharField(choices=[('Green', '#7CFC00'), ('Yellow', '#E4D00A'), ('Red', '#C70039')], default='#7CFC00', max_length=20),
        ),
    ]
