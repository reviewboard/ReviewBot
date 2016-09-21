from __future__ import unicode_literals

from django.conf.urls import patterns, url
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
    """Admin site definitions for the tool profiles."""

    model = Profile
    extra = 0


class ToolAdmin(admin.ModelAdmin):
    """Admin site definitions for the Tool model."""

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

    def refresh_tools_view(self, request, template_name='refresh.html'):
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

        my_urls = patterns(
            '',
            url('^refresh/$',
                self.admin_site.admin_view(self.refresh_tools_view)))
        return my_urls + urls

    def has_add_permission(self, request):
        return False


class AutomaticRunGroupAdmin(admin.ModelAdmin):
    """Admin site definitions for the AutomaticRunGroup model."""

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
    """Admin site definitions for the ManualPermission model"""
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


# Register these admin pages with the extension's "Database" section, rather
# than Review Board as a whole. We can assume that the extension exists here
# because this code is only executed once the extension is enabled.
extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)
extension.admin_site.register(Tool, ToolAdmin)
extension.admin_site.register(AutomaticRunGroup, AutomaticRunGroupAdmin)
extension.admin_site.register(ManualPermission, ManualPermissionAdmin)
