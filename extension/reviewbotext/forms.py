from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm


class ReviewBotSettingsForm(SettingsForm):
    BROKER_URL = forms.CharField(
        max_length=512,
        label=_("Broker URL"),
        help_text=_("The Celery configuration BROKER_URL"))
    ship_it = forms.BooleanField(
        required=False,
        label=_("Ship It!"),
        help_text=_("Ship it! If no issues raised."))
    open_issues = forms.BooleanField(
        required=False,
        label=_("Open Issues"),
        help_text=_("Should Review Bot open issues on comments."))
    comment_unmodified = forms.BooleanField(
        required=False,
        label=_("Comment on unmodified code"),
        help_text=_("Should comments be made to unmodified code."))
    rb_url = forms.URLField(
        label=_("Review Board URL"),
        help_text=_("URL of this Review Board instance."))
    user = forms.CharField(
        label=_("Username"),
        help_text=_("Username of the account Review Bot will use."))
    password = forms.CharField(
        label=_("Password"),
        help_text=_("Password of the account Review Bot will use."))
