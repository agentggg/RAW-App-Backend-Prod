from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver
from .models import *
from exponent_server_sdk import DeviceNotRegisteredError, PushClient, PushMessage, PushServerError, PushTicketError
from django.db.models import Q, Count, Min
import logging
logger = logging.getLogger(__name__)
from .serializers import *
from django.core.exceptions import ObjectDoesNotExist


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
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.enabled != instance.enabled:
                leadership_role = Role.objects.get(name="Leadership")
                project_role = Role.objects.get(name="Project Manager")
                users_leadership_or_project_role = CustomUser.objects.filter(Q(profile_access=leadership_role) | Q(profile_access=project_role))
                status = 'approved and added to the RAW Project docket' if instance.enabled else 'removed from the RAW project board'
                message = f'The RAW planning team has {status} the project {instance.name} is now {status}.'

                for user in users_leadership_or_project_role:
                    pushToken = PushToken.objects.filter(username=user).values_list('push_token', flat=True).first()
                    if pushToken:
                        send_push_message(pushToken, message, extra={'screenView':'Projects'})
        except sender.DoesNotExist:
            print("error")
            pass

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
                deliverableInformation = ProjectDeliverables.objects.filter(id=instance.project_deliverable_name.id).values(
                    'deliverableColor','deliverableCompleted','deliverableName','deliverableOwner__first_name','deliverableOwner__last_name','deliverableOwner__username','deliverableStatus','id'
                    )[0]
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
                    send_push_message(pushToken, message, extra={'screenView':"ViewNotes", "projectId":projectId, "deliverableInformation":deliverableInformation})
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

@receiver(post_save, sender=ProjectDeliverables) #updated app config stuff 4/24
def markedForReview(sender, instance, created, **kwargs):
    if not created and instance.tracker.has_changed('markedForReview'):
        if instance.tracker.previous('markedForReview') == False and instance.markedForReview == True:
            try:
                deliverableName = instance.deliverableName
                projectName = instance.projectName.name
                deliverableOwner = instance.deliverableOwner.username
                project_role = Role.objects.get(name="Project Manager")
                projectManagers = CustomUser.objects.filter(profile_access=project_role)

                pushTokens = PushToken.objects.filter(username__in=projectManagers).values_list('username_id', 'push_token')
                token_dict = dict(pushTokens)  # Optimizing token retrieval

                for manager in projectManagers:
                    pushTokenQuery = token_dict.get(manager.id)
                    if pushTokenQuery:
                        message = f'{deliverableOwner} has completed the {deliverableName} for {projectName} project. Please review.'
                        deliverableInformation = {
                            'deliverableColor': instance.deliverableColor,
                            'deliverableCompleted': instance.deliverableCompleted,
                            'deliverableName': instance.deliverableName,
                            'deliverableOwner__first_name': instance.deliverableOwner.first_name,
                            'deliverableOwner__last_name': instance.deliverableOwner.last_name,
                            'deliverableOwner__username': instance.deliverableOwner.username,
                            'deliverableStatus': instance.deliverableStatus,
                            'id': instance.id
                        }
                        send_push_message(pushTokenQuery, message, extra={'screenView': deliverableInformation})

            except Exception as e:
                logging.error(f'Error sending notification: {e}')
        else:
            # This else could log or handle cases where 'markedForReview' does not change as expected
            logging.info('No notification sent: "markedForReview" not changed from False to True.')

@receiver(post_save, sender=ProjectDeliverables) # updated appconfig, and settings for this to work  on 4/24
def completedDeliverable(sender, instance, created, **kwargs):
    if not created:  # This ensures we're not dealing with a new record, but an update
        try:
            deliverableName = instance.deliverableName
            print(f"==>> deliverableName: {deliverableName}")
        except Exception as e:
            print(e)


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


@receiver(post_save, sender=Event)
def send_notification_to_subscribers(sender, instance, created, **kwargs):
    if created:
        send_event_notifications(instance)


@receiver(m2m_changed, sender=Event.eventSubscribers.through)
def notify_subscribers_m2m(sender, instance, action, **kwargs):
    if action == "post_add":
        send_event_notifications(instance)

