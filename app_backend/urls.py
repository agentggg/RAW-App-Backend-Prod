from django.urls import path, include
from .views import *

def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('project_info', project_info, name='project_info'),
    path('project_cost', project_cost, name='project_cost'),
    path('project_details', project_details, name='project_details'),
    path('project_notes', project_notes, name='project_notes'),
    path('project_details_update', project_details_update, name='project_details_update'),
    path('project_deliverables', project_deliverables, name='project_deliverables'),
    path('deliverableStatuses', deliverableStatuses, name='deliverableStatuses'),

    path('update_deliverables', update_deliverables, name='update_deliverables'),
    path('update_project_meter', update_project_meter, name='update_project_meter'),

    path('announcements', announcements, name='announcements'),

    path('re_occurance_notification', re_occurance_notification, name='re_occurance_notification'),
    path('re_occurance_notification_execution', re_occurance_notification_execution, name='re_occurance_notification_execution'),
    path('deliverable_reminder', deliverable_reminder, name='deliverable_reminder'),


    path('my_deliverables', my_deliverables, name='my_deliverables'),
    path('my_notes', my_notes, name='my_notes'),
    path('new_note', new_note, name='new_note'),

    path('propose_project', propose_project, name='propose_project'),
    path('upload_image', upload_image, name='upload_image'),
    path('get_random_image', get_random_image, name='get_random_image'),


    path('user_profile', user_profile, name='user_profile'),
    path('token_validation', token_validation, name='token_validation'),
    path('deactivate', deactivate, name='deactivate'),
    path('save_push_token', save_push_token, name='save_push_token'),
    path('create_account', create_account, name='create_account'),
    path('login_verification', login_verification, name='login_verification'),

    path('send_notifications', send_notifications, name='send_notifications'),

    path('link_to_app', link_to_app, name='link_to_app'),
    path('alert', alert, name='alert'),
    path('send_blast_emails', send_blast_emails, name='send_blast_emails'),

    path('test_api', test_api, name='test_api'),

    path('accounts/', include('django.contrib.auth.urls')),
    # for sentry testing
    path('__debug__/', include('debug_toolbar.urls')),

    path('send_blast_email_manually', send_blast_email_manually, name='send_blast_email_manually'),
    path('send_blast_notification_manually', send_blast_notification_manually, name='send_blast_notification_manually')
]
