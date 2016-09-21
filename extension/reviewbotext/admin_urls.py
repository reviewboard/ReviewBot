from __future__ import unicode_literals

from django.conf.urls import patterns, url

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import ReviewBotSettingsForm


urlpatterns = patterns(
    '',

    url(r'^$',
        'reviewboard.extensions.views.configure_extension',
        {
            'ext_class': ReviewBotExtension,
            'form_class': ReviewBotSettingsForm,
        }),
)
