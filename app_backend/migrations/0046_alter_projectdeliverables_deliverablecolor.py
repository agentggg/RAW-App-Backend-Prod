# Generated by Django 4.2.9 on 2024-01-23 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_backend', '0045_rename_deliverablecompletion_projectdeliverables_deliverablecompleted_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectdeliverables',
            name='deliverableColor',
            field=models.CharField(choices=[('green', 'Green'), ('#ecb753', 'Yellow'), ('red', 'Red')], default='green', max_length=20),
        ),
    ]
