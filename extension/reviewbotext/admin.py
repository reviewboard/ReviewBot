from django.contrib import admin

from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.models import ReviewBotTool


class ReviewBotToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'enabled')


# Get the ReviewBotExtension instance. We can assume it exists because
# this code is executed after the extension has been registered with
# the manager.
extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)

# Register with the extension's, not Review Board's, admin site.
extension.admin_site.register(ReviewBotTool, ReviewBotToolAdmin)
