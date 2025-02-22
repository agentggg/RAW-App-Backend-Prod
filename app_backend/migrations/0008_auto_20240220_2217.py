# Generated by Django 3.2.13 on 2024-02-20 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_backend', '0007_reoccurance'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdeliverables',
            name='markedForReview',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='reoccurance',
            name='timeSlot',
            field=models.CharField(choices=[('08am', '08am'), ('12pm', '12pm'), ('04pm', '04pm'), ('08pm', '08pm'), ('12am', '12am'), ('04am', '04am'), ('06pm', '06pm')], max_length=30),
        ),
        migrations.AlterField(
            model_name='reoccurance',
            name='week',
            field=models.CharField(choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')], max_length=10),
        ),
    ]
