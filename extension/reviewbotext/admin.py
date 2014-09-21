from django.conf.urls import patterns
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import (AutomaticRunGroupForm, ManualPermissionForm,
                                ToolForm)
from reviewbotext.models import (AutomaticRunGroup, ManualPermission, Profile,
                                 Tool)


class ProfileInline(admin.StackedInline):
    model = Profile
    # formset = ProfileFormset
    # form = ProfileForm
    extra = 0

    # fieldsets = (
    #     ('General', {
    #         'fields': (
    #             'name',
    #             'description',
    #         ),
    #         'classes': ('wide',),
    #     }),
    #     ('Execution Settings', {
    #         'fields': (
    #             'allow_manual',
    #         ),
    #         'classes': ('wide',),
    #     }),
    #     ('Review Settings', {
    #         'fields': (
    #             'ship_it',
    #             'open_issues',
    #             'comment_unmodified',
    #         ),
    #         'classes': ('wide',),
    #     }),
    #     (ProfileForm.TOOL_OPTIONS_FIELDSET, {
    #         'fields': (),
    #         'classes': ('wide',),
    #     }),
    # )

class ToolAdmin(admin.ModelAdmin):
    inlines = [
        ProfileInline,
    ]

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
    )

    def refresh_tools_view(self, request, template_name="refresh.html"):
        extension_manager = get_extension_manager()
        extension = extension_manager.get_enabled_extension(
            ReviewBotExtension.id)

        Tool.objects.all().update(in_last_update=False)
        extension.send_refresh_tools()

        return render_to_response(
            template_name,
            RequestContext(request, {},  current_app=self.admin_site.name))

    def get_urls(self):
        urls = super(ToolAdmin, self).get_urls()

        my_urls = patterns('',
            (
                r'^refresh/$',
                self.admin_site.admin_view(self.refresh_tools_view),
            ),
        )
        return my_urls + urls

    def has_add_permission(self, request):
        return False


class AutomaticRunGroupAdmin(admin.ModelAdmin):
    form = AutomaticRunGroupForm

    filter_horizontal = (
        'repository',
        'profile',
    )
    list_display = (
        'name',
        'file_regex',
    )
    raw_id_fields = (
        'local_site',
    )

    fieldsets = (
        (_('General Information'), {
            'fields': (
                'name',
                'file_regex',
                'local_site',
            ),
            'classes': ('wide',),
        }),
        (_('Tool Profiles'), {
            'description': _('<p>These tool profiles will be executed when '
                             'the provided file regex and repositories match '
                             'a review request.</p>'),
            'fields': (
                'profile',
            ),
        }),
        (_('Repositories'), {
            'description': _('<p>An AutomaticRunGroup will only cover the '
                             'repositories specified below.</p>'),
            'fields': (
                'repository',
            ),
        }),
    )


class ManualPermissionAdmin(admin.ModelAdmin):
    form = ManualPermissionForm

    list_display = (
        'user',
        'local_site',
        'allow',
    )
    raw_id_fields = (
        'user',
        'local_site',
    )

    fieldsets = (
        (_('General Information'), {
            'fields': (
                'user',
                'local_site',
            ),
            'classes': ('wide',),
        }),
        (_('Permissions'), {
            'fields': (
                'allow',
            ),
        }),
    )


# Get the ReviewBotExtension instance. We can assume it exists because
# this code is executed after the extension has been registered with
# the manager.
extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)

# Register with the extension's, not Review Board's, admin site.
extension.admin_site.register(Tool, ToolAdmin)
extension.admin_site.register(AutomaticRunGroup, AutomaticRunGroupAdmin)
extension.admin_site.register(ManualPermission, ManualPermissionAdmin)
