from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponse
from django.template.context import RequestContext
from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import ToolForm
from reviewbotext.models import Tool


class ToolAdmin(admin.ModelAdmin):
    """Admin site definitions for the Tool model."""

    form = ToolForm

    list_display = [
        'name',
        'version',
        'in_last_update',
    ]
    list_filter = [
        'in_last_update',
    ]
    ordering = [
        'enabled',
        'in_last_update',
        'name',
        'version',
    ]
    readonly_fields = [
        'name',
        'version',
        'description',
        'in_last_update',
        'timeout',
    ]

    fieldsets = (
        ('Tool Information', {
            'fields': (
                'name',
                'version',
                'description',
                'in_last_update',
                'timeout',
            ),
            'classes': ('wide',),
        }),
    )

    def refresh_tools_view(self, *args, **kwargs):
        """Refresh the list of tools.

        This will mark all current tools as stale and ask the workers to
        send new tool information.

        Args:
            *args (tuple, unused):
                Unused positional arguments.

            **kwargs (dict, unused):
                Unused keyword arguments.

        Returns:
            django.http.HttpResponse:
            The result of the API call.
        """
        Tool.objects.all().update(in_last_update=False)
        ReviewBotExtension.instance.send_refresh_tools()

        # The caller is not sensitive to the contents. It's just looking for
        # a response.
        return HttpResponse('ok')

    def get_urls(self):
        urls = super(ToolAdmin, self).get_urls()

        my_urls = [
            url('^refresh/$',
                self.admin_site.admin_view(self.refresh_tools_view)),
        ]
        return my_urls + urls

    def has_add_permission(self, request):
        return False


# Register these admin pages with the extension's "Database" section, rather
# than Review Board as a whole. We can assume that the extension exists here
# because this code is only executed once the extension is enabled.
extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)
extension.admin_site.register(Tool, ToolAdmin)
