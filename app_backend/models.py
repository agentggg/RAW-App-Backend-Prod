from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker
from django.core.exceptions import ValidationError
import re
from datetime import time

def generate_time_choices():
    times = []
    for hour in range(24):
        for minute in [0, 30]:  # Adjust to 0 and 30 for half-hour intervals, or just [0] for hourly
            times.append((time(hour, minute).strftime('%H:%M'), time(hour, minute).strftime('%H:%M')))
    return times

def validate_event_image_time(value):
    pattern = r'^[0-2][0-9]:[0-5][0-9]$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Invalid format. Please use hh:mm in military time.'
        )

class Role(models.Model):
    name = models.CharField(max_length=30, unique=True)


    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    color = models.TextField(null=False, blank=False, default='#000')
    profile_access = models.ManyToManyField(Role, blank=True, related_name='users')
    phone_number = models.TextField(null=True, blank=True, default='#000')

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super(CustomUser, self).save(*args, **kwargs)
        if is_new:
            default_role = Role.objects.get_or_create(name='Pending Approval')[0]
            self.profile_access.add(default_role)

    def __str__(self):
        return str(self.username)

class PushToken(models.Model):
    username = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    push_token = models.TextField(null=False, blank=False)
    device_make = models.TextField(null=False, blank=False)
    device_model = models.TextField(null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.username)

class Analytics(models.Model):
    date = models.TextField(null=False, blank=False)
    time = models.TextField(null=False, blank=False)
    browser = models.TextField(null=False, blank=False)
    os = models.TextField(null=False, blank=False)
    device = models.TextField(null=False, blank=False)
    region = models.TextField(null=False, blank=False)
    endpoint = models.TextField(null=False, blank=False)

class ProjectType(models.Model):
    NAME_CHOICES = [
        ('Relationship', 'Relationship'),
        ('Evangelism', 'Evangelism'),
        ('Discipleship', 'Discipleship'),
    ]
    name = models.CharField(choices=NAME_CHOICES,max_length=30)

    def __str__(self):
        return str(self.name)


class Project(models.Model):
    PHASE_CHOICES = [
        ('initiation', 'Initiation'),
        ('planning', 'Planning'),
        ('execution', 'Execution'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('review', 'Review')
    ]
    FLAG_CHOICES = [
        ('green', 'Green'),
        ('#ecb753', 'Yellow'),
        ('red', 'Red')
    ]
    COLOR_HEX = [
    ("#FF0000", "Red"),
    ("#00FF00", "Green"),
    ("#0000FF", "Blue"),
    ("#FFFF00", "Yellow"),
    ("#FFA500", "Orange"),
    ("#800080", "Purple"),
    ("#FFC0CB", "Pink"),
    ("#A52A2A", "Brown"),
    ("#000000", "Black"),
    ("#808080", "Grey"),
    ("#00FFFF", "Cyan"),
    ("#800000", "Maroon"),
    ("#008000", "Dark Green"),
    ("#000080", "Navy")
]
    name = models.TextField(null=False, blank=False)
    flag = models.CharField(choices=FLAG_CHOICES, default='green',max_length=20)
    phase = models.CharField(choices=PHASE_CHOICES, default='initiation', max_length=20 )
    projectColor = models.CharField(choices=COLOR_HEX, default='#00FF00', max_length=20 )
    projectType = models.ForeignKey(ProjectType, on_delete=models.CASCADE)
    projectStakeholders = models.ManyToManyField(CustomUser, related_name='project_stakeholders')
    startDate = models.TextField(null=False, blank=False)
    dueDate = models.TextField(null=False, blank=False)
    shortDescription = models.TextField(null=False, blank=False)
    longDescription = models.TextField(null=False, blank=False)
    image = models.URLField(null=False, blank=False, max_length=200)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

class ProjectDeliverables(models.Model): #updated 4/23
    COLOR_HEX = [
    ("#FF0000", "Red"),
    ("#00FF00", "Green"),
    ("#0000FF", "Blue"),
    ("#FFFF00", "Yellow"),
    ("#FFA500", "Orange"),
    ("#800080", "Purple"),
    ("#FFC0CB", "Pink"),
    ("#A52A2A", "Brown"),
    ("#000000", "Black"),
    ("#808080", "Grey"),
    ("#00FFFF", "Cyan"),
    ("#800000", "Maroon"),
    ("#008000", "Dark Green"),
    ("#000080", "Navy")
]
    PHASE_CHOICES = [
        ('On Track', 'On Track'),
        ('At Risk', 'At Risk'),
        ('Delayed', 'Delayed'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
        ('Blocked', 'Blocked'),
    ]
    FLAG_CHOICES = [
        ('green', 'Green'),
        ('#ecb753', 'Yellow'),
        ('red', 'Red')
    ]
    deliverableName = models.TextField()
    projectName = models.ForeignKey(Project, on_delete=models.CASCADE)
    deliverableStatus = models.CharField(choices=PHASE_CHOICES, default='initiation', max_length=20)
    deliverableStatusColor = models.CharField(choices=FLAG_CHOICES, default='green', max_length=20)
    deliverableColor = models.CharField(choices=COLOR_HEX, default='green', max_length=20)
    deliverableOwner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='project_details_as_owner')
    deliverableDetails = models.TextField()
    deliverableCompleted = models.BooleanField(default=False)
    deliverableStartDate = models.TextField(null=False, blank=False, default = '01-12-2024')
    deliverableEndDate = models.TextField(null=False, blank=False, default= '09-01-2024')
    enabled = models.BooleanField(default=False)
    markedForReview = models.BooleanField(default=False)

    tracker = FieldTracker(fields=['markedForReview'])

    def __str__(self):
        return str(f'Deliverable {self.deliverableName} for the {self.projectName} project owned by {self.deliverableOwner}')

class ProjectNotes(models.Model):
    project_deliverable_name = models.ForeignKey(ProjectDeliverables, on_delete=models.CASCADE)
    notes = models.TextField(null=False, blank=False)
    noteAuthor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timeStamp = models.TextField(null=False, blank=False)

    def __str__(self):
        return str(self.project_deliverable_name)

class DeliverableNotesWatchers:
    watcher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='task_owner')
    project_deliverable = models.ForeignKey(ProjectDeliverables, on_delete=models.CASCADE)
    projectName = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectExpense(models.Model):
    projectName = models.ForeignKey(Project, on_delete=models.CASCADE)
    cost = models.TextField(null=False, blank=False)
    costName = models.TextField(null=False, blank=False)
    color = models.TextField(null=False, blank=False, default='blue')

    def __str__(self):
        return str(self.projectName)

