from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import *
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from django.db.models import Count
from django.db.models import Q


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


@receiver(pre_save, sender=Project)
def enable_project(sender, instance, **kwargs):
    if instance.pk:  # Check if this is an update
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.enabled != instance.enabled:
                leadership_role = Role.objects.get(name="Leadership")
                project_role = Role.objects.get(name="Project Manager")

                # Use Q object to create an OR condition
                users_leadership_or_project_role = CustomUser.objects.filter(Q(profile_access=leadership_role) | Q(profile_access=project_role))
                status = 'approved and added to the RAW Project docket' if instance.enabled else 'removed from the RAW project board'
                message = f'The RAW planning team has {status} the project {instance.name} is now {status}.'

                for user in users_leadership_or_project_role:
                    pushToken = PushToken.objects.filter(username=user).values_list('push_token', flat=True).first()
                    if pushToken:
                        send_push_message(pushToken, message)
        except sender.DoesNotExist:
            print("error")
            pass  # This is a new instance, so there's no 'enabled' state change to check

@receiver(pre_save, sender=ProjectDeliverables)
def enable_deliverables(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.enabled != instance.enabled:  # Check if 'enabled' has changed
                deliverableName = instance.deliverableName
                projectName = instance.projectName.name  # Assuming 'Project' has a 'name' field
                deliverableOwner = instance.deliverableOwner.username
                deliverableOwnerToken = CustomUser.objects.filter(username=deliverableOwner).values_list('id', flat=True).first()
                deliverableOwnerFirstName = CustomUser.objects.filter(username=deliverableOwner).values_list('first_name', flat=True).first()
                messageTrue = f'{deliverableOwnerFirstName}, you have a new deliverable for {projectName}: {deliverableName}'
                messageFalse = f'{deliverableOwnerFirstName}, the {deliverableName} for {projectName} project has been removed from your deliverables'
                status = messageTrue if instance.enabled else messageFalse
                pushTokenQuery = PushToken.objects.filter(username_id=deliverableOwnerToken).values_list('push_token', flat=True)
                pushToken = pushTokenQuery.first() if pushTokenQuery.exists() else None
                send_push_message(pushToken, status)
                stevensonName = CustomUser.objects.get(username='agentofgod')
                deliverableName = instance.deliverableName
                deliverableNameInstance = ProjectDeliverables.objects.filter(deliverableName = deliverableName).first()
                notes = "In our project management app's comments section, we strive to foster a collaborative and respectful environment. We encourage users to share insights, feedback, and constructive criticism to enhance project outcomes. To maintain the quality of discussions, we ask all participants to adhere to our guidelines: refrain from posting any content that is offensive, coarse jokes, or unrelated to the project at hand. Personal attacks, disrespectful speech, and sharing of confidential information are strictly prohibited. Comments should contribute positively to the project, offering clear, relevant, and respectful input. We reserve the right to moderate and remove comments that violate these principles to ensure our community remains a productive space for all users."
                noteAuthor = stevensonName
                from datetime import datetime
                import pytz
                est_timezone = pytz.timezone('America/New_York')
                current_time_est = datetime.now(est_timezone)
                formatted_time = current_time_est.strftime('%m/%d/%Y %I:%M:%S %p')
                ProjectNotes.objects.create(
                    project_deliverable_name=deliverableNameInstance,
                    notes = notes,
                    noteAuthor = noteAuthor,
                    timeStamp = formatted_time
                )
        except sender.DoesNotExist:
            print('error')
            pass

@receiver(post_save, sender=ProjectNotes)
def notesNotification(sender, instance, **kwargs):
    if instance.pk:
        message = """In our project management app's comments section, we strive to foster a collaborative and respectful environment. We encourage users to share insights, feedback, and constructive criticism to enhance project outcomes. To maintain the quality of discussions, we ask all participants to adhere to our guidelines: refrain from posting any content that is offensive, coarse jokes, or unrelated to the project at hand. Personal attacks, disrespectful speech, and sharing of confidential information are strictly prohibited. Comments should contribute positively to the project, offering clear, relevant, and respectful input. We reserve the right to moderate and remove comments that violate these principles to ensure our community remains a productive space for all users."""
        if instance.notes == message:
            print('skipping')
            return
        print('not skipping')
        try:
                if instance.project_deliverable_name.deliverableOwner != instance.noteAuthor:
                    owner = instance.project_deliverable_name.deliverableOwner
                    ownerToken = CustomUser.objects.get(username=owner)
                    try:
                        pushToken = PushToken.objects.filter(username_id = ownerToken).values_list('push_token')[0][0]
                        print(pushToken)
                        pass
                    except Exception as e:
                        print(e)
                else:
                    print('owner created notes')
                # Now, get all stakeholders for this project
                print('owner created notes')
                projectManager = CustomUser.objects.filter(profile_access=6)
                print(f"==>> projectManager: {projectManager}")
                # Iterate through stakeholders to get their names
                for stakeholder in projectManager:
                    pushTokenQuery = PushToken.objects.filter(username_id=stakeholder).values_list('push_token', flat=True)
                    for eachToken in pushTokenQuery:
                        pushToken = PushToken.objects.filter(push_token = eachToken).values_list('push_token')[0][0]
                        print("pushToken")
                        message = f"{instance.noteAuthor} added a new note to the {instance.project_deliverable_name.projectName} project for the {instance.project_deliverable_name.deliverableName} deliverables"
                        send_push_message(pushToken, message)
        except sender.DoesNotExist:
            print('error')
            pass

@receiver(post_save, sender=ProjectDeliverables)
def automatedNotes(sender, instance, created, **kwargs):
        if instance.pk:
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                if old_instance.enabled != instance.enabled:
                    stevensonName = CustomUser.objects.get(username='agentofgod')
                    deliverableName = instance.deliverableName
                    deliverableNameInstance = ProjectDeliverables.objects.filter(deliverableName = deliverableName).first()
                    notes = "In our project management app's comments section, we strive to foster a collaborative and respectful environment. We encourage users to share insights, feedback, and constructive criticism to enhance project outcomes. To maintain the quality of discussions, we ask all participants to adhere to our guidelines: refrain from posting any content that is offensive, coarse jokes, or unrelated to the project at hand. Personal attacks, disrespectful speech, and sharing of confidential information are strictly prohibited. Comments should contribute positively to the project, offering clear, relevant, and respectful input. We reserve the right to moderate and remove comments that violate these principles to ensure our community remains a productive space for all users."
                    noteAuthor = stevensonName
                    from datetime import datetime
                    import pytz
                    est_timezone = pytz.timezone('America/New_York')
                    current_time_est = datetime.now(est_timezone)
                    formatted_time = current_time_est.strftime('%m/%d/%Y %I:%M:%S %p')
                    ProjectNotes.objects.create(
                        project_deliverable_name=deliverableNameInstance,
                        notes = notes,
                        noteAuthor = noteAuthor,
                        timeStamp = formatted_time
                    )
            except sender.DoesNotExist:
                print('error')
                pass