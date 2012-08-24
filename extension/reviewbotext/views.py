from django.shortcuts import render_to_response
from django.template.context import RequestContext

from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.models import ReviewBotTool


def refresh_tools(request, template_name="refresh.html"):
    extension_manager = get_extension_manager()
    extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)

    ReviewBotTool.objects.all().update(in_last_update=False)
    extension.send_refresh_tools()

    return render_to_response(template_name, RequestContext(request, {
    }))