@receiver(post_save, sender=EventSurveyQuestion)
def send_survey(sender, instance, created, **kwargs):
    if created:
        try:
            landing = {'screenView': 'LandingPage'}
            event_instance = Event.objects.get(eventName=instance.eventName)
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
                # 'reoccuringInfo': event_instance.reoccuringInfo.id if event_instance.reoccuringInfo else None,
            }
            processed_users = set()

            def process_users(user_list, user_role):
                for eachUser in user_list:
                    print(eachUser)
                    if eachUser['id'] not in processed_users:
                        try:
                            userToken = PushToken.objects.get(username=eachUser['id']).push_token
                            send_push_message(userToken, f'Help the ministry by taking a quick survey for the {instance.eventName} event', landing)
                            processed_users.add(eachUser['id'])
                        except PushToken.DoesNotExist:
                            print(f"PushToken for {eachUser['username']} ({user_role}) does not exist.")
                        except Exception as e:
                            print(f"An error occurred while processing {user_role}: {e}")

            process_users(event_data['eventFollower'], 'eventFollower')
            process_users(event_data['eventWatcher'], 'eventWatcher')
            process_users(event_data['eventNotification'], 'eventNotification')

        except Event.DoesNotExist:
            print(f"Event with name {instance.eventName} does not exist.")



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

def camel_case_to_human_readable(name):
    s1 = re.sub('([a-z])([A-Z])', r'\1 \2', name)
    return re.sub('([A-Z])([A-Z][a-z])', r'\1 \2', s1).lower()

@receiver(pre_save, sender=ReOccurance)
def reoccurance_pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous = ReOccurance.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            field_name = field.name
            human_readable_field_name = camel_case_to_human_readable(field_name)
            if getattr(previous, field_name) != getattr(instance, field_name):
                if field_name == 'message':
                    return
                for user in instance.username.all():
                    try:
                        userToken = PushToken.objects.get(username=user).push_token
                        message = f"The {human_readable_field_name} has been changed in the {instance.taskName} activity"
                        landing = {'pageView': 'Stewardship'}
                        send_push_message(userToken, message, landing)
                    except ObjectDoesNotExist:
                        pass

@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous = Event.objects.get(pk=instance.pk)
        print(instance.eventName)
        event_enabled_change = previous.eventEnable == False and instance.eventEnable == True
        print(f"==>> event_enabled_change: {event_enabled_change}")
        if event_enabled_change:
            # Send a custom message when eventEnable changes from False to True
            subscriber_roles = instance.eventSubscribers.all()
            subscribers = CustomUser.objects.filter(profile_access__in=subscriber_roles).distinct()
            unique_users = {user for user in subscribers}
            print(f"==>> unique_users: {unique_users}")
            for user in unique_users:
                try:
                    userToken = PushToken.objects.get(username=user).push_token
                    message = f"The event {instance.eventName} has been re-added to the calendar. Go check it out."
                    landing = {'pageView': 'EventsHomepage'}
                    send_push_message(userToken, message, landing)
                except ObjectDoesNotExist:
                    pass

        for field in instance._meta.fields:
            field_name = field.name
            human_readable_field_name = camel_case_to_human_readable(field_name)
            if field_name not in ['eventFollower', 'eventWatcher', 'eventNotification', 'eventSubscribers', 'eventImageUrl', 'eventEnable']:
                if getattr(previous, field_name) != getattr(instance, field_name):
                    subscriber_roles = instance.eventSubscribers.all()
                    subscribers = CustomUser.objects.filter(profile_access__in=subscriber_roles).distinct()
                    unique_users = {user for user in subscribers}
                    for user in unique_users:
                        try:
                            userToken = PushToken.objects.get(username=user).push_token
                            message = f"The {human_readable_field_name} has been changed for the {instance.eventName} event"
                            landing = {'pageView': 'EventsHomepage'}
                            send_push_message(userToken, message, landing)
                        except ObjectDoesNotExist:
                            pass