from django.conf.urls import patterns
from django.contrib import admin

from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import ReviewBotToolForm
from reviewbotext.models import ReviewBotTool
from reviewbotext.views import refresh_tools


class ReviewBotToolAdmin(admin.ModelAdmin):
    form = ReviewBotToolForm
    list_display = [
        'name',
        'version',
        'enabled',
    ]
    readonly_fields = [
        'name',
        'entry_point',
        'version',
        'description',
        'in_last_update',
    ]

    fieldsets = (
        ('Tool Information', {
            'fields': (
                'name',
                'version',
                'entry_point',
                'description',
                'in_last_update',
                'enabled',
            ),
            'classes': ('wide',),
        }),
        ('Settings', {
            'fields': (
                'run_automatically',
                'allow_run_manually',
            ),
            'classes': ('wide',),
        }),
        (ReviewBotToolForm.TOOL_OPTIONS_FIELDSET, {
            'fields': (),
            'classes': ('wide',),
        }),
    )

    def get_urls(self):
        urls = super(ReviewBotToolAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^refresh/$', self.admin_site.admin_view(refresh_tools))
        )
        return my_urls + urls

    def has_add_permission(self, request):
        return False


# Get the ReviewBotExtension instance. We can assume it exists because
# this code is executed after the extension has been registered with
# the manager.
extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)

# Register with the extension's, not Review Board's, admin site.
extension.admin_site.register(ReviewBotTool, ReviewBotToolAdmin)
