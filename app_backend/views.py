from django.db import IntegrityError
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.http import JsonResponse
from .models import *
from .tasks import *
import environ
env = environ.Env()
environ.Env.read_env()
from datetime import datetime
from django.core.mail import send_mail
from rest_framework import status
from user_agents import parse
import pytz
from django.db.models import Prefetch
from collections import defaultdict
import json
from django.db.models import Prefetch

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
def send_notifications(request):  # sourcery skip: avoid-builtin-shadow
    analytics(request, "Sent Push Notification")
    message = request.data.get('message', False)
    setView = request.data.get('setView', False)
    if setView == "friendNotification":
        contactType = request.data.get('contactType', False)
        if contactType == 'username':
            contactDetail = request.data.get('contactDetail', False) #returns the new friend username
            contactUsername = CustomUser.objects.filter(profile_name=contactDetail).values_list('id')[0][0] #returns the new friend profile id number
            try:
                token = PushToken.objects.filter(username=contactUsername).values_list('push_token', flat=True)[0]
            except Exception as e:
                print('error')
                token = ""
    if token == "":
        return Response('noToken')
    else:
        send_push_message(token, message, extra=None)
        return Response('dispatched')



@api_view(['POST'])
def login_verification(request):
    serializer = ObtainAuthToken.serializer_class(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'email': user.email,
        'profile_name': user.profile_name,
        'premium': user.premium,
        'active': user.is_active
    })

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
    # retrieves front end usrname
    username_id = CustomUser.objects.filter(username=username).values("first_name","last_name","username","email")
    # retrieves org account owner info from DB
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

@api_view(['POST'])
def project_info(request):
    infoType = request.data.get('infoType', False)
    if infoType == 'project':
        watchers_prefetch = Prefetch('watchers', queryset=CustomUser.objects.only('first_name', 'last_name', 'id', 'username', 'color'))
        all_projects = Project.objects.prefetch_related(watchers_prefetch)
        projects_data = []
        for project in all_projects:
            project_data = {
                'id': project.id,
                'name': project.name,
                'flag': project.flag,
                'dueDate': project.dueDate,
                'shortDescription': project.shortDescription,
                'longDescription': project.longDescription,
                'image': project.image,
                'color': project.color,
                'initation': project.initation,
                'planning': project.planning,
                'execution': project.execution,
                'live': project.live,
                'completed': project.completed,
                'review': project.review,
                'type': project.projectType,
                'startDate': project.startDate,
                'watchers': [
                    {
                        'first_name': watcher.first_name,
                        'last_name': watcher.last_name,
                        'id': watcher.id,
                        'username': watcher.username,
                        'color': watcher.color
                    }
                    for watcher in project.watchers.all()
                ]
            }
            projects_data.append(project_data)
        return Response(projects_data)
    return Response(None)

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
        project_id = request.data.get('project_id', False)
        if project_id == False:
            api_post_data_str = request.data.get('apiPostData')
            api_post_data = json.loads(api_post_data_str)
            stakeholder = api_post_data.get('stakeholder')
            project_id = api_post_data.get('project_id')
            username_id = CustomUser.objects.get(username=stakeholder)
            project_details = ProjectDetails.objects.filter(name=project_id, deliverableOwner=username_id).values(
                'name__name',
                'deliverableName',
                'deliverableColor',
                'deliverableDetails',
                'deliverableOwner__first_name', 
                'deliverableOwner__last_name',
                'deliverableOwner__username',
                'watchers__username',           
                'deliverableStatus',
                'id' 
            ) 
            print(project_details)
        project_details = ProjectDetails.objects.filter(name=project_id).values(
            'name__name',
            'deliverableName',
            'deliverableDetails',
            'deliverableOwner__first_name', 
            'deliverableOwner__last_name',
            'deliverableOwner__username',
            'watchers__username',           
            'deliverableStatus',
            'id',
            'name'
        )  
        unique_usernames = defaultdict(dict)     
        filtered_project_details = []
        for detail in project_details:
            username = detail['deliverableOwner__username']
            if username not in unique_usernames:
                unique_usernames[username] = detail
                filtered_project_details.append(detail)

        return Response(filtered_project_details)
    except Exception as err:
            print(err)
            return Response('unsuccessful')

@api_view(['POST'])
def project_notes(request):
    try:
        deliverableId = request.data.get('deliverableId', False)
        print(f"==>> deliverableId: {deliverableId}")
        deliverableNotes = ProjectNotes.objects.filter(project_details_name=deliverableId).values()
        print(f"==>> deliverableNotes: {deliverableNotes}")
        return Response(deliverableNotes)
    except Exception as e:
        print(e)
        return Response('Unsuccessful')

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
            # phone_number = request.data.get("phoneNumber", False)
            profile_name = request.data.get("profileName", False)
            user = CustomUser.objects.create_user(
                username = username,
                password = password,
                first_name = first_name,
                last_name = last_name,
                email = email,
                # phone_number = phone_number,
                profile_name = profile_name
                )
            user.save()
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
