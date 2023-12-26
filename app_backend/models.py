from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

REGEX_PHONE_NUMBER = RegexValidator(regex=r'^\d{10}$', message="PHONE MUST BE 10 DIGITS: '4731234567'.")

class CustomUser(AbstractUser):
    color = models.TextField(null=False, blank=False, default='#000')

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

class Project(models.Model):
    name = models.TextField(null=False, blank=False)
    flag = models.TextField(null=False, blank=False)
    dueDate = models.TextField(null=False, blank=False)
    shortDescription = models.TextField(null=False, blank=False)
    longDescription = models.TextField(null=False, blank=False)
    image = models.TextField(null=False, blank=False)
    color = models.TextField(null=False, blank=False)
    initation = models.BooleanField(default=False)
    planning = models.BooleanField(default=False)
    execution = models.BooleanField(default=False)
    live = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    review = models.BooleanField(default=False)
    watchers = models.ManyToManyField('CustomUser', related_name='watched_projects')
    projectType = models.TextField(null=False, blank=False)
    startDate = models.TextField(null=False, blank=False)



    def __str__(self):
        return str(self.name)

class ProjectDetails(models.Model):
    name = models.ForeignKey(Project, on_delete=models.CASCADE)
    deliverableName = models.TextField(null=False, blank=False)
    deliverableDetails = models.TextField(null=False, blank=False)
    deliverableOwner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='project_details_as_owner')
    watchers = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='project_details_as_watcher')
    deliverableStatus = models.TextField(null=False, blank=False)

    def __str__(self):
        return str(self.name)
    
class ProjectReporting(models.Model):
    name = models.ForeignKey(Project, on_delete=models.CASCADE)
    notes = models.TextField(null=False, blank=False)
    comments = models.TextField(null=False, blank=False)

    def __str__(self):
        return str(self.name)

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
    
@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


