from django.db import IntegrityError, transaction
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.http import JsonResponse
from .models import *
from .tasks import *
import environ
env = environ.Env()
import logging
logger = logging.getLogger(__name__)
environ.Env.read_env()
from datetime import datetime
from django.core.mail import send_mail
from rest_framework import status
from user_agents import parse
import pytz
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from .reuseableFunctions.deliverableReminders import notifications
from .serializers import *
from faker import Faker
fake = Faker()
from django.shortcuts import get_object_or_404
from django.db.models import Value, CharField #udpated 4/23
from django.db.models.functions import Concat #udpated 4/23
from random import choice  # Import choice function to randomly select from a list
from django.contrib.auth.models import User, Group #updated 5/11
import re
import math
from twilio.rest import Client

def send_event_notifications(event):
    message = f"A new event '{event.eventName}' has been added to the Event board! Check it out. Hopefully you will be able join 😊"
    landing = {'pageView': 'EventsHomepage'}

    # Get all users associated with the roles in eventSubscribers
    subscriber_roles = event.eventSubscribers.all()
    subscribers = CustomUser.objects.filter(profile_access__in=subscriber_roles).distinct()

    for user in subscribers:
        try:
            userToken = PushToken.objects.get(username=user).push_token
            send_push_message(userToken, message, landing)
        except PushToken.DoesNotExist:
            print(f"No push token for user {user.username}")
        except Exception as e:
            print(f"Error sending notification to {user.username}: {e}")


def get_week_of_month(date):
    first_day = date.replace(day=1)
    day_of_week = first_day.weekday()
    adjusted_dom = date.day + day_of_week  # day of month + day of week adjustment
    return int(math.ceil(adjusted_dom / 7.0))

def analytics(request, endpoint):
    try:
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
        language_parts = re.split(r'[;,]', accept_language)
        nation = [part.strip() for part in language_parts if part.strip()]
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_string)
        currentDateTime = datetime.now()
        est_timezone = pytz.timezone('US/Eastern')
        est_datetime = currentDateTime.astimezone(est_timezone)
        date = currentDateTime.strftime("%m/%d/%Y")
        time = est_datetime.strftime("%H:%M:%S %Z")
        browser = user_agent.browser.family, user_agent.browser.version_string
        os = user_agent.os.family, user_agent.os.version_string
        device = user_agent.device.family
        region = nation[0]
        Analytics.objects.create(
            date=date,
            time=time,
            browser=browser,
            os=os,
            device=device,
            region=region,
            endpoint=endpoint
        )
    except Exception as e:
        print(f"An error occurred in the analytics function: {str(e)}")
        return(500)

def send_push_message(token, message, extra=None):
    try:
        if not token:
            raise ValueError("Token cannot be empty")
        if not message:
            raise ValueError("Message cannot be empty")
        response = PushClient().publish(
            PushMessage(to=token,
                        body=message,
                        data=extra))
        if response.status == "ok":
            print("Notification sent successfully")
        else:
            error_message = response.get("message", "Unknown error")
            print(f"Notification failed to send: {error_message}")
    except DeviceNotRegisteredError as dnre:
        print("DeviceNotRegisteredError:", dnre)
    except PushTicketError as pte:
        print("PushTicketError:", pte)
    except PushServerError as pse:
        print("PushServerError:", pse)
    except ValueError as ve:
        print("ValueError:", ve)
    except Exception as exc:
        print("An unexpected error occurred:", exc)



@api_view(['GET', 'POST'])
def send_blast_notification_manually(request):
    message = request.data.get("message", False)
    try:
        message = request.data.get("message", False)
        allToken = []
        for eachToken in allToken:
            send_push_message(eachToken, message)
        return Response ('successful')
    except Exception as exc:
        # print('error found in notification targeted:', exc)
        return Response('failed ')

