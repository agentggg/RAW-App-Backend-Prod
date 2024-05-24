from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver
from .models import *
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from django.db.models import Q, Count, Min
import logging
logger = logging.getLogger(__name__)

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
                        send_push_message(pushToken, message, extra={'screenView':'Projects'})
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
                try:
                    projectName = instance.projectName.name
                    projectId = instance.projectName.id
                    project = Project.objects.get(id=projectId)
                except Project.DoesNotExist:
                    logger.error(f'Project with id {projectId} does not exist.')
                    return
                try:
                    deliverableOwner = instance.deliverableOwner.username
                    user_to_add = CustomUser.objects.get(username=deliverableOwner)
                    project.projectStakeholders.add(user_to_add)
                except CustomUser.DoesNotExist:
                    logger.error(f'User {deliverableOwner} does not exist.')
                    return
                try:
                    deliverableOwnerToken = CustomUser.objects.filter(username=deliverableOwner).values_list('id', flat=True).first()
                    deliverableOwnerFirstName = CustomUser.objects.filter(username=deliverableOwner).values_list('first_name', flat=True).first()
                except CustomUser.DoesNotExist:
                    logger.error(f'User {deliverableOwner} does not exist.')
                    return
                messageTrue = f'{deliverableOwnerFirstName}, you have a new deliverable for {projectName}: {deliverableName}'
                messageFalse = f'{deliverableOwnerFirstName}, the {deliverableName} for {projectName} project has been removed from your deliverables'
                status = messageTrue if instance.enabled else messageFalse
                try:
                    pushTokenQuery = PushToken.objects.filter(username_id=deliverableOwnerToken).values_list('push_token', flat=True)
                    pushToken = pushTokenQuery.first() if pushTokenQuery.exists() else None
                except Exception as e:
                    print(e)
                    return
                send_push_message(pushToken, status, extra={'screenView':'My Deliverables'})
                deliverableName = instance.deliverableName
                try:
                    stevensonName = CustomUser.objects.get(username='agentofgod')
                    deliverableNameInstance = ProjectDeliverables.objects.filter(deliverableName = deliverableName).first()
                except Exception as e:
                    print(e)
                    return
                notes = "In our project management app's comments section, we strive to foster a collaborative and respectful environment. We encourage users to share insights, feedback, and constructive criticism to enhance project outcomes. To maintain the quality of discussions, we ask all participants to adhere to our guidelines: refrain from posting any content that is offensive, coarse jokes, or unrelated to the project at hand. Personal attacks, disrespectful speech, and sharing of confidential information are strictly prohibited. Comments should contribute positively to the project, offering clear, relevant, and respectful input. We reserve the right to moderate and remove comments that violate these principles to ensure our community remains a productive space for all users."
                noteAuthor = stevensonName
                from datetime import datetime
                import pytz
                est_timezone = pytz.timezone('America/New_York')
                current_time_est = datetime.now(est_timezone)
                formatted_time = current_time_est.strftime('%m/%d/%Y %I:%M:%S %p')
                try:
                    ProjectNotes.objects.create(
                        project_deliverable_name=deliverableNameInstance,
                        notes = notes,
                        noteAuthor = noteAuthor,
                        timeStamp = formatted_time
                    )
                except Exception as e:
                    print(e)
                    return
        except sender.DoesNotExist:
            print('error')
            pass

@receiver(post_save, sender=ProjectNotes)
def notesNotification(sender, instance, **kwargs):
    if instance.pk:
        projectId = instance.project_deliverable_name_id
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
                    pass
                except Exception as e:
                    print(e)
            else:
                print('owner created notes')
            # Now, get all stakeholders for this project
            projectManager = CustomUser.objects.filter(profile_access=6)
            for stakeholder in projectManager:
                pushTokenQuery = PushToken.objects.filter(username_id=stakeholder).values_list('push_token', flat=True)
                for eachToken in pushTokenQuery:
                    pushToken = PushToken.objects.filter(push_token = eachToken).values_list('push_token')[0][0]
                    message = f"{instance.noteAuthor} added a new note to the {instance.project_deliverable_name.projectName} project for the {instance.project_deliverable_name.deliverableName} deliverables"
                    send_push_message(pushToken, message, extra={'screenView':"ViewNotes", "projectId":projectId})
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

@receiver(pre_save, sender=ProjectDeliverables)
def markedForReview(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.markedForReview != instance.markedForReview:
                deliverableName = instance.deliverableName
                print(instance.id)
                projectName = instance.projectName.name
                deliverableOwner = instance.deliverableOwner.username
                project_role = Role.objects.get(name="Project Manager")
                users_leadership_or_project_role = CustomUser.objects.filter(profile_access=project_role)
                for projectManagers in users_leadership_or_project_role:
                    deliverableOwnerToken = CustomUser.objects.filter(username=projectManagers).values_list('id', flat=True).first()
                    messageFalse = f'{deliverableOwner}, has completed the {deliverableName} for {projectName} project. Please review.'
                    pushTokenQuery = PushToken.objects.filter(username_id=deliverableOwnerToken).values_list('push_token', flat=True)[0]
                    send_push_message(pushTokenQuery, messageFalse, extra={'screenView':'My Deliverables'})
        except Exception as e:
            print(e, '>>>error')


@receiver(pre_save, sender=ProjectNotes)
def deleteDuplicates(sender, instance, **kwargs):
    duplicates = ProjectNotes.objects.values('notes', 'noteAuthor', 'project_deliverable_name') \
    .annotate(notes_count=Count('id'), min_id=Min('id')) \
    .filter(notes_count__gt=1)
    for item in duplicates:
        ProjectNotes.objects.filter(notes=item['notes'], noteAuthor=item['noteAuthor'], project_deliverable_name=item['project_deliverable_name']) \
            .exclude(id=item['min_id']) \
            .delete()


@receiver(post_save, sender=Event)
def newEvent(sender, instance, created, **kwargs):
    if created == False:
        pass
    else:
        try:
            id = instance.id
            event_id = Event.objects.get(id=id)
            contacts = [eachContact.id for eachContact in event_id.eventSubscribers.all()]
            for eachUserGroup in contacts:
                username = CustomUser.objects.filter(profile_access=eachUserGroup)
                for eachUsername in username:
                    token = PushToken.objects.get(username=eachUsername.id)
                    send_push_message(token.push_token, f"Check out the details of the newly published {instance.eventName} event.")
        except Exception as e:
            print(e)



# @receiver(post_save, sender=ProjectDeliverables)
# def updateProjectHealth(sender, instance, created, **kwargs):
#     if instance.pk: