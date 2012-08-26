from django.conf.urls import patterns
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import ReviewBotToolForm
from reviewbotext.models import ReviewBotTool


class ReviewBotToolAdmin(admin.ModelAdmin):
    form = ReviewBotToolForm
    list_display = [
        'name',
        'version',
        'run_automatically',
        'in_last_update',
    ]
    list_editable = [
        'run_automatically',
    ]
    list_filter = [
        'in_last_update',
        'run_automatically',
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
    ]

    fieldsets = (
        ('Tool Information', {
            'fields': (
                'name',
                'version',
                'description',
                'in_last_update',
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

    def refresh_tools_view(self, request, template_name="refresh.html"):
        extension_manager = get_extension_manager()
        extension = extension_manager.get_enabled_extension(
            ReviewBotExtension.id)

        ReviewBotTool.objects.all().update(in_last_update=False)
        extension.send_refresh_tools()

        return render_to_response(
            template_name,
            RequestContext(request, {},  current_app=self.admin_site.name))

    def get_urls(self):
        urls = super(ReviewBotToolAdmin, self).get_urls()

        my_urls = patterns('',
            (
                r'^refresh/$',
                self.admin_site.admin_view(self.refresh_tools_view),
            ),
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
