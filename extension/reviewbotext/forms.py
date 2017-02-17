from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from djblets.forms.fields import ConditionsField
from reviewboard.integrations.forms import IntegrationConfigForm
from reviewboard.reviews.conditions import ReviewRequestConditionChoices

from reviewbotext.models import Tool
from reviewbotext.widgets import ToolOptionsWidget


class ToolForm(forms.ModelForm):
    """Form for the :py:class:`~reviewbotext.models.Tool` model."""

    class Meta:
        model = Tool


class ReviewBotConfigForm(IntegrationConfigForm):
    """Form for configuring Review Bot.

    This allows administrators to set up a Review Bot configuration for running
    tools against code changes based on the specified conditions.
    """

    COMMENT_ON_UNMODIFIED_CODE_DEFAULT = False
    OPEN_ISSUES_DEFAULT = True
    MAX_COMMENTS_DEFAULT = 30

    #: When to run this configuration.
    conditions = ConditionsField(
        ReviewRequestConditionChoices,
        label=_('Conditions'),
        required=False)

    #: What to run when this configuration matches.
    tool = forms.ModelChoiceField(
        queryset=Tool.objects.filter(enabled=True),
        label=_('Tool'))

    #: Whether the tool should comment on code which hasn't been modified.
    comment_on_unmodified_code = forms.BooleanField(
        label=_('Comment on unmodified code'),
        required=COMMENT_ON_UNMODIFIED_CODE_DEFAULT)

    #: Whether this tool should open issues.
    open_issues = forms.BooleanField(
        label=_('Open issues'),
        required=False,
        initial=OPEN_ISSUES_DEFAULT)

    #: Maximum number of comments to make.
    max_comments = forms.IntegerField(
        label=_('Maximum Comments'),
        help_text=_('The maximum number of comments to make at one time. If '
                    'the tool generates more than this number, a warning will '
                    'be shown in the review. If this is set to a large value '
                    'and a tool generates a large number of comments, the '
                    'resulting page can be very slow in some browsers.'),
        initial=MAX_COMMENTS_DEFAULT)

    def __init__(self, *args, **kwargs):
        """Initialize the form.

        Args:
            *args (tuple):
                Arguments for the form.

            **kwargs (dict):
                Keyword arguments for the form.
        """
        super(ReviewBotConfigForm, self).__init__(*args, **kwargs)

        from reviewbotext.extension import ReviewBotExtension
        extension = ReviewBotExtension.instance

        self.css_bundle_names = [extension.get_bundle_id('integration-config')]
        self.js_bundle_names = [extension.get_bundle_id('integration-config')]

    def load(self):
        """Load the form."""
        if 'tool_options' not in self.fields:
            self.fields['tool_options'] = forms.CharField(
                widget=ToolOptionsWidget(self.fields['tool'].queryset))

        super(ReviewBotConfigForm, self).load()

    def serialize_tool_field(self, value):
        """Serialize the tool field.

        This takes the value from the :py:attr:`tool field <tool>` and
        converts it to a JSON-serializable format.

        Args:
            value (reviewbotext.models.Tool):
                The value to serialize.

        Returns:
            int:
            The primary key of the selected tool.
        """
        return value.pk

    def deserialize_tool_field(self, value):
        """Deserialize the tool field.

        This takes the serialized version (pks) and turns it back into a Tool
        object.

        Args:
            value (list of int):
                The serialized value.

        Returns:
            reviewbotext.models.Tool:
            The deserialized value.
        """
        try:
            return Tool.objects.get(pk=value)
        except Tool.DoesNotExist:
            raise ValidationError('Tool with pk %s does not exist' % value)

    class Meta:
        fieldsets = (
            (_('What review requests should be reviewed?'), {
                'description': _(
                    'You can choose which review requests would be reviewed '
                    'by choosing the repositories and groups to match '
                    'against.'
                ),
                'fields': ('conditions',),
            }),
            (_('What tool should be run?'), {
                'fields': ('tool',),
            }),
            (_('Tool options'), {
                'fields': ('comment_on_unmodified_code',
                           'open_issues',
                           'max_comments',
                           'tool_options'),
            }),
        )