@api_view(['GET', 'POST'])
def send_blast_email_manually(request):
    import time
    emailSender = request.data.get('emailSender', False)
    emailSubject = request.data.get('emailSubject', False)
    emailMessage = request.data.get('emailMessage', False)
    try:
        allEmails = [
    "stevensongerardeustache@outlook.com",
    "raw_ministries@outlook.com",
    "deeirdra21@gmail.com"
]
        for eachEmail in allEmails:
            updatedEmailMessage = f"""Hey there😃!

{emailMessage}

Please feel free to respond to this email with any questions, comments, and/or concerns. I am not a robot 😂. This account is being monitored 😊.

Thank you very much!

Sincerely,

Revealed Mysteries Support Team ✨🌙
"""
            try:
                send_mail(
                    emailSubject,
                    updatedEmailMessage,
                    emailSender,
                    [eachEmail],
                    fail_silently=False,
                )

                print(f'Email sent to {eachEmail} successfully.')
                time.sleep(5)
            except Exception as e:
                print(f'Error sending email to {eachEmail}: {e}')
        return Response({'message': 'Emails sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def process_survey_notifications(event_name, survey_name): #05/31
    landing = {'screenView': 'Homepage'}
    try:
        event_instance = Event.objects.get(eventName=event_name)
        event_data = {
            'id': event_instance.id,
            'eventFollower': list(event_instance.eventFollower.values('id', 'username')),
            'eventWatcher': list(event_instance.eventWatcher.values('id', 'username')),
            'eventNotification': list(event_instance.eventNotification.values('id', 'username')),
            'eventSubscribers': [{'id': subscriber.id, 'name': subscriber.name} for subscriber in event_instance.eventSubscribers.all()],
            'eventName': event_instance.eventName,
            'eventDate': event_instance.eventDate,
            'eventNote': event_instance.eventNote,
            'eventTime': event_instance.eventTime,
            'eventLocation': event_instance.eventLocation,
            'eventDescription': event_instance.eventDescription,
            'eventImageUrl': event_instance.eventImageUrl,
            'eventEnable': event_instance.eventEnable,
            'eventReoccuring': event_instance.eventReoccuring,
            'reoccuringInfo': event_instance.reoccuringInfo.id if event_instance.reoccuringInfo else None,
        }
        processed_users = set()

        def process_users(user_list, user_role):
            for eachUser in user_list:
                print(eachUser)
                if eachUser['id'] not in processed_users:
                    try:
                        userToken = PushToken.objects.get(username=eachUser['id']).push_token
                        send_push_message(userToken, f'Help the ministry by taking a quick survey for the {survey_name} event', landing)
                        processed_users.add(eachUser['id'])
                    except PushToken.DoesNotExist:
                        print(f"PushToken for {eachUser['username']} ({user_role}) does not exist.")
                    except Exception as e:
                        print(f"An error occurred while processing {user_role}: {e}")

        process_users(event_data['eventFollower'], 'eventFollower')
        process_users(event_data['eventWatcher'], 'eventWatcher')
        process_users(event_data['eventNotification'], 'eventNotification')

    except Event.DoesNotExist:
        print(f"Event with name {event_name} does not exist.")

@api_view(['POST'])
def send_blast_emails(request):
    import time
    try:
        emailSender = request.data.get('emailSender', False)
        emailSubject = request.data.get('emailSubject', False)
        emailMessage = request.data.get('emailMessage', False)
        setView = request.data.get('setView', False)
        if setView == "APITest":
            try:
                send_mail(
                    emailSubject,
                    emailMessage,
                    emailSender,
                    ["gersard@yahoo.com"],
                    fail_silently=False,
                )
                return Response("successful test")
            except Exception as e:
                print(e)
                return Response("unsuccessful test")
        user_data = CustomUser.objects.values('first_name', 'email')  # Replace 'CustomUser' with your actual model name
        for user in user_data:
            first_name = user['first_name']
            email = user['email']
            updatedEmailMessage = f"""Hey {first_name}😃!

{emailMessage}
Please feel free to respond to this email with any questions, comments, and/or concerns. I am not a robot 😂. This account is being monitored.

Thank you {first_name}

Sincerely,

Revealed Mysteries Team ✨🌙
"""
            try:
                send_mail(
                    emailSubject,
                    updatedEmailMessage,
                    emailSender,
                    [email],
                    fail_silently=False,
                )

                print(f'Email sent to {email} successfully.')
                time.sleep(5)
            except Exception as e:
                print(f'Error sending email to {email}: {e}')
        return Response({'message': 'Emails sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def send_blast_notifications(request):
    analytics(request, "Blast Notifications Sent")
    try:
        setView = request.data.get("setView", False)
        if setView == "verify":
            password = request.data.get("password", False)
            if password != "cisco":
                return Response("unsuccessful")
            else:
                return Response("successful")
        elif setView == "blastNotifications":
            message = request.data.get("message", False)
            allToken = PushToken.objects.all().values_list('push_token', flat=True)
            for eachToken in allToken:
                send_push_message(eachToken, message)
            return Response ('successful')
    except Exception as exc:
        # print('error found in notification targeted:', exc)
        return Response('failed ')

@api_view(['POST']) #updated 4/8
def send_blast(request):
    try:
        setView = request.data.get("setView", False)
        if setView == "verify":
            password = request.data.get("password", False)
            if password != "cisco":
                return Response("unsuccessful")
            else:
                return Response("successful")
        elif setView == "blastNotifications":
            message = request.data.get("message", False)
            allToken = PushToken.objects.all().values_list('push_token', flat=True)
            for eachToken in allToken:
                send_push_message(eachToken, message)
            return Response ('successful')
    except Exception as exc:
        print(exc)
        return Response('failed ')

@api_view(['GET', 'POST'])
def test(request):
    import random
    questions_data = [
        # Easy Questions (Reward 1-3)
        ("What is the first book of the Bible?", "Genesis", "Genesis", "Exodus", "Leviticus", "Numbers", 1),
        ("Who built the ark?", "Noah", "Moses", "Noah", "David", "Solomon", 1),
        ("Who was swallowed by a great fish?", "Jonah", "Jonah", "Peter", "Paul", "Daniel", 2),
        ("In what city was Jesus born?", "Bethlehem", "Nazareth", "Bethlehem", "Jerusalem", "Capernaum", 1),
        ("Who brought Jesus gifts when he was born?", "The wise men", "The shepherds", "The wise men", "John the Baptist", "The Pharisees", 2),
        ("What is the eighth commandment?", "Thou shall not steal", "Thou shall not steal", "Thou shall not kill", "Thou shall not commit adultery", "Thou shall not covet", 2),
        ("Who is the angel who told Mary she would give birth to Jesus?", "Gabriel", "Michael", "Gabriel", "Raphael", "Uriel", 3),
        ("On which day did Jesus rise from the dead?", "Third day", "Second day", "Third day", "Fourth day", "Fifth day", 3),
        ("What was Jesus' crown made of?", "Thorns", "Gold", "Silver", "Thorns", "Bronze", 3),
        ("Where does Jesus give his first sermon?", "On the mount", "In the temple", "On the mount", "By the sea", "In the synagogue", 2),

        # Medium Questions (Reward 4-6)
        ("Who baptized Jesus and in what river?", "John the Baptist in the River Jordan", "Peter in the Sea of Galilee", "John the Baptist in the River Jordan", "Paul in the Tigris", "James in the Nile", 4),
        ("Name the first two apostles to follow Jesus.", "Peter and Andrew", "James and John", "Peter and Andrew", "Matthew and Thomas", "Philip and Nathanael", 4),
        ("What was the profession of Simon Peter before following Jesus?", "Fisherman", "Tax collector", "Fisherman", "Carpenter", "Shepherd", 4),
        ("Where did Jesus turn water into wine?", "Cana", "Nazareth", "Bethlehem", "Cana", "Jericho", 5),
        ("How many days was Lazarus dead before Jesus came to visit?", "Four", "Three", "Four", "Five", "Two", 5),
        ("What is the name of the garden where Jesus went to pray after the Last Supper?", "Garden of Gethsemane", "Garden of Eden", "Garden of Gethsemane", "Garden of Olives", "Garden of Bethany", 5),
        ("After Jesus fed 5,000 people, how many baskets of food were left over?", "Twelve", "Five", "Seven", "Twelve", "Four", 5),
        ("What color are the four horses in the Book of Revelation?", "White, Red, Black, and Pale", "White, Red, Blue, and Green", "White, Red, Black, and Pale", "White, Yellow, Black, and Pale", "White, Red, Black, and Grey", 6),
        ("How old was Jesus when he started his ministry?", "Thirty", "Twenty-five", "Thirty", "Thirty-three", "Forty", 5),
        ("After Jesus was crucified, who took His body down from the cross?", "Joseph of Arimathea", "Nicodemus", "Joseph of Arimathea", "Simon Peter", "John the Apostle", 6),

        # Hard Questions (Reward 7-10)
        ("Who is considered the 13th apostle to replace Judas Iscariot?", "Matthias", "Paul", "Barnabas", "Matthias", "Timothy", 8),
        ("At King Herod's birthday party, what unusual gift did he grant his stepdaughter?", "The head of John the Baptist", "A golden crown", "The head of John the Baptist", "A horse", "A palace", 8),
        ("What city mentioned in the Book of Revelation is also the name of an American city?", "Philadelphia", "Bethlehem", "Philadelphia", "Jericho", "Nazareth", 7),
        ("Name the shortest verse in the Bible.", "Jesus wept.", "Rejoice always", "Pray without ceasing", "Jesus wept.", "God is love", 7),
        ("Who watched as Moses floated in the basket down the Nile?", "His Sister Miriam", "His Mother Jochebed", "Pharaoh's daughter", "His Sister Miriam", "Aaron", 8),
        ("Who would have nothing to do with the author of 3 John?", "Diotrephes", "Demetrius", "Diotrephes", "Gaius", "The Elder", 9),
        ("In the book of Philemon, who is Paul's fellow prisoner?", "Epaphras", "Timothy", "Epaphras", "Tychicus", "Archippus", 8),
        ("James used the example of which Old Testament figure to demonstrate how the prayers of a righteous man can have powerful results?", "Elijah", "Moses", "Elijah", "David", "Solomon", 9),
        ("How does the author of 1 John often refer to his readers?", "Children", "Beloved", "Children", "Brethren", "Friends", 8),
        ("Who pretended to be mad to avoid capture and death at the hands of an enemy king?", "David", "Saul", "David", "Jonathan", "Absalom", 10),
    ]

    # Shuffle the questions
    random.shuffle(questions_data)

    for question_data in questions_data:
        question, answer, option1, option2, option3, option4, reward = question_data
        Questions.objects.create(
            question=question,
            answer=answer,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            rewardAmount=reward
        )

    return Response({"message": "Questions populated successfully."}, status=200)

@api_view(['POST'])
def alert(request):
    if request.method != "POST":
        print(request.data)
        return JsonResponse({"error": "Invalid request method"}, status=400)
    try:
        """
         [
            {
                'token': '34c1cbb3f0a60e40a0d526275aae6e1a9798017a',
                'first_name': 'Stevenson',
                'last_name': 'Gerard Eustache',
                'username': 'cisco',
                'email': 'stevensongerardeustache@outlook.com',
                'profile_name': 'cisco',
                'premium': 'notPremium',
                'active': True,
                'ipAddress': '10.0.0.212',
                'networkState': {'type': 'WIFI', 'isConnected': True, 'isInternetReachable': True}
            },
        ]

        """
        frontendData = request.data.get('userInfo')
        first_name = frontendData.get('first_name')
        last_name = frontendData.get('last_name')
        username = frontendData.get('username')
        email = frontendData.get('email')
        profile_name = frontendData.get('profile_name')
        ipAddress = frontendData.get('ipAddress')
        networkState = frontendData.get('networkState')
        try:
            CustomUser.objects.filter(username=username).update(
            is_active=0,
            )
        except Exception as e:
            print(e)
            return Response(500)
        message = f"""
A user is attempting to access the Revealed Mysteries admin page, and has failed to successfully authenticate 3 times. The user account is now suspended until further actions.
-------------------------------------------------
First name: {first_name}
Last name: {last_name}
User: {username}
Email: {email}
Profile name: {profile_name}
IP: {ipAddress}
Network info: {networkState}
-------------------------------------------------
"""

        send_mail(
            "Revealed App Unauthorized Access Detected",
            message,
            'tech.and.faith.contact@gmail.com',
            ['tech.and.faith.contact@gmail.com'],
            fail_silently=False,
        )
        return Response(200)
    except Exception as e:
        print(e)
        return Response(500)

@api_view(['GET'])
def link_to_app(request):
    analytics(request, "Shared The App")
    link = "https://techandfaith.carrd.co"
    return Response(link)

@api_view(['POST'])
def send_notifications(request):
    analytics(request, "Sent Push Notification")
    message = request.data.get('message', False)
    setView = request.data.get('setView', False)
    projectName = request.data.get('projectName', False)
    deliverables = request.data.get('deliverables', False)
    deliverableName = request.data.get('deliverableName', False)
    deliverableOwner = request.data.get('deliverableOwner', False)
    if setView == "projectProposal":
        username = ["agentofgod"]
        message = (f"New project, {projectName}, has been submitted. Please review and submit feedback")
        for eachUsername in username:
            receiverToken = CustomUser.objects.filter(username=eachUsername).values_list('id')[0][0] #returns the new friend profile id number
            try:
                token = PushToken.objects.filter(username=receiverToken).values_list('push_token', flat=True)[0]
            except Exception as e:
                print('error')
                token = ""
            if token == "":
                print("No token")
            else:
                send_push_message(token, message, extra=None)
        return Response({"message": "Notifications sent"}, status=status.HTTP_201_CREATED)
    elif setView == "deliverables":
        username = ["agentofgod"]
        for eachDeliverable in deliverables:
            message = (f"New project, {eachDeliverable['name']}, has been submitted. Please review and submit feedback")
            for eachUsername in username:
                receiverToken = CustomUser.objects.filter(username=eachUsername).values_list('id')[0][0]
                try:
                    token = PushToken.objects.filter(username=receiverToken).values_list('push_token', flat=True)[0]
                except Exception as e:
                    print('error')
                    token = ""
                if token == "":
                    print("No token")
                else:
                    send_push_message(token, message)
        return Response({"message": "Notifications sent"}, status=status.HTTP_201_CREATED)
    elif setView == "editDeliverable":
        projectName = Project.objects.get(id=projectName)
        message = (f"The {deliverableName} for {projectName} has been modified by the RAW Project Manager team. Please review this deliverable")
        try:
            receiverToken = CustomUser.objects.filter(pk=deliverableOwner).values_list('id')[0][0]
            token = PushToken.objects.filter(username=receiverToken).values_list('push_token', flat=True)[0]
        except Exception as e:
            print('error')
            token = ""
        if token == "":
            print("No token")
        else:
            landing = {'pageView':'My Deliverables'}
            send_push_message(token, message, extra=landing)
    return Response({"message": "Notifications sent"}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
def login_verification(request):
    try:
        # Initialize your serializer with the request data
        serializer = ObtainAuthToken.serializer_class(data=request.data, context={'request': request})

        # Validate the data. If it's not valid, a ValidationError will be raised
        serializer.is_valid(raise_exception=True)

        # Get the user from the validated data
        user = serializer.validated_data['user']

        # Fetch profile access roles. This assumes the user model has a related 'profile_access' field
        profile_access_roles = user.profile_access.all().values_list('name', flat=True)

        # Attempt to get or create the auth token for the user
        token, created = Token.objects.get_or_create(user=user)

        # If everything is successful, return the user information and token
        return Response({
            'token': token.key,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'active': user.is_active,
            'profile_access': list(profile_access_roles)
        })

    except ValidationError as e:
        print(e)
        # Handle validation errors from serializer.is_valid()
        return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        # Handle any other exceptions that may occur
        print(e)
        return Response({"errors": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def token_validation(request):
    analytics(request, "Token Validation")
    if request.method != "POST":
        return Response("This is a POST and not a GET. Please contact admin", status=status.HTTP_400_BAD_REQUEST)
    username_frontend = request.data.get("username", False)
    try:
        user_identification_value = CustomUser.objects.get(username=username_frontend)
    except CustomUser.DoesNotExist:
        return Response("User not found", status=status.HTTP_404_NOT_FOUND)
    try:
        token_value = Token.objects.filter(user_id=user_identification_value).values_list('key', flat=True)
    except Token.DoesNotExist:
        return Response("Token not found for the user", status=status.HTTP_404_NOT_FOUND)
    return Response(token_value, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def user_profile(request):
    analytics(request, "User Profile Viewed")
    username = request.data.get('username', False)
    username_id = CustomUser.objects.filter(username=username).values("first_name","last_name","username","email")
    return Response(username_id) # Send the response to the frontend

@api_view(['POST'])
def save_push_token(request):
    analytics(request, "Devices Saved")
    username = request.data.get('username', False)
    pushToken = request.data.get('token', False)
    queryUsernameId = CustomUser.objects.values_list('id', flat=True).get(username=username)
    customUserInstance = CustomUser.objects.get(id=queryUsernameId)
    deviceMake = request.data.get('deviceMake', False)
    deviceModel = request.data.get('deviceModel', False)
    setView = request.data.get('setView', False)
    confirmPushToken = PushToken.objects.filter(username=queryUsernameId).exists()
    if confirmPushToken == False:
        if setView == "tokenCheck":
            return Response("notExsist")
        try:
            if pushToken != False:
                PushToken.objects.create(
                    username=customUserInstance,
                    device_make=deviceMake,
                    device_model=deviceModel,
                    push_token=pushToken
                )
                return Response('successful')
            return Response('successful')
        except Exception as e:
            print(e)
            return Response(e)
    elif confirmPushToken == True:
        try:
            if pushToken != False:
                if setView == "tokenCheck":
                    if confirmPushToken == False:
                        return Response('successful')
                    else:
                        return Response('alreadyConfirmed')
                else:
                    PushToken.objects.filter(username=customUserInstance).update(
                        push_token=pushToken,
                        device_make=deviceMake,
                        device_model=deviceModel
                    )
                    return Response('successful')
            return Response('successful')
        except Exception as err:
            print(err)
            return Response('unsuccessful')


@api_view(['POST']) #updated 4/19
def edit_deliverables(request):
    name = request.data.get('name', False)
    endDate = request.data.get('endDate', False)
    startDate = request.data.get('startDate', False)
    detail = request.data.get('detail', False)
    id = request.data.get('id', False)
    try:
        updated_count = ProjectDeliverables.objects.filter(
            id=id,
        ).update(
            deliverableEndDate=endDate,
            deliverableStartDate=startDate,
            deliverableDetails=detail,
            deliverableName=name
        )
        if updated_count == 0:
            print("Deliverable not found or no update needed")
            return Response('not updated')
        return Response('successful')
    except Exception as e:
        print(e)
        return Response('error')


@api_view(['POST']) #updated 4/23
def project_info(request):
    infoType = request.data.get('infoType', False)
    projectId = request.data.get('projectId', False)
    if infoType == 'project':
        projectInfo = Project.objects.filter(enabled=True).select_related('projectType').prefetch_related('projectStakeholders').values('projectType__name', 'id', 'name', 'flag', 'phase', 'projectStakeholders', 'startDate', 'dueDate', 'shortDescription', 'longDescription', 'image', 'projectStakeholders__first_name', 'projectStakeholders__username', 'projectColor', 'id')
        projectInfo = list(projectInfo)
        seen = set()
        unique_projects = []

        for item in projectInfo:
            if item['id'] not in seen:
                seen.add(item['id'])
                unique_projects.append(item)
        return Response(unique_projects)
    elif infoType == 'project_details':
        projectInfo = ProjectDeliverables.objects.filter(projectName=projectId).select_related('projectType').prefetch_related('projectStakeholders').values().order_by('-id')
        projectInfo = list(projectInfo)
        seen = set()
        unique_projects = []

        for item in projectInfo:
            if item['id'] not in seen:
                seen.add(item['id'])
                unique_projects.append(item)
        return Response(unique_projects)
    elif infoType == 'stakeholders':
        projectInfo = Project.objects.filter(id=projectId)
        projectInfo = Project.objects.filter(id=projectId).prefetch_related('projectStakeholders').values("projectStakeholders__first_name","projectStakeholders__last_name")
    elif infoType == 'deliverablesPercentage':
        allDeliverables = ProjectDeliverables.objects.filter(projectName=projectId, enabled=True).values()
        completedCount = sum(1 for eachDeliverable in allDeliverables if eachDeliverable.get('deliverableCompleted') == True)
        deliverablesTotal = len(allDeliverables)
        projectInfo = completedCount / deliverablesTotal
    elif infoType == 'deliverables':
        projectInfo = ProjectDeliverables.objects.filter(projectName=projectId, enabled=True).values(
            'deliverableOwner__first_name','deliverableOwner__last_name',
            'deliverableName','projectName','deliverableStatus','deliverableStatusColor',
            'deliverableColor','deliverableOwner','deliverableDetails','deliverableCompleted',
            'deliverableStartDate','deliverableEndDate'
            )
    elif infoType == 'specficProjectDeliverableView':
        projectIdInstance = Project.objects.get(id=projectId)
        projectInfoId = ProjectDeliverables.objects.filter(projectName=projectIdInstance)
        projectInfo = ProjectDeliverablesSerializers(projectInfoId, many=True).data
    return Response(projectInfo)

@api_view(['GET']) #updated 4/23
def allUsers(request):
    users = CustomUser.objects.all()
    userSerializer = OwnerNameSerializer(users, many=True).data
    return Response(userSerializer)

@api_view(['POST']) #updated 4/24
def update_deliverables(request):
    """
    {
    "id": 391,
    "deliverableName": "Family responsibility message. Professional better thank lose of. Oil tonight common professor.",
    "deliverableStatus": "Blocked",
    "deliverableStatusColor": "red",
    "deliverableColor": "#800000",
    "deliverableDetails": "",
    "deliverableCompleted": true,
    "deliverableStartDate": "2006-01-30",
    "deliverableEndDate": "2017-05-19",
    "enabled": true,
    "markedForReview": null,
    "projectName": 63,
    "deliverableOwner": 116,
    "completed": null,
    "status": "Completed",
    "owner": null
    }
    """""
    setView = request.data.get('setView', False)
    deliverables = request.data.get('deliverables', [])
    project_id = request.data.get('projectName', False)
    if setView ==  'ProjectManagement':
        deliverableCompleted = request.data.get('valueCompleted', False)
        markedForReview = request.data.get('markedForReview', False)
        status = request.data.get('status', False)
        id = request.data.get('id', False)
        deliverableOwner = request.data.get('owner', False)
        deliverableOwner = CustomUser.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
        ).get(full_name=deliverableOwner)
        try:
            ProjectDeliverables.objects.update_or_create(
                id=id,
                defaults={
                    'deliverableCompleted': deliverableCompleted,
                    'markedForReview': markedForReview,
                    'deliverableStatus': status,
                    'deliverableOwner': deliverableOwner
                }
            )
            return Response('successful')
        except Exception as e:
            print(e)
            return Response('error')
    else:
        project = Project.objects.get(id=project_id)
        new_deliverables = []
        with transaction.atomic():
            for deliverable_data in deliverables:
                owner_username = deliverable_data.get('owner')
                if not owner_username:
                    return Response({"error": "Owner username missing in deliverables"}, status=status.HTTP_400_BAD_REQUEST)
                deliverableOwner = CustomUser.objects.get(username=owner_username)
                new_deliverable = ProjectDeliverables(
                    deliverableName=deliverable_data.get('name'),
                    projectName=project,
                    deliverableColor=deliverable_data.get('color'),
                    deliverableOwner=deliverableOwner,
                    deliverableDetails=deliverable_data.get('details'),
                    deliverableStartDate=deliverable_data.get('startDate'),
                    deliverableEndDate=deliverable_data.get('endDate'),
                )
                new_deliverables.append(new_deliverable)
            ProjectDeliverables.objects.bulk_create(new_deliverables)  # Bulk create for efficiency
        return Response({"message": "Project and deliverables successfully updated"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def my_deliverables(request):
    infoType = request.data.get('infoType', False)
    username = request.data.get('username', False)
    try:
        usernameInstance = CustomUser.objects.get(username=username).id
        if infoType == 'deliverablesPercentage':
            allDeliverables = ProjectDeliverables.objects.filter(deliverableOwner=usernameInstance, enabled=True).values()
            completedCount = sum(1 for eachDeliverable in allDeliverables if eachDeliverable.get('deliverableCompleted') == True)
            deliverablesTotal = len(allDeliverables)
            projectInfo = completedCount / deliverablesTotal
        elif infoType == 'delvierables':
            projectInfo = ProjectDeliverables.objects.filter(deliverableOwner=usernameInstance, enabled=True).values(
                'projectName__name','deliverableName','deliverableStatus','deliverableStatusColor',
                'deliverableColor','deliverableOwner','deliverableDetails','deliverableCompleted',
                'deliverableStartDate','deliverableEndDate', 'markedForReview'
                )
            return Response(projectInfo)
    except Exception as e:
        print(e)
        return Response('error')

@api_view(['POST'])
def my_notes(request):
    deliverableOwner = request.data.get('deliverableOwner', False)
    deliverableName = request.data.get('deliverableName', False)
    project_deliverable_name_instance = ProjectDeliverables.objects.get(deliverableName=deliverableName, deliverableOwner=deliverableOwner).id
    notes = ProjectNotes.objects.filter(project_deliverable_name=project_deliverable_name_instance).values(
        'noteAuthor__username',
        'timeStamp',
        'notes',
        'project_deliverable_name'
    ).order_by('-id')
    return Response(notes)

@api_view(['POST'])
def new_note(request):
    setView = request.data.get('setView')
    project_deliverable_name = request.data.get('project_deliverable_name')
    notes = request.data.get('notes')
    timeStamp = request.data.get('timeStamp')
    username = request.data.get('username')
    noteAuthor = CustomUser.objects.get(username=username)
    if setView == "stakeHolderNotes":
        try:
            project_deliverable_name = ProjectDeliverables.objects.get(deliverableName=project_deliverable_name)
        except Exception as e:
            print(e)
            return Response ('error')
    else:
        try:
            project_deliverable_name = ProjectDeliverables.objects.get(id=project_deliverable_name)
        except Exception as e:
            print(e)
            return Response ('error')
    try:
        ProjectNotes.objects.create(
            project_deliverable_name=project_deliverable_name,
            notes=notes,
            timeStamp=timeStamp,
            noteAuthor=noteAuthor
        )
        return Response('successful')
    except Exception as e:
        print(e)
        return Response('error')


@api_view(['POST'])
def profile_access(request):
    return Response('hi')

@api_view(['POST','GET']) #5/30
def re_occurance_notification(request):
    setView = request.data.get('setView', False)
    if setView == 'createTask':
        username = request.data.get('username', False)
        weekOfMonth = request.data.get('reminderWeekSelected', False)
        message = request.data.get('deliverableDetails', False)
        timeSlot = request.data.get('reminderTimeSelected', False)
        pattern = r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(pattern, timeSlot):
            return Response('time error')
        dayOfWeek = request.data.get('reminderDaySelected', False)
        deliverableName = request.data.get('deliverableName', False)
        if weekOfMonth == 'First':
           weekOfMonth == 1
        elif weekOfMonth == 'Second':
           weekOfMonth == 2
        elif weekOfMonth == 'Third':
           weekOfMonth == 3
        elif weekOfMonth == 'Fourth':
           weekOfMonth == 4
        try:
            createEvent = ReOccurance.objects.create(
                # The username field is not set here, it will be added later
                message=message,
                timeOfEvent=timeSlot,
                dayOfWeek=dayOfWeek,
                taskName=deliverableName,
                week=weekOfMonth
            )
            errors = []
            for eachUsername in username:
                try:
                    username_instance = CustomUser.objects.get(username=eachUsername)
                    createEvent.username.add(username_instance)
                    token = PushToken.objects.get(username=username_instance).push_token
                    landing = {'screenView': 'Stewardship', 'deliverableInformation': 'deliverableInformation'}
                    send_push_message(token, f'Take a look at the new task, {deliverableName}, that is within your stewardship space', extra=landing)
                except CustomUser.DoesNotExist:
                    errors.append(f'Username {eachUsername} does not exist.')
                except PushToken.DoesNotExist:
                    errors.append(f'Push token for username {eachUsername} does not exist.')
                except Exception as e:
                    errors.append(f'Error with username {eachUsername}: {str(e)}')

            createEvent.save()

            if errors:
                return Response('errors')
            return Response('successful')
        except Exception as e:
            print(e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif setView == 'profiles':
        return Response(CustomUser.objects.all().values())
    elif setView == 'times':
        time_of_day_dicts = [{time[0]: time[1]} for time in ReOccurance.TimeOfDay]
        return Response(time_of_day_dicts)
    elif setView == 'days':
        day_of_week_dicts = [{day[0]: day[1]} for day in ReOccurance.DayOfWeek]
        return Response(day_of_week_dicts)
    elif setView == 'weekOfMonth':
        week_dicts = [{week[0]: week[1]} for week in ReOccurance.WeekOfMonth]
        return Response(week_dicts)
    elif setView == 'getTask':
        data = ReOccurance.objects.all().order_by('-id')
        response = ReOccuranceSerializers(data, many=True).data
        return Response(response)
    elif setView == 'getSpecifcTask':
        username = request.data.get('username', False)
        username_id = get_object_or_404(CustomUser, username=username)
        allTask = ReOccurance.objects.filter(username=username_id)
        allTaskInstance = ReOccuranceSerializers(allTask, many=True)
        return Response(allTaskInstance.data)


@api_view(['POST','GET'])
def get_random_image(request):
    import numpy as np
    import cloudinary.api
    import cloudinary.uploader
    cloud_name = "dxhcnn7k3"
    api_key = "989734149712141"
    api_secret = "j6XSOzQQTfMeXTPXYQNXvOB8Kaw"

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    # Specify the folder in Cloudinary where your images are stored
    if request.data.get("setView") == "capturing_the_moments":
        folder = 'Capturing the Moments'
        amount = 200
    else:
        folder = 'raw-random'
        amount = 20
    # Fetch all images from the specified folder
    response = cloudinary.api.resources(type='upload', prefix=folder, max_results=500)['resources']
    # Convert the response to a NumPy array for easier handling
    numpyArray = np.array(response)

    # Initialize an empty list to store the selected image URLs
    selectedImageUrls = []

    # Loop until we have up to 5 unique image URLs
    while len(selectedImageUrls) < amount and len(selectedImageUrls) < len(numpyArray):
        # Randomly select an image URL
        randomImage = np.random.choice(numpyArray)
        imageUrl = randomImage['secure_url']
        # If the URL is not already in the selected list, add it
        if imageUrl not in selectedImageUrls:
            selectedImageUrls.append(imageUrl)
    # Return the list of selected image URLs as a DRF Response
    return Response({'image_urls': selectedImageUrls})


@api_view(['GET']) #updated 4/18
def update_project_meter(request):
    today_date = datetime.today()
    # Get the day of the week as an integer (Monday=0, Sunday=6)
    day_of_week_int = today_date.weekday()
    # Map integer representation to day name
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week_name = day_names[day_of_week_int]
    if day_of_week_name == "Thursday":
        eachProject = Project.objects.filter(enabled=True)
        if len(eachProject) == 0:
            print('no project to udpate')
            return Response('no project to update')
        emailData = []
        for eachProjectEntry in eachProject:
            startDate = eachProjectEntry.startDate
            dueDate = eachProjectEntry.dueDate
            date1 = datetime.strptime(startDate, "%m/%d/%Y")
            date2 = datetime.strptime(dueDate, "%m/%d/%Y")
            difference = date2.date() - date1.date()
            daysLeft = difference.days
            eachProjectEntryId = eachProjectEntry.id
            try:
                ProjectDeliverablesTotalCount = ProjectDeliverables.objects.filter(projectName=eachProjectEntryId, enabled=True).count()
                ProjectDeliverablesCountCompleted = ProjectDeliverables.objects.filter(projectName=eachProjectEntryId, deliverableCompleted=True, enabled=True).count()
                percantageOfCompleted = round(ProjectDeliverablesCountCompleted / ProjectDeliverablesTotalCount * 100)
                theProject = eachProject = Project.objects.filter(id=eachProjectEntryId, enabled=True)
            except Exception as e:
                print(e)
                print('no deliverables enabled')
                return Response('no deliverables enabled')
            if percantageOfCompleted >= 0.0 and percantageOfCompleted <= 33.0:
                try:
                    theProject.flag = 'red'
                    theProject.save()
                except Exception as e:
                    print(e)
            elif percantageOfCompleted > 33.0 and percantageOfCompleted <= 66.0:
                try:
                    theProject.flag = '#ecb753'  # Adjust flag as needed
                    theProject.save()
                except Exception as e:
                    print(e)
            elif percantageOfCompleted > 66.0 and percantageOfCompleted <= 100.0:
                try:
                    theProject.flag = 'green'  # Adjust flag as needed
                    theProject.save()
                except Exception as e:
                    print("error ", e)
            if eachProjectEntry.flag == '#ecb753':
                eachProjectEntry.flag = 'Yellow'
            emailData.append(
                    {
                        'id': eachProjectEntry.id,
                        'percantageOfCompleted':percantageOfCompleted,
                        'ProjectDeliverablesTotalCount':ProjectDeliverablesTotalCount,
                        'ProjectDeliverablesCountCompleted':ProjectDeliverablesCountCompleted,
                        'projectName':eachProjectEntry.name,
                        'daysLeft':daysLeft,
                        'projectStatus':eachProjectEntry.flag,
                    }
                )
        roles = Role.objects.get(name='Project Manager')
        projectManagersEmail = CustomUser.objects.filter(profile_access=roles).values_list('email', flat=True)
        emailDataText = "\n".join([f"Project Name: {item['projectName']}\nTotal Deliverables: {item['ProjectDeliverablesTotalCount']}\nCompleted Deliverables: {item['ProjectDeliverablesCountCompleted']}\nPercentage of Completed Deliverables: {item['percantageOfCompleted']}%\nDays Left: {item['daysLeft']}\nProject status code: {item['projectStatus']}\n" for item in emailData])
        subject = 'Weekly Project Status Updates'
        sender = 'Rise and Walk Ministry Team'
        message= f"""Hey there!

    We hope this message finds you feeling motivated and empowered. The RAW Leadership Team is excited to share with you an update on the progress of our ongoing projects. Please see the report below and let us know your thoughts on how we can continue to move forward and make a positive impact.

    {emailDataText}

    Should you have any questions or concerns, please don't hesitate to get in touch with us. We appreciate your continued support and look forward to working together towards our shared goals.
        """
        for eachProjectManager in projectManagersEmail:
            try:
                send_mail(
                    subject,
                    message,
                    sender,
                    [eachProjectManager],
                    fail_silently=True,
                )
            except Exception as e:
                print(e)
        return Response('successful')
    else:
        return Response('not successful')


@api_view(['GET','POST']) #updated 4/18
def deliverable_reminder(request):
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
    current_datetime = datetime.now()
    currentDate = current_datetime.strftime("%m/%d/%Y")
    currentDate = datetime.strptime(currentDate, "%m/%d/%Y")
    allDeliverables = ProjectDeliverables.objects.all()
    for eachDeliverable in allDeliverables:
        if eachDeliverable.deliverableCompleted == True:
            pass
        if eachDeliverable.markedForReview == True:
            pass
        else:
            date_object = datetime.strptime(eachDeliverable.deliverableEndDate, "%m/%d/%Y")
            difference = relativedelta(date_object,  currentDate)
            total_days_difference = difference.days + difference.months * 30 + difference.years * 365
            notifications(
                dName = eachDeliverable.deliverableName,
                pName = eachDeliverable.projectName,
                dOwner = eachDeliverable.deliverableOwner,
                dDetails = eachDeliverable.deliverableDetails,
                dStartDate = eachDeliverable.deliverableStartDate,
                dEndDate = eachDeliverable.deliverableEndDate,
                countDown = total_days_difference,
            )
    return Response(currentDate)


@api_view(['POST'])
def propose_project(request):
    setView = request.data.get('setView')

    if setView == 'getUserProfile':
        users = CustomUser.objects.all().values('first_name', 'last_name', 'username')
        return Response(list(users), status=status.HTTP_200_OK)

    elif setView == 'projectColors':
        colors = Project.objects.all().values_list('projectColor', flat=True).distinct()
        return Response(list(colors), status=status.HTTP_200_OK)

    elif setView == 'createProject':
        deliverables = request.data.get('deliverables', [])
        projectName = request.data.get('projectName')
        projectColor = request.data.get('projectColor')
        startDate = request.data.get('startDate')
        projectType = request.data.get('projectType')
        dueDate = request.data.get('dueDate')
        shortDescription = request.data.get('shortDescription')
        longDescription = request.data.get('longDescription')
        image = request.data.get('image')

        if not all([projectName, projectColor, startDate, projectType, dueDate, shortDescription, longDescription, image]):
            return Response({"error": "Missing required project fields."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            project_type_instance = ProjectType.objects.get(name=projectType)
        except ProjectType.DoesNotExist:
            return Response({"error": "Project type not found"}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            project = Project(
                name=projectName,
                projectColor=projectColor,
                startDate=startDate,
                dueDate=dueDate,
                shortDescription=shortDescription,
                longDescription=longDescription,
                image=image,
                projectType=project_type_instance,
            )
            project.save()
            for eachDeliverableOwner in deliverables:
                user_instance = CustomUser.objects.get(username=eachDeliverableOwner["owner"])
                project.projectStakeholders.add(user_instance)
            for deliverable_data in deliverables:
                owner_username = deliverable_data.get('owner')
                if not owner_username:
                    return Response({"error": "Owner username missing in deliverables"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    deliverableOwner = CustomUser.objects.get(username=owner_username)
                except CustomUser.DoesNotExist:
                    return Response({"error": f"Deliverable owner {owner_username} not found"}, status=status.HTTP_404_NOT_FOUND)

                deliverable = ProjectDeliverables(
                    deliverableName=deliverable_data.get('name'),
                    projectName=project,
                    deliverableColor=deliverable_data.get('color'),
                    deliverableOwner=deliverableOwner,
                    deliverableDetails=deliverable_data.get('details'),
                    deliverableStartDate=deliverable_data.get('startDate'),
                    deliverableEndDate=deliverable_data.get('endDate')
                )
                deliverable.save()
        return Response({"message": "Project and deliverables successfully created"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"error": "Invalid setView value"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def upload_image(request):
    if request.method == 'POST':
        import random
        import datetime
        import cloudinary.uploader

        try:
            cloud_name = "dxhcnn7k3"
            api_key = "989734149712141"
            api_secret = "j6XSOzQQTfMeXTPXYQNXvOB8Kaw"

            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            # If files were uploaded with unique keys or as an array under a single key
            for key in request.FILES.keys():
                uploaded_images = request.FILES.getlist(key)  # Get list of files for the current key
                folder_path = "raw-approval-needed"  # Define the target folder path on Cloudinary

                for uploaded_image in uploaded_images:
                    # Generate a unique name for each image
                    current_time_with_milliseconds = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    cleaned_time = current_time_with_milliseconds.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
                    random_number = str(random.randint(100000000000, 999999999999))
                    final_string = random_number + cleaned_time
                    new_file_name = final_string  # This will be the public_id of the image
                    # Upload to Cloudinary, specifying the folder path
                    cloudinary.uploader.upload(
                        uploaded_image,
                        folder=folder_path,  # Correct parameter for specifying the folder
                        public_id=new_file_name
                    )
            approver_role_id = Role.objects.get(name='Capturing The Moments Approver')
            approvers = CustomUser.objects.filter(profile_access=approver_role_id)
            for eachUser in approvers:
                print(f"==>> eachUser: {eachUser}")
                try:
                    token = PushToken.objects.get(username=eachUser).push_token
                except PushToken.DoesNotExist:
                    logger.error(f'Token not found for {eachUser.first_name}')
                except Exception as e:
                    logger.exception(f'Error fetching token for {eachUser.first_name}: {str(e)}')
                else:
                    message = f"Hi {eachUser.first_name}, there are a few pictures waiting for your approval to be uploaded to the app 📸📷"
                    send_push_message(token, message)
            return Response('successful')
        except Exception as e:
            print(e)
            return Response("unsuccesful")
    return Response('good')


@api_view(['POST'])
def project_cost(request):
    try:
        request.data.get('project_id', False)
        allCostReport = ProjectExpense.objects.values()
        return Response(allCostReport)
    except Exception as err:
        print(err)
        return Response('unsuccessful')

@api_view(['POST'])
def project_details(request):
    try:
        apiPostData = request.data.get('apiPostData', False)
        if apiPostData['setView'] == "stakeholder":
            # returns {'stakeholderFirstName': 'Joshua', 'stakeholderLastName': 'Dean', 'project_id': 44, 'setView': 'stakeholder'}
            project_id = apiPostData['project_id']
            stakeholderFirstName = apiPostData['stakeholderFirstName']
            # print(f"==>> stakeholderFirstName: {stakeholderFirstName}" )
            stakeholderLastName = apiPostData['stakeholderLastName']
            # print(f"==>> stakeholderLastName: {stakeholderLastName}")
            usernameInstance = CustomUser.objects.get(first_name=stakeholderFirstName, last_name=stakeholderLastName)
            # print(f"==>> username_id: {username_id}")
            projectDeliverables = ProjectDeliverables.objects.filter(projectName_id=project_id, deliverableOwner=usernameInstance).values(
                'deliverableName',
                'deliverableDetails',
                'deliverableOwner__first_name',
                'deliverableOwner__last_name',
                'deliverableOwner__username',
                'deliverableStatus',
                'deliverableColor',
                'id',
                'deliverableCompleted'
            )
            # print(projectDeliverables)
            return Response(projectDeliverables)
        else:
            return Response('no project match')
    except Exception as err:
            print(err)
            return Response('unsuccessful')

@api_view(['POST'])
def project_deliverables(request):
    try:
        project_id = request.data.get('project_id', False)
        try:
            projectDeliverables = ProjectDeliverables.objects.filter(projectName=project_id)
            serializer = ProjectDeliverablesSerializers(projectDeliverables, many=True)
            return Response (serializer.data)
        except Exception as e:
            print(e)
            return Response('unsuccessful')
    except Exception as err:
        print(err)
        return Response('unsuccessful')

@api_view(['POST']) #updated 4/19
def project_details_update(request):
    return Response('successful')

@api_view(['GET','POST'])
def deliverableStatus(request):
    value = request.data.get('value', False)
    project_deliverable_name = value['project_deliverable_name']
    try:
        obj = ProjectDeliverables.objects.get(id=project_deliverable_name)
        if not obj.markedForReview:
            obj.markedForReview = True
            obj.save(update_fields=['markedForReview'])
            message = 'Deliverable marked for review.'
        else:
            message = 'Deliverable was already marked for review.'
    except ObjectDoesNotExist:
        message = 'Deliverable does not exist.'
    return Response(message)

@api_view(['POST'])
def project_notes(request):
    try:
        deliverableId = request.data.get('deliverableId', False)
        deliverableNotes = ProjectNotes.objects.filter(
        project_deliverable_name_id=deliverableId
            ).values(
                'notes',
                'noteAuthor__first_name',
                'noteAuthor__last_name',
                'noteAuthor__username',
                'timeStamp'
            ).order_by('-id')
        return Response(deliverableNotes)
    except Exception as e:
        print(e)
        return Response('Unsuccessful')

@api_view(['GET'])
def announcements(request):
    try:
        announcements=Announcement.objects.all().values('announcementAuthor__first_name', 'announcementAuthor__last_name', 'announcementDate', 'announcement')
        return Response(announcements)
    except Exception as e:
        print(e)
        return Response('Unsuccessful')

@api_view(['POST'])
def my_task_creation(request):
    infoType = request.data.get('infoType', False)
    tasks = request.data.get('deliverables', [])
    if infoType == "createTask":
        ProjectDeliverables(
            taskName=tasks.get('name'),
            taskColor=tasks.get('color'),
            taskOwner=tasks.get('owner'),
            taskDetails=tasks.get('details'),
            taskStartDate=tasks.get('startDate'),
            taskEndDate=tasks.get('endDate'),
        )

@api_view(['POST'])
def create_account(request):
    # analytics(request, "New Account Created")
    try:
        if request.method == "POST":
            username = request.data.get("username", False)
            password = request.data.get("password", False)
            first_name = request.data.get("firstName", False)
            last_name = request.data.get("lastName", False)
            email = request.data.get("email", False)
            phone_number = request.data.get("phone_number", False)
            user = CustomUser.objects.create_user(
                username = username,
                password = password,
                first_name = first_name,
                last_name = last_name,
                email = email,
                phone_number = phone_number,
                )
            user.save()
            admin = CustomUser.objects.get(username='agentofgod')
            token = PushToken.objects.get(username=admin)
            username_id = CustomUser.objects.get(username=username)
            Stats.objects.create(
                username=username_id,
                total=0
            )
            send_push_message(token.push_token, f'{username} created a new account. Approval needed')
        return Response("successful")
    except IntegrityError as e:
        errorStringFormat = str(e)
        if "username" in errorStringFormat:
            error = "Username is being used, please try another email, or contact support tech.and.faith.contact@gmail.com"
            return Response(error)
        elif "profile_name" in errorStringFormat:
            error = "Profile name is being used, please try another profile name, or contact support tech.and.faith.contact@gmail.com"
            return Response(error)
        else:
            return Response("Error creating account. Please try again or contact support tech.and.faith.contact@gmail.com")

@api_view(['GET','POST'])
def deactivate(request):
    analytics(request, "Accounts Deactivated")
    try:
        username = request.data.get('username', False)
        userInfo = CustomUser.objects.filter(username=username).delete()
        if userInfo == (0, {}):
            print("error")
            return Response('unsuccessful')
        else:
            print("no error")
            return Response ('successful')
    except Exception as e:
        # print(e)
        return Response('unsuccessful')



@api_view(['POST', 'GET']) #5/31
def event(request):
    setView = request.data.get('setView', False)
    # print(request.data)
    try:
        if setView == "all_events":
            group = request.data.get('group', False)
            allRolesId = [Role.objects.get(name=eachRole).id  for eachRole in group]
            filteredEvents = Event.objects.filter(eventSubscribers__id__in=allRolesId, eventEnable=True).prefetch_related('eventFollower').distinct().order_by('-id')
            serializedData = EventSerializers(filteredEvents, many=True)
            apiResponse =  serializedData.data
            return Response(apiResponse)
        elif setView == "event_modification":
            id = request.data.get('id')
            eventName = request.data.get('eventName')
            eventDate = request.data.get('eventDate')
            eventNote = request.data.get('eventNote')
            eventLocation = request.data.get('eventLocation')
            eventDescription = request.data.get('eventDescription')
            eventFollower_ids = [f['id'] for f in request.data.get('eventFollower', [])]
            eventWatcher_ids = [w['id'] for w in request.data.get('eventWatcher', [])]
            eventNotification_ids = [n['id'] for n in request.data.get('eventNotification', [])]
            eventSubscribers_ids = [s['id'] for s in request.data.get('eventSubscribers', [])]
            followers = CustomUser.objects.filter(id__in=eventFollower_ids)
            watchers = CustomUser.objects.filter(id__in=eventWatcher_ids)
            notifications = CustomUser.objects.filter(id__in=eventNotification_ids)
            subscribers = Role.objects.filter(id__in=eventSubscribers_ids)

            with transaction.atomic():
                updateEvent, created = Event.objects.update_or_create(
                    id=id,
                    defaults={
                        'eventName': eventName,
                        'eventDate': eventDate,
                        'eventNote': eventNote,
                        'eventLocation': eventLocation,
                        'eventDescription': eventDescription,
                        # 'eventReoccuring': eventReoccuring
                    }
                )

                # Set ManyToMany relationships
                updateEvent.eventFollower.set(followers)
                updateEvent.eventWatcher.set(watchers)
                updateEvent.eventNotification.set(notifications)
                updateEvent.eventSubscribers.set(subscribers)
            if updateEvent:
                print('event updated')
                apiResponse = "updated"
            elif created:
                print('create event')
                apiResponse = "created"
            else:
                print('nothing happened')
                apiResponse = 'nothing'
        elif setView == "participant":
            username = request.data.get('username', False)
            event = request.data.get('event', False)
            buttonPressed = request.data.get('buttonPressed', False)
            apiResponse = 'error'
            if buttonPressed == 'notify':
                try:
                    event_id = Event.objects.get(id=event)
                    user_id = CustomUser.objects.get(username=username)
                    contacts = [eachContact.username for eachContact in event_id.eventNotification.all()]
                    if username in contacts:
                        return Response('already being notified')
                    re_occurance_id = ReOccurance.objects.get(taskName=event_id.eventName)
                    re_occurance_id.username.add(user_id)
                    event_id.eventNotification.add(user_id)
                    return Response('user notification added')
                except ReOccurance.DoesNotExist:
                    print('sdfsfsdfsf')
                except Exception as e:
                    print(e)
                    return Response('user not added')
            elif buttonPressed == 'following':
                try:
                    event_id = Event.objects.get(id=event)
                    user_id = CustomUser.objects.get(username=username)
                    contacts = [eachContact.username for eachContact in event_id.eventFollower.all()]
                    if username in contacts:
                        return Response('already following')
                    event_id.eventFollower.add(user_id)
                    return Response('user is following')
                except Exception as e:
                    print(e)
                    return Response('user not added')
        elif setView == "create_event":
            event_name = request.data.get('eventName')
            event_date = request.data.get('eventDate')
            event_note = request.data.get('eventNote')
            event_time = request.data.get('eventTime')
            event_location = request.data.get('eventLocation')
            event_description = request.data.get('eventDescription')
            event_subscriber_ids = request.data.get('eventSubscribers', [])
            event_image_url = request.data.get('eventImageUrl')
            # event_enable = request.data.get('eventEnable', False)
            event_reoccuring = request.data.get('eventReoccuring', False)
            # reoccuring_info_id = request.data.get('reoccuringInfo')
            event = Event.objects.create(
                eventName=event_name,
                eventDate=event_date,
                eventNote=event_note,
                eventTime=event_time,
                eventLocation=event_location,
                eventDescription=event_description,
                eventImageUrl=event_image_url,
                eventEnable=True,
                eventReoccuring=event_reoccuring,
            )
            if event_subscriber_ids:
                subscribers = Role.objects.filter(id__in=event_subscriber_ids)
                event.eventSubscribers.set(subscribers)
                send_event_notifications(event)
                return Response("successful")
        elif setView == "all_roles":
            all_roles = Role.objects.all()
            apiResponse = RoleSerializers(all_roles, many=True).data
        return Response(apiResponse)
    except Exception as e:
        print(e)
        return Response('error')



@api_view(['POST', 'GET']) #5/31
def questions(request):
    from datetime import timedelta
    from django.utils import timezone
    fields = ['stats','question', 'answer', 'rewardAmount', 'setView', 'questionAttempted', 'answeredCorrectly', 'username']
    stats, question, answer, rewardAmount, setView, questionAttempted, answeredCorrectly, username = (request.data.get(field, False) for field in fields)
    if setView == "create_questions":
        try:
            Questions.objects.create(
                question=question,
                answer=answer,
                rewardAmount=rewardAmount
            )
        except Exception as e:
            print('error')
            response = 'error'
        response = "successful"
    elif setView == "get_questions":
        all_question = Questions.objects.all()
        response = QuestionSerializer(all_question, many=True).data
    elif setView == "latest_question":
        latest_question = Questions.objects.filter(enabled=True).order_by('?').first()
        contacts = [eachContact.username for eachContact in latest_question.questionAnswered.all()]
        response = "pass" if username in contacts else QuestionSerializer(latest_question).data
    elif setView == "answer_queston":
        try:
            username_id = CustomUser.objects.get(username=username)
            question = Questions.objects.get(question=question)
            AnsweredQuestion.objects.create(
                username=username_id,
                question=question,
                questionAttempted=True,
                answeredCorrectly=answeredCorrectly
            )

            question.questionAnswered.add(username_id)
            if answeredCorrectly == True:
                currentStats = Stats.objects.get(username=username_id)
                Stats.objects.filter(username=username_id).update(
                    total = currentStats.total + question.rewardAmount
                )
            response = 'successful'
        except Exception as e:
            print(e)
            response = 'error'
    elif setView == "stats":
        allStats =  Stats.objects.all().order_by('-total')
        response = StatsSerializer(allStats, many=True).data
    elif setView == "personal_stats":
        username_id = CustomUser.objects.get(username=username)
        allStats =  Stats.objects.filter(username=username_id)
        response = StatsSerializer(allStats, many=True).data
    elif setView == "rewards":
        allRewards = Rewards.objects.all()
        response = RewardsSerializer(allRewards, many=True).data
    elif setView == "disable":
        response = "successfully hit the API"
        try:
            all_question = Questions.objects.filter(enabled=True)
            for eachQuestion in all_question:
                time_elapsed = timezone.now() - eachQuestion.date
                if time_elapsed > timedelta(hours=24):
                    Questions.objects.filter(id=eachQuestion.id).update(enabled=False)
                else:
                    pass
        except Exception as e:
            print(e)
    return Response(response)


@api_view(['POST']) #5/31
def survey(request):
    response = 'error'
    setView = request.data.get('setView', False)
    if setView == 'create':
        survey_name = request.data.get('surveyName', False)
        eventName = request.data.get('eventName', False)
        question1 = request.data.get('question1', False)
        question2 = request.data.get('question2', False)
        question3 = request.data.get('question3', False)
        question4 = request.data.get('question4', False)
        question5 = request.data.get('question5', False)

        try:
            event = Event.objects.get(eventName=eventName)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            event_survey_question = EventSurveyQuestion(
                surveyName=survey_name,
                eventName=event,
                question1=question1,
                question2=question2,
                question3=question3,
                question4=question4,
                question5=question5,
                enable=True
            )
            event_survey_question.save()
            process_survey_notifications(eventName, survey_name)
            return Response('successful')
        except Exception as e:
            print(e)
    if setView == 'getSurvey':
        username = request.data.get('username', False)
        try:
            survey = EventSurveyQuestion.objects.filter(enable=True).latest('id')
            username = CustomUser.objects.get(username="agentofgod")
            try:
                survey = SurveyViewed.objects.get(username=username, survey=survey.id, status=True)

            except Exception as e:
                print('none')
                response = EventSurveyQuestionSerializer(survey).data
        except Exception as e:
            print(e)
            return Response ('unsuccessful')
    if setView == 'saveSurvey':
        survey_name = request.data.get('surveyName', False)
        eventName = request.data.get('eventName', False)
        question1 = request.data.get('question1', False)
        question2 = request.data.get('question2', False)
        question3 = request.data.get('question3', False)
        question4 = request.data.get('question4', False)
        question5 = request.data.get('question5', False)
        username = request.data.get('username', False)
        anonymous = request.data.get('anonymous', False)
        # Retrieve the event instance
        try:
            # Retrieve the survey instance
            survey_instance = EventSurveyQuestion.objects.get(surveyName=survey_name)
            print(f"==>> survey_instance: {survey_instance}")

            # Determine the user
            if anonymous:
                user = CustomUser.objects.get(username=username)
                print(f"==>> user: {user}")
            else:
                user = CustomUser.objects.get(username='Development')
                print(f"==>> user: {user}")

            # Create the survey response
            event_survey_response = EventSurveyResponse(
                surveyName=survey_instance,
                username=user,
                answer1=question1,
                answer2=question2,
                answer3=question3,
                answer4=question4,
                answer5=question5
            )
            event_survey_response.save()
            print(f"==>> event_survey_response: {event_survey_response}")

            # Mark the survey as viewed
            SurveyViewed.objects.create(
                username=user,
                status=True,
                survey=survey_instance
            )

            return Response({'response': 'successful'}, status=status.HTTP_200_OK)
        except EventSurveyQuestion.DoesNotExist:
            return Response({'error': 'Survey not found'}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'An error occurred: {e}')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response (response)


@api_view(['GET'])
def reoccuring_reoccurance_notification(request):
    from django.utils import timezone
    from datetime import datetime, timedelta
    est = pytz.timezone('US/Eastern')
    now = timezone.now().astimezone(est)
    today = now.date()
    time_now = now.time()
    messages = []
    landing = {'screenView':'Stewardship'}
    # Get the current week of the month
    current_week = str(get_week_of_month(today))
    # Day of the week mapping

    day_of_week_map = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6,
    }
    # Condition 1: If it is Sunday and the week of the month matches
    if today.weekday() == 6 and now.hour == 15:  # Sunday
        upcoming_events = ReOccurance.objects.filter(week=current_week)
        client = Client(env("SID"), env("SIDTOKEN"))
        user_events = {}
        for event in upcoming_events:
            contacts = [eachContact.username for eachContact in event.username.all()]
            for eachUsername in contacts:
                if eachUsername not in user_events:
                    user_events[eachUsername] = []
                user_events[eachUsername].append(event)
        for eachUsername, events in user_events.items():
            user_info = CustomUser.objects.get(username=eachUsername)
            message = f"Hey there {user_info.first_name}. Time to start off the week fresh! Below are the RAW stewardship activities for this week 😊. You can add them to your calendar or reminders by pressing on the date and time\n\n"

            for event in events:
                message += f"Activity: {event.taskName}\nWhen: {event.dayOfWeek} {event.timeOfEvent}\n\n"

            message += "Once you complete the task, please mark it as complete on the RAW App.\n\nWe are praying for you, and you are important to us. Jesus got you and victory belongs to Jesus and you."
            try:
                client.messages.create(body=message, to=user_info.phone_number, from_='+14704678410')
            except Exception as e:
                print(e)
    # Get all events
    events = ReOccurance.objects.all()

    for event in events:
        def send_notification(countdown, event):
            if countdown == "2-days":
                message = f"You are 2 days away from the {event.taskName} activity. Thank you from RAW!"
            elif countdown == "Today":
                message = f"Today is the day for {event.taskName} activity. Check out the details in the in-app stewardship section"
            elif countdown == "Now":
                message = f"It's time for {event.taskName}. Let's goooo!🔥🔥"
            event_id = ReOccurance.objects.get(id=event.id)
            contacts = [eachContact.id for eachContact in event_id.username.all()]
            for eachContact in contacts:
                try:
                    eachContactToken = PushToken.objects.get(username=eachContact).push_token
                    send_push_message(eachContactToken, message, landing)
                except Exception as e:
                    print(e)

        event_time = datetime.strptime(event.timeOfEvent, '%H:%M').time()
        event_date_time_naive = datetime.combine(today, event_time)
        event_date_time = est.localize(event_date_time_naive)
        event_day = day_of_week_map[event.dayOfWeek]
        if event_date_time > now and now.hour == 22:
            # Condition 2: If it is 2 days prior to the event
            event_day = day_of_week_map[event.dayOfWeek]
            event_date_in_two_days = (today + timedelta(days=2)).weekday()
            if event_day == event_date_in_two_days:
                messages.append(f"Two days prior: {event.taskName}")
                send_notification("2-days", event)
        # Condition 3: If it is day of the event and 8am
        if today.weekday() == event_day and time_now.hour == 1:
            messages.append(f"Day of: {event.taskName}")
            send_notification("Today", event)
        # Condition 5: If it is the current date and hour
        if (today == event_date_time.date() and
                now.hour == event_date_time.hour and
                current_week == event.week and
                today.weekday() == day_of_week_map[event.dayOfWeek]):
                messages.append(f"Current hour: {event.taskName}")
                send_notification("Now", event)

    return Response({'messages': messages}, status=status.HTTP_200_OK)


@api_view(['GET']) # 06/06
def reoccuring_event_notification(request):
    from django.utils import timezone
    from datetime import datetime, timedelta
    est = pytz.timezone('US/Eastern')
    now = timezone.now().astimezone(est)
    messages = []
    landing = {'screenView':'Stewardship'}
    current_datetime_est = datetime.now(est)
    # Day of the week mapping
    today_date = current_datetime_est.date()
    # 2024-06-06
    current_time_est = datetime.now(est)
    # Get the current time in EST
    current_hour_est = current_time_est.hour

    events = Event.objects.filter(eventEnable=True)
    print(f"==>> events: {events}")
    if len(events) == 0:
        print('no event')
        return Response ('No event')
    def send_notification(countdown, event):
        if countdown == "1-day":
            message = f"You are 1 day away from the {event.eventName} activity. Thank you for your prayers and support"
        elif countdown == "Today":
            message = f"Today is the day for {event.eventName} activity. Check out the details in the in-app stewardship section"
        elif countdown == "Now":
            message = f"It's time for {event.eventName}. Let's goooo!🔥🔥"
        elif countdown == "Done":
            message = f"Earn Glory Coins by completing a quick survey for our {event.eventName} event that took place yesterday?"

        event_id = Event.objects.get(id=event.id)
        contacts = [eachContact.id for eachContact in event_id.eventNotification.all()]
        for eachContact in contacts:
            try:
                eachContactToken = PushToken.objects.get(username=eachContact).push_token
                send_push_message(eachContactToken, message, landing)
            except Exception as e:
                print(e)

    for event in events:
        try:
            date_object = datetime.strptime(event.eventDate, '%m/%d/%Y').date()
            event_time = datetime.strptime(event.eventTime, '%H:%M').time()
        except ValueError:
            print(f"Skipping event with invalid date format: {event.eventDate}")
            continue
        event_time = datetime.strptime(event.eventTime, '%H:%M').time()
        # date_object = datetime.strptime(event.eventDate, '%m/%d/%Y').date()
        event_hour = event_time.hour

        if today_date + timedelta(days=1) == date_object and now.hour == 10:
            messages.append(f"Two days prior at 10am for: {event.eventName}")
            print(f'1 day prior notice for {event.eventName}')
            send_notification("1-day", event)

        # 8am, day of.
        if today_date == date_object and now.hour == 8:
            messages.append(f"Day of at 8am for: {event.eventName}")
            print(f'8am reminder for {event.eventName} event')
            send_notification("Now", event)

        # event starts now
        if today_date == date_object and event_hour == current_hour_est:
            messages.append(f"Now is the start time for: {event.eventName}")
            print(f'Now Event for {event.eventName}')
            send_notification("Now", event)

        # one day after the event at 10am
        if date_object < today_date - timedelta(days=1) and current_hour_est == 17:
            messages.append(f"Event concluded for: {event.eventName}")
            print(f'event concluded for {event.eventName}')
            Event.objects.filter(id=event.id).update(
                eventEnable=False
            )
            send_notification("Done", event)
    return Response({'messages': messages}, status=status.HTTP_200_OK)
