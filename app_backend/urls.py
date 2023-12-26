from django.urls import path, include
from .views import * 

def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('project_info', project_info, name='project_info'),
    path('project_cost', project_cost, name='project_cost'),
    path('project_details', project_details, name='project_details'),
    path('project_notes', project_notes, name='project_notes'),

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

    path('accounts/', include('django.contrib.auth.urls')),
    # for sentry testing
    path('__debug__/', include('debug_toolbar.urls')),

    path('send_blast_email_manually', send_blast_email_manually, name='send_blast_email_manually'),
    path('send_blast_notification_manually', send_blast_notification_manually, name='send_blast_notification_manually')
]
