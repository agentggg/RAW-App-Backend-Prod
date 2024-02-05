from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    color = models.TextField(null=False, blank=False, default='#000')
    profile_access = models.TextField(null=False, blank=False)

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
    ("#FFFFFF", "White"),
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

    def __str__(self):
        return str(self.name)

class ProjectDeliverables(models.Model):
    COLOR_HEX = [
    ("#FF0000", "Red"),
    ("#00FF00", "Green"),
    ("#0000FF", "Blue"),
    ("#FFFF00", "Yellow"),
    ("#FFA500", "Orange"),
    ("#800080", "Purple"),
    ("#FFC0CB", "Pink"),
    ("#A52A2A", "Brown"),
    ("#FFFFFF", "White"),
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
    deliverableStatusColor = models.CharField(choices=FLAG_CHOICES, default='initiation', max_length=20)
    deliverableColor = models.CharField(choices=COLOR_HEX, default='green', max_length=20)
    deliverableOwner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='project_details_as_owner')
    deliverableDetails = models.TextField() 
    deliverableCompleted = models.BooleanField(default=False) 
    deliverableStartDate = models.TextField(null=False, blank=False, default = '01-12-2024')
    deliverableEndDate = models.TextField(null=False, blank=False, default= '09-01-2024')


    def __str__(self):
        return str(f'Deliverable {self.deliverableName} for the {self.projectName} project owned by {self.deliverableOwner}')

class ProjectNotes(models.Model):
    project_deliverable_name = models.ForeignKey(ProjectDeliverables, on_delete=models.CASCADE)
    notes = models.TextField(null=False, blank=False)
    noteAuthor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timeStamp = models.TextField(null=False, blank=False)

    def __str__(self): 
        return str(self.project_deliverable_name)

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


