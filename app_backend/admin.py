from .models import *
from django.contrib import admin


class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'browser', 'os', 'device', 'region', 'endpoint')

admin.site.register(Analytics, AnalyticsAdmin)
admin.site.register(PushToken)
admin.site.register(AutomatedNotification)
admin.site.register(CustomUser)

admin.site.register(Project)
admin.site.register(ProjectDetails)
admin.site.register(ProjectReporting)

