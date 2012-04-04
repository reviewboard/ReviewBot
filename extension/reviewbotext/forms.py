from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm


class ReviewBotSettingsForm(SettingsForm):
    BROKER_URL = forms.CharField(
        max_length=512,
        help_text=_("The Celery configuration BROKER_URL"))
    CELERY_RESULT_BACKEND = "amqp"
    ship_it = forms.BooleanField(
        help_text=_("Ship it! If no issues raised."))
    user = forms.CharField(
        help_text=_("Username of the account Review Bot will use."))
    password = forms.CharField(
        help_text=_("Password of the account Review Bot will use."))
