from ..models import *
from django.core.mail import send_mail, BadHeaderError
from backend.settings import EMAIL_HOST_USER
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError

def notifications(**kwargs):
    # print(kwargs)
    print((kwargs['dOwner']))
    try:
        pName = kwargs['pName']
        dName = kwargs['dName']
        dOwnerEmail = CustomUser.objects.get(username=kwargs['dOwner']).email
        print(f"==>> dOwnerEmail: {dOwnerEmail}")
        dOwnerFirstName = CustomUser.objects.get(username=kwargs['dOwner']).first_name
        # print(f"==>> dOwnerFirstName: {dOwnerFirstName}")
        dOwnerLastName = CustomUser.objects.get(username=kwargs['dOwner']).last_name
        # print(f"==>> dOwnerLastName: {dOwnerLastName}")
        dOwnerPushToken = PushToken.objects.get(username_id=kwargs['dOwner']).push_token
        stevensonInstance = CustomUser.objects.get(username='agentofgod')
        stevensonToken = PushToken.objects.get(username_id=stevensonInstance).push_token
        print(f"==>> dOwnerPushToken: {dOwnerPushToken}")
        # print(f"==>> dOwnerId: {dOwnerId}")
        print(kwargs['countDown'])
        if kwargs['countDown'] == 10:
            print('you got 10 days')
            emailMessage = f"""Hey there {dOwnerFirstName}!

The Rise and Walk project management team just wanted to touch base with you regarding the {pName} project. As we're getting closer to the deadline, we wanted to remind you about the {dName} deliverables that need your attention. This item is due in the next 10 days and is pretty crucial for the successful completion of the project.

Your input and expertise are super important to us, and we're counting on you to help us get everything done on time. Could you please take a look at this activity, add any notes you think are necessary, and mark them as "ready to close" once you've completed the task?

We're really grateful for your cooperation and dedication to this project and we're confident that with your efforts, we'll achieve our goals successfully. If you have any questions or need further clarification, just give us a shout by responding to this e-mail.

Thanks for your help, and let's work together to wrap up this project successfully!

Luke 16:10
"Whoever can be trusted with very little can also be trusted with much, and whoever is dishonest with very little will also be dishonest with much."

"""
            emailSubject = f"10 more days left to complete {dName} deliverable"
            sender_name = "RAW Ministry Communication Team"
            if sending_mail(emailSubject, emailMessage, [dOwnerEmail], sender_name):
                print('successfull sent email')
            else:
                print('Failed to send email.')
        elif kwargs['countDown'] == 7:
            print('you got 7 days')
            emailMessage = f"""Hey there {dOwnerFirstName}!

The Rise and Walk project management team just wanted to touch base with you regarding the {dName} deliverable coming up soon. I hope everything's going well with you! Our records show that the {dName} deliverables is due in the next 7 days that we could use your help on.

We know you're a rockstar and your input is super important to the success of this project. Would you mind taking a look at each deliverable, adding any notes, and marking them as "ready to close" when you're done reviewing them?

That would be a huge help and keep us on track to meet our deadlines. We appreciate your dedication to this project and know we can count on you to help us achieve our goals. If you have any questions or need clarification on anything, just let us know. Thanks so much, and let's get this project across the finish line together!

Thanks for your help, and let's work together to wrap up this project successfully!

Luke 16:10
"Whoever can be trusted with very little can also be trusted with much, and whoever is dishonest with very little will also be dishonest with much."

"""
            emailSubject = f"7 more days left to complete {dName} deliverable"
            sender_name = "RAW Ministry Communication Team"
            if sending_mail(emailSubject, emailMessage, [dOwnerEmail], sender_name):
                print('successfull sent email')
            else:
                print('Failed to send email.')
        elif kwargs['countDown'] == 4:
            print('you got 4 days')
            emailMessage = f"""Hey there {dOwnerFirstName}!

Just wanted to check in and remind you about the {dName} deliverable for the {pName}. This critical item is due in the next 4 days.

Your input and expertise are so important to the success of this project, and we're grateful for all your hard work so far.

Would you mind taking some time to review the deliverable, add any notes you think are necessary, and mark them as "ready to close" when you're done? 

It'll help us stay on track and meet our deadlines with ease. And, of course, if you have any questions or need any clarification, feel free to give me a shout.

Thanks so much for your cooperation and dedication to this project. Together, we'll get it done and achieve our goals successfully!

Luke 16:10
"Whoever can be trusted with very little can also be trusted with much, and whoever is dishonest with very little will also be dishonest with much."

"""
            emailSubject = f"Urgent! 4 more days left to complete {dName} deliverable"
            sender_name = "RAW Ministry Communication Team"
            if sending_mail(emailSubject, emailMessage, [dOwnerEmail], sender_name):
                print('successfull sent email')
            else:
                print('Failed to send email.')
        elif kwargs['countDown'] == 3:
            print('you got 3 days')
            emailMessage = f"""Hello, it's important that we address the {dName} deliverables for the {pName} project. We are approaching the deadline, and this item is due within the next 3 days which require your urgent attention. 

Our records show that your input is crucial to the successful completion of the project, and we're counting on your expertise to ensure that this deliverable is completed accurately and on time. 

Please review the deliverable, add any necessary notes, and mark them as "ready to close" once you've completed your review. Completing this tasks promptly is critical to stay on track and ensure that we meet our project deadlines effectively. 

Your cooperation and dedication to this project are greatly appreciated, and we're confident that with your efforts, we'll achieve our goals successfully. If you have any questions or need further clarification on any aspect of the deliverables, please don't hesitate to respond to this email
.
Thank you for your attention to this matter. We expect your prompt action to help us complete this project successfully.

Luke 16:10
"Whoever can be trusted with very little can also be trusted with much, and whoever is dishonest with very little will also be dishonest with much."

"""
            emailSubject = f"Urgent! 3 more days left to complete {dName} deliverable"
            sender_name = "RAW Ministry Communication Team"
            stevensonMessage = f"""{dName} for the {pName} is due in 3 days. Please contact {dOwnerFirstName}"""
            send_push_message(stevensonToken, stevensonMessage)
            if sending_mail(emailSubject, emailMessage, [dOwnerEmail], sender_name):
                print('successfull sent email')
            else:
                print('Failed to send email.')
        elif kwargs['countDown'] == 2:
            print('you got 2 days')
            stevensonMessage = f"""{dName} for the {pName} is due in 2 days. Please contact {dOwnerFirstName}"""
            dOwnerMessage = f"""{dName} for the {pName} is due in 2 days. Please update the note logs accordingly"""
            send_push_message(stevensonToken, stevensonMessage)
            send_push_message(dOwnerPushToken, dOwnerMessage)
        elif kwargs['countDown'] == 1:
            print('you got 1 day')
            stevensonMessage = f"""{dName} for the {pName} is due in 1 day. Please contact {dOwnerFirstName}"""
            dOwnerMessage = f"""{dName} for the {pName} is due in 1 days. Please update the note logs accordingly"""
            send_push_message(stevensonToken, stevensonMessage)
            send_push_message(dOwnerPushToken, dOwnerMessage)
        elif kwargs['countDown'] == 0:
            print('due today')
            stevensonMessage = f"""{dName} for the {pName} is due today. Please contact {dOwnerFirstName}"""
            dOwnerMessage = f"""{dName} for the {pName} is due today. Please update the note logs accordingly"""
            send_push_message(stevensonToken, stevensonMessage)
            send_push_message(dOwnerPushToken, dOwnerMessage)
        elif kwargs['countDown'] < 0:
            print('you are overdue') 
            stevensonMessage = f"""{dName} for the {pName} is going into red flag today. Please contact {dOwnerFirstName}"""
            dOwnerMessage = f"""{dName} for the {pName} is officially in red flag."""
            send_push_message(stevensonToken, stevensonMessage)
            send_push_message(dOwnerPushToken, dOwnerMessage)
    except Exception as e:
        print('error found >>> ', e)
        return

