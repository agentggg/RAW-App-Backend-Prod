from rest_framework import serializers
from app_backend.models import *
from django.utils.encoding import force_str


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"

class OwnerNameSerializer(serializers.ModelSerializer): #4/23
    class Meta: 
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'is_active') 


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = "__all__"
        
class ProjectDeliverablesSerializers(serializers.ModelSerializer): #updated 4/23
    project_type = ProjectTypeSerializer(read_only = True, source='projectType')
    deliverableOwner = OwnerNameSerializer(read_only = True)
    class Meta:
        model = ProjectDeliverables
        fields = "__all__"



class ProjectSerializers(serializers.ModelSerializer):
    projectType = ProjectTypeSerializer(read_only=True)
    projectStakeholders = CustomUserSerializer(read_only=True, many=True)  # Notice the many=True here
    class Meta:
        model = Project
        fields = "__all__"

class ReOccuranceSerializers(serializers.ModelSerializer):
    class Meta:
        model = ReOccurance
        fields = "__all__"

class RoleSerializers(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"

class EventSerializers(serializers.ModelSerializer):
    eventFollower = OwnerNameSerializer(read_only=True, many=True)
    eventWatcher = OwnerNameSerializer(read_only=True, many=True)
    eventNotification = OwnerNameSerializer(read_only=True, many=True)
    eventSubscribers = RoleSerializers(read_only=True, many=True)
    class Meta:
        model = Event
        fields = "__all__"

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = "__all__"


class AnsweredQuestionSerializer(serializers.ModelSerializer):
    username = OwnerNameSerializer(read_only=True, many=True)
    question = QuestionSerializer(read_only=True, many=True)
    class Meta:
        model = AnsweredQuestion
        fields = "__all__"

class StatsSerializer(serializers.ModelSerializer):
    username = OwnerNameSerializer(read_only=True)

    class Meta:
        model = Stats
        fields = "__all__"
    
class RewardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rewards
        fields = "__all__"