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
environ.Env.read_env()
from datetime import datetime
from django.core.mail import send_mail
from rest_framework import status
from user_agents import parse
import pytz
from collections import defaultdict
import json
from django.core.exceptions import ObjectDoesNotExist
from .reuseableFunctions.deliverableReminders import notifications, send_test_email

@api_view(['GET'])
def test_api(request):
    send_test_email()
    return Response('test')

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


@api_view(['POST','GET'])
def re_occurance_notification(request):
    setView = request.data.get('setView', False)
    if setView == 'createTask':
        username = request.data.get('username', False)
        message = request.data.get('deliverableDetails', False)
        timeSlot = request.data.get('reminderTimeSelected', False)
        dayOfWeek = request.data.get('reminderDaySelected', False)
        deliverableName = request.data.get('deliverableName', False)
        week = request.data.get('week', False)
        try:
            username_instance = CustomUser.objects.get(username=username)
            ReOccurance.objects.create(
                username=username_instance,
                message=message,
                timeSlot=timeSlot,
                dayOfWeek=dayOfWeek,
                taskName=deliverableName,
                week=week
            )
        except Exception as e:
            print(e)
            return Response({'error': 'Error with submission'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'successful': 'successful submission'}, status=status.HTTP_200_OK)
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
        return Response(ReOccurance.objects.all().values('username__username','message', 'timeSlot','dayOfWeek','taskName','id'))