def sending_mail(emailSubject, emailMessage, emailRecipient, emailSender):

    try:
        # Attempt to send the email using Django's send_mail function
        send_mail(
            emailSubject,
            emailMessage,
            emailSender,
            emailRecipient,
            fail_silently=True,
            # You can add extra parameters like headers or attachments here
        )

        # If no exception is raised, the email was sent successfully
        return True
    except BadHeaderError as e:
        # BadHeaderError indicates that the email headers are not valid
        print('Invalid email headers:', e)
        return False
    except Exception as e:
        # Other exceptions may occur during email sending
        print('Error with sending email:', e)
        return False
    
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

def send_test_email():
    try:
        sender_name = "RAW Ministry Communication Team" 
        emailMessage = """Hey there {dOwnerFirstName}!

The Rise and Walk Ministry Project Management Team just wanted to touch base with you regarding the {pName} project. As we're getting closer to the deadline, we wanted to remind you about the {dName} deliverables that need your attention. This item is due in the next 10 days and is pretty crucial for the successful completion of the project.

Your input and expertise are super important to us, and we're counting on you to help us get everything done on time. Could you please take a look at this activity, add any notes you think are necessary, and mark them as "ready to close" once you've completed the task?

We are really grateful for your cooperation and dedication to this project and we are confident that with your efforts, we'll achieve our common goal successfully. If you have any questions or need further clarification, just give us a shout by responding to this e-mail.

Thanks for your help, and let's work together to wrap up this project successfully!

Luke 16:10 * "Whoever can be trusted with very little can also be trusted with much, and whoever is dishonest with very little will also be dishonest with much." *
"""
        emailSubject = "10 more days left to complete your deliverables"
            
        # Attempt to send the email using Django's send_mail function
        send_mail(
            emailSubject,
            emailMessage,
            sender_name, 
            ["stevensongerardeustache@outlook.com"],
            fail_silently=False,
            # You can add extra parameters like headers or attachments here
        )

        # If no exception is raised, the email was sent successfully
        return True
    except BadHeaderError as e:
        # BadHeaderError indicates that the email headers are not valid
        print('Invalid email headers:', e)
        return False
    except Exception as e:
        # Other exceptions may occur during email sending
        print('Error with sending email:', e)
        return False