class AutomatedNotification(models.Model):
    notification = models.CharField(max_length=255)
    executed = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.notification} execution status {self.executed}'

class MyTask(models.Model):
    COLOR_HEX = [
    ("#FF0000", "Red"),
    ("#00FF00", "Green"),
    ("#0000FF", "Blue"),
    ("#FFFF00", "Yellow"),
    ("#FFA500", "Orange"),
    ("#800080", "Purple"),
    ("#FFC0CB", "Pink"),
    ("#A52A2A", "Brown"),
    ("#000000", "Black"),
    ("#808080", "Grey"),
    ("#00FFFF", "Cyan"),
    ("#800000", "Maroon"),
    ("#008000", "Dark Green"),
    ("#000080", "Navy")
]
    PHASE_CHOICES = [
        ('On Track', 'On Track'),
        ('At Risk', 'At Risk'),
        ('Delayed', 'Delayed'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold'),
        ('Blocked', 'Blocked'),
    ]
    FLAG_CHOICES = [
        ('green', 'Green'),
        ('#ecb753', 'Yellow'),
        ('red', 'Red')
    ]
    taskName = models.TextField()
    taskStatus = models.CharField(choices=PHASE_CHOICES, default='initiation', max_length=20)
    taskStatusColor = models.CharField(choices=FLAG_CHOICES, default='green', max_length=20)
    taskColor = models.CharField(choices=COLOR_HEX, default='green', max_length=20)
    taskOwner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='task_owner')
    taskDetails = models.TextField()
    taskCompleted = models.BooleanField(default=False)
    taskStartDate = models.TextField(null=False, blank=False, default = '01-12-2024')
    taskEndDate = models.TextField(null=False, blank=False, default= '09-01-2024')
    enabled = models.BooleanField(default=False)

class Announcement(models.Model):
    announcementAuthor =  models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='announcementAuthor')
    announcementDate = models.TextField(max_length=100)
    announcement = models.TextField()

class ReOccurance(models.Model): #05/23
    TimeOfDay = generate_time_choices()
    DayOfWeek = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    WeekOfMonth = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ]
    username = models.ManyToManyField(CustomUser)
    taskName = models.TextField(null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    timeOfEvent = models.CharField(max_length=16, validators=[validate_event_image_time], null=True, blank=True)
    dayOfWeek = models.CharField(choices=DayOfWeek,max_length=30)
    week = models.CharField(choices=WeekOfMonth,max_length=10)

    def __str__(self):
        return self.taskName

class Event(models.Model):
    eventName = models.TextField()
    eventDate = models.TextField()
    eventNote = models.TextField(null=True, blank=True)
    eventTime = models.TextField(null=False, blank=False)
    eventLocation = models.TextField()
    eventDescription = models.TextField()
    eventFollower = models.ManyToManyField(CustomUser, related_name='eventFollowers', blank=True)
    eventWatcher = models.ManyToManyField(CustomUser, related_name='eventWatchers', blank=True)
    eventNotification = models.ManyToManyField(CustomUser, related_name='eventNotifications', blank=True)
    eventSubscribers = models.ManyToManyField(Role)
    eventImageUrl = models.TextField(null=True, blank=True)
    eventEnable = models.BooleanField(default=False)
    eventReoccuring = models.BooleanField(default=False, blank=True)
    reoccuringInfo = models.ForeignKey(ReOccurance, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return self.eventName

class Questions(models.Model):
    question = models.TextField(null=False, blank=False)
    answer = models.TextField(null=False, blank=False)
    date = models.DateTimeField(auto_now=True)
    rewardAmount = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return self.question

class AnsweredQuestion(models.Model):
    username = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True, blank=True)
    question = models.ForeignKey(Questions, on_delete=models.RESTRICT,null=True, blank=True)
    questionAttempted = models.BooleanField(default=False)
    answeredCorrectly = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.question.question}"

class Stats(models.Model):
    username = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True, blank=True)
    total = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username} - {self.total} points"

class Rewards(models.Model):
    rewardName = models.TextField(null=False, blank=False)
    rewardImage = models.URLField(default=0, null=False, blank=False)
    pointRequirement = models.IntegerField(default=10, null=False, blank=False)
    winners = models.ManyToManyField(CustomUser, null=True, blank=True)

    def __str__(self):
        return f"{self.rewardName}"

class EventNotification(models.Model):
    eventName = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.eventName.eventName}'

@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)