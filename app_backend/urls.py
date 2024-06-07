from django.urls import path, include
from .views import *

urlpatterns = [
    path('project_info', project_info, name='project_info'),
    path('project_cost', project_cost, name='project_cost'),
    path('project_details', project_details, name='project_details'),
    path('project_notes', project_notes, name='project_notes'),
    path('project_details_update', project_details_update, name='project_details_update'),
    path('project_deliverables', project_deliverables, name='project_deliverables'),
    path('deliverableStatus', deliverableStatus, name='deliverableStatus'),
    path('update_deliverables', update_deliverables, name='update_deliverables'),
    path('update_project_meter', update_project_meter, name='update_project_meter'),
    path('test', test, name='test'),
    path('edit_deliverables', edit_deliverables, name='edit_deliverables'),
    path('deliverable_reminder', deliverable_reminder, name='deliverable_reminder'),
    path('announcements', announcements, name='announcements'),
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
    path('re_occurance_notification', re_occurance_notification, name='re_occurance_notification'),
    path('send_notifications', send_notifications, name='send_notifications'),
    path('allUsers', allUsers, name='allUsers'), #updated 4/23
    path('link_to_app', link_to_app, name='link_to_app'),
    path('alert', alert, name='alert'),
    path('send_blast_emails', send_blast_emails, name='send_blast_emails'),
    path('send_blast', send_blast, name='send_blast'),  #updated 4/8
    path('event', event, name='event'), #5/11
    path('accounts/', include('django.contrib.auth.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('reoccuring_event_notification', reoccuring_event_notification, name='reoccuring_event_notification'), #06/06
    path('reoccuring_reoccurance_notification', reoccuring_reoccurance_notification, name='reoccuring_reoccurance_notification'),
    path('questions', questions, name='questions'),
    path('survey', survey, name='survey'), #5/31
    path('send_blast_email_manually', send_blast_email_manually, name='send_blast_email_manually'),
    path('send_blast_notification_manually', send_blast_notification_manually, name='send_blast_notification_manually')
]