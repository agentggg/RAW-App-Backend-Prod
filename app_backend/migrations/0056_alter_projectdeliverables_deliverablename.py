# Generated by Django 4.2.9 on 2024-02-05 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_backend', '0055_alter_projectdeliverables_deliverablename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectdeliverables',
            name='deliverableName',
            field=models.TextField(),
        ),
    ]