@api_view(['POST'])
def re_occurance_notification_execution(request):
    from datetime import datetime
    import calendar
    # Get current date and time
    now = datetime.now()
    # Get current day of the week
    today = now.strftime('%A')
    # Get current hour in am/pm format
    current_hour_ampm = now.strftime('%I%p').lower()
    # Create a timezone object for EST
    est = pytz.timezone('US/Eastern')
    # Get the current time in UTC
    now_utc = datetime.now(pytz.utc)
    # Convert the current time to EST
    now_est = now_utc.astimezone(est)
    # Format the time in the desired format and convert to lowercase
    current_hour_ampm = now_est.strftime('%I%p').lower()
    first_day_of_month_weekday, _ = calendar.monthrange(now_est.year, now_est.month)
    day_of_month = now_est.day
    # Calculate week number of the month
    week_number = ((day_of_month + first_day_of_month_weekday - 1) // 7) + 1
    # integer format
    try:
        allEntries = ReOccurance.objects.all()
        for eachEntries in allEntries:
            print(eachEntries.taskName)
            try:
                if eachEntries.dayOfWeek == today:
                    print('found for today')
                    if week_number == int(eachEntries.week):
                        print('found for the Week Of Month')
                        if eachEntries.timeSlot == current_hour_ampm:
                            print('found for the current hour')
                            username_instance = CustomUser.objects.get(username=eachEntries.username)
                            userToken = PushToken.objects.filter(username_id=username_instance).values_list('push_token', flat=True)[0]
                            message = eachEntries.message
                            send_push_message(userToken, message)
                        else:
                            print('not for this hour')
                    else:
                        print('not for this week')
                else:
                    print('not for today')
            except Exception as e:
                print(f'error {e}')
                return('error')
    except Exception as e:
        print(f'error {e}')
    return Response('successful')

@api_view(['GET','POST'])
def update_project_meter(request):
    today_date = datetime.today()
    # Get the day of the week as an integer (Monday=0, Sunday=6)
    day_of_week_int = today_date.weekday()
    # print(f"==>> day_of_week_int: {day_of_week_int}")
    # Map integer representation to day name
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_of_week_name = day_names[day_of_week_int]
    # print(f"==>> day_of_week_name: {day_of_week_name}")
    if day_of_week_name == "Tuesday":
        # print("Today is:", day_of_week_name)
        eachProject = Project.objects.all()
        emailData = []
        # thirtyThree = []
        # sixtySix = []
        for eachProjectEntry in eachProject:
            # print(f"==>> eachProjectEntry: {eachProjectEntry}")      
            startDate = eachProjectEntry.startDate
            dueDate = eachProjectEntry.dueDate
            date1 = datetime.strptime(startDate, "%m/%d/%Y")
            date2 = datetime.strptime(dueDate, "%m/%d/%Y")
            difference = date2.date() - date1.date()
            daysLeft = difference.days
            eachProjectEntryId = eachProjectEntry.id
            try:
                ProjectDeliverablesTotalCount = ProjectDeliverables.objects.filter(projectName=eachProjectEntryId, enabled=True).count()
                # print(f"==>> ProjectDeliverablesTotalCount: {ProjectDeliverablesTotalCount}")
                ProjectDeliverablesCountCompleted = ProjectDeliverables.objects.filter(projectName=eachProjectEntryId, deliverableCompleted=True, enabled=True).count()
                # print(f"==>> ProjectDeliverablesCountCompleted: {ProjectDeliverablesCountCompleted}")
                percantageOfCompleted = round(ProjectDeliverablesCountCompleted / ProjectDeliverablesTotalCount * 100)
                theProject = eachProject = Project.objects.get(id=eachProjectEntryId)
                # print(f"==>> theProject: {theProject}")
            except Exception as e:
                print(e)
                print('no deliverables enabled')
            if percantageOfCompleted >= 0.0 and percantageOfCompleted <= 33.0:
                # print('this is 0% through 33%')
                try: 
                    # print(theProject.flag)
                    theProject.flag = 'red'  # Adjust flag as needed
                    theProject.save()
                    # print(theProject.flag)
                except Exception as e:
                    print(e)
            elif percantageOfCompleted > 33.0 and percantageOfCompleted <= 66.0:
                # print('this is between 33% through 66%')
                try: 
                    # print(theProject.flag)
                    theProject.flag = '#ecb753'  # Adjust flag as needed
                    theProject.save()
                    # print(theProject.flag)
                except Exception as e:
                    print(e)
            elif percantageOfCompleted > 66.0 and percantageOfCompleted <= 100.0:
                # print('this is between 66% through 100%')
                try: 
                    # print(theProject.flag)
                    theProject.flag = 'green'  # Adjust flag as needed
                    theProject.save()
                    # print(theProject.flag)
                except Exception as e:
                    print(e)
            if eachProjectEntry.flag == '#ecb753':
                # print('sdfdsf')
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
        # print(f"==>> roles: {roles}")
        projectManagersEmail = CustomUser.objects.filter(profile_access=roles).values_list('email', flat=True)
        # print(f"==>> projectManagers: {projectManagers}")
        emailDataText = "\n".join([f"Project Name: {item['projectName']}\nTotal Deliverables: {item['ProjectDeliverablesTotalCount']}\nCompleted Deliverables: {item['ProjectDeliverablesCountCompleted']}\nPercentage of Completed Deliverables: {item['percantageOfCompleted']}%\nDays Left: {item['daysLeft']}\nProject status code: {item['projectStatus']}\n" for item in emailData])
        # print(f"==>> zeroText: {zeroText}")
        # thirtyThreeText = "\n".join([f"Project Name: {item['projectName']}\nTotal Deliverables: {item['ProjectDeliverablesTotalCount']}\nCompleted Deliverables: {item['ProjectDeliverablesCountCompleted']}\nPercentage of Completed Deliverables: {item['percantageOfCompleted']}%\nDays Left: {item['daysLeft']}\nProject status code: {item['projectStatus']}\n" for item in thirtyThree])
        # # print(f"==>> thirtyThreeText: {thirtyThreeText}")
        # sixtySixText = "\n".join([f"Project Name: {item['projectName']}\nTotal Deliverables: {item['ProjectDeliverablesTotalCount']}\nCompleted Deliverables: {item['ProjectDeliverablesCountCompleted']}\nPercentage of Completed Deliverables: {item['percantageOfCompleted']}%\nDays Left: {item['daysLeft']}\nProject status code: {item['projectStatus']}\n" for item in sixtySix])
        # # print(f"==>> sixtySixText: {sixtySixText}")  
        subject = 'Weekly Project Status Updates'
        sender = 'Rise and Walk Ministry Team'
        message= f"""Hey there! 

We hope this message finds you feeling motivated and empowered. The RAW Leadership Team is excited to share with you an update on the progress of our ongoing projects. Please see the report below and let us know your thoughts on how we can continue to move forward and make a positive impact. 

{emailDataText}

Should you have any questions or concerns, please don't hesitate to get in touch with us. We appreciate your continued support and look forward to working together towards our shared goals.
        """
        for eachProjectManager in projectManagersEmail:
            # print(eachProjectManager)
            # print(message)
            send_mail(
                subject,
                message,
                sender,  # Use Django admin email as the sender
                [eachProjectManager],  # Recipient's email address
                fail_silently=True,  # Raise exceptions for errors
            )
            # pushTokens = PushToken.objects.filter(username=eachProjectManager).values_list('push_token', flat=True)[0]
            # print(f"==>> pushTokens: {pushTokens}")
            # send_push_message()
            pass 
        return Response('ran successful, today') 
    else:
        return Response('not today') 



@api_view(['GET'])
def deliverable_reminder(request):
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
    current_datetime = datetime.now()
    # print(f"==>> current_datetime: {current_datetime}")
    currentDate = current_datetime.strftime("%m/%d/%Y")
    currentDate = datetime.strptime(currentDate, "%m/%d/%Y")
    # print(f"==>> currentDate: {currentDate}")
    allDeliverables = ProjectDeliverables.objects.all()
    # print(allDeliverables)
    for eachDeliverable in allDeliverables:
        # print(eachDeliverable.deliverableName)
        # print(eachDeliverable.deliverableEndDate)
        date_object = datetime.strptime(eachDeliverable.deliverableEndDate, "%m/%d/%Y")
        # print(f"==>> date_object: {date_object}")
        difference = relativedelta(date_object,  currentDate)
        # print(f"==>> difference: {difference}")
        total_days_difference = difference.days + difference.months * 30 + difference.years * 365
        # print(f"==>> total_days_difference: {total_days_difference}")
        x = notifications(
            dName = eachDeliverable.deliverableName,
            pName = eachDeliverable.projectName,
            dOwner = eachDeliverable.deliverableOwner,
            dDetails = eachDeliverable.deliverableDetails,
            dStartDate = eachDeliverable.deliverableStartDate,
            dEndDate = eachDeliverable.deliverableEndDate,
            countDown = total_days_difference
        )
        # print(x)

    return Response(currentDate)


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
    projectName = request.data.get('projectName', False)
    deliverables = request.data.get('deliverables', False)
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




@api_view(['POST'])
def login_verification(request):
    from rest_framework.exceptions import ValidationError
    from django.contrib.auth.models import User
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
        # Handle validation errors from serializer.is_valid()
        return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        # Handle case where the user does not exist
        return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Catch any other unexpected errors
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        projectInfo = ProjectDeliverables.objects.filter(projectName=projectId).select_related('projectType').prefetch_related('projectStakeholders').values()
        projectInfo = list(projectInfo)
        seen = set()
        unique_projects = []

        for item in projectInfo:
            if item['id'] not in seen:
                seen.add(item['id'])
                unique_projects.append(item)
        return Response(unique_projects)
    elif infoType == 'stakeholders':
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
    return Response(projectInfo)

@api_view(['POST'])
def update_deliverables(request):
    try:
        deliverables = request.data.get('deliverables', [])
        project_id = request.data.get('projectName')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        new_deliverables = []
        with transaction.atomic():
            for deliverable_data in deliverables:
                owner_username = deliverable_data.get('owner')
                if not owner_username:
                    return Response({"error": "Owner username missing in deliverables"}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    deliverableOwner = CustomUser.objects.get(username=owner_username)
                except CustomUser.DoesNotExist:
                    return Response({"error": f"Deliverable owner {owner_username} not found"}, status=status.HTTP_404_NOT_FOUND)

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

    except ObjectDoesNotExist:
        return Response({"error": "Invalid data provided"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                'deliverableStartDate','deliverableEndDate'
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
                    deliverableEndDate=deliverable_data.get('endDate'),
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

            current_time_with_milliseconds = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            cleaned_time = current_time_with_milliseconds.replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
            random_number = str(random.randint(100000000000, 999999999999))
            final_string = random_number + cleaned_time
            new_file_name = final_string

            uploaded_image = request.FILES['image']
            upload_result = cloudinary.uploader.upload(uploaded_image, public_id=new_file_name)

            url = upload_result['secure_url']


            return Response(url)
        except Exception as e:
            return Response("unsuccesful")
    return Response('good')

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
    folder = 'raw-random'

    # Fetch all images from the specified folder
    response = cloudinary.api.resources(type='upload', prefix=folder, max_results=500)['resources']

    # Convert the response to a NumPy array for easier handling
    numpyArray = np.array(response)

    # Initialize an empty list to store the selected image URLs
    selectedImageUrls = []

    # Loop until we have up to 5 unique image URLs
    while len(selectedImageUrls) < 30 and len(selectedImageUrls) < len(numpyArray):
        # Randomly select an image URL
        randomImage = np.random.choice(numpyArray)
        imageUrl = randomImage['secure_url']
        # If the URL is not already in the selected list, add it
        if imageUrl not in selectedImageUrls:
            selectedImageUrls.append(imageUrl)

    # Return the list of selected image URLs as a DRF Response
    return Response({'image_urls': selectedImageUrls})


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
        return Response(project_details)
    except Exception as err:
        print(err)
        return Response('unsuccessful')

@api_view(['POST'])
def project_details_update(request):
    project_id = request.data.get('project_id', False)
    print(f"==>> project_id: {project_id}")
    json_string = project_id
    data = json.loads(json_string)
    editableStatus = data['editableStatus']
    editableNotes = data['editableNotes']
    timestamp = data['time']
    status = data['status']
    deliverableId = data['id']
    try:
        projectStatus = ProjectDetails.objects.get(id=deliverableId)
        projectNotes = ProjectNotes.objects.get(id=deliverableId)
        print(f"==>> projectNotes: {projectNotes}")
        'no changes' if editableStatus == projectStatus.deliverableStatus else ProjectDetails.objects.filter(id=deliverableId).update(deliverableStatus=editableStatus)
        'no changes' if editableNotes == projectStatus.deliverableStatus else ProjectDetails.objects.filter(id=deliverableId).update(deliverableStatus=editableStatus)
    except Exception as e:
        print(e)
        return Response('error')
    return Response('successful')

@api_view(['GET'])
def deliverableStatuses(request):
    choices = [value for key, value in ProjectDetails.STATUS_CHOICES]
    return Response(choices)

@api_view(['POST'])
def project_notes(request):
    try:
        deliverableId = request.data.get('deliverableId', False)
        try:
            deliverableNotes = ProjectNotes.objects.filter(
            project_deliverable_name_id=deliverableId
                ).values(
                    'notes',
                    'noteAuthor__first_name',
                    'noteAuthor__last_name',
                    'noteAuthor__username',
                    'timeStamp'
                )
            return Response(deliverableNotes)
        except Exception as e:
            print(e)
            return Response('unsuccessful')
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
            # phone_number = request.data.get("phoneNumber", False)
            user = CustomUser.objects.create_user(
                username = username,
                password = password,
                first_name = first_name,
                last_name = last_name,
                email = email,
                # phone_number = phone_number,
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