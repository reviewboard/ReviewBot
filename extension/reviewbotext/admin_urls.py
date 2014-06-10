from django.conf.urls import patterns

from reviewbotext.extension import ReviewBotExtension
from reviewbotext.forms import ReviewBotSettingsForm


urlpatterns = patterns(
    '',
    (
        r'^$', 'reviewboard.extensions.views.configure_extension',
        {
            'ext_class': ReviewBotExtension,
            'form_class': ReviewBotSettingsForm,
        }
    ))
