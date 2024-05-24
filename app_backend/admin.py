from .models import *
from django.contrib import admin


class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'browser', 'os', 'device', 'region', 'endpoint')

admin.site.register(Analytics, AnalyticsAdmin)
admin.site.register(PushToken)
admin.site.register(AutomatedNotification)
admin.site.register(CustomUser)
admin.site.register(ProjectExpense)
admin.site.register(Project)
admin.site.register(ProjectDeliverables)
admin.site.register(ProjectNotes)
admin.site.register(ProjectType)
admin.site.register(Role)
admin.site.register(Announcement)
admin.site.register(ReOccurance)
admin.site.register(Event) #5/11
admin.site.register(Questions) #5/24
admin.site.register(AnsweredQuestion) #5/24
admin.site.register(Stats) #5/24
admin.site.register(Rewards) #5/24
admin.site.register(EventNotification)