from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm

from reviewbotext.models import ReviewBotTool


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


class ReviewBotToolForm(forms.ModelForm):
    class Meta:
        model = ReviewBotTool

    TOOL_OPTIONS_FIELDSET = 'Tool Specific Settings'

    def __init__(self, *args, **kwargs):
        super(ReviewBotToolForm, self).__init__(*args, **kwargs)

        self.tool_opt_form = None

        instance = kwargs.get('instance', None)

        if instance is None:
            return

        options = instance.tool_options
        settings = instance.tool_settings
        form_class = self._make_tool_opt_form(options, settings)
        self.tool_opt_form = form_class(self.data or None)

    def is_valid(self):
        """Returns whether or not the form is valid."""
        return (super(ReviewBotToolForm, self).is_valid() and
                self.tool_opt_form.is_valid())

    def save(self, commit=True, *args, **kwargs):
        tool = super(ReviewBotToolForm, self).save(commit=False,
                                                      *args, **kwargs)

        options = tool.tool_options
        settings = tool.tool_settings

        for option in options:
            field_name = option['name']
            settings[field_name] = self.tool_opt_form.cleaned_data[field_name]

        tool.tool_settings = settings

        if commit:
            tool.save()

        return tool

    def _make_tool_opt_form(self, options, settings):
        """Construct the tool specific settings form.

        Given the tool's tool_options, and tool_settings
        construct a new form class with the proper fields.
        """
        fields = {}
        for option in options:
            field_name = option['name']
            field_class = self._get_field_class(option['field_type'])
            field_options = option.get('field_options', {})

            option_value = settings.get(field_name, None)
            if option_value is not None:
                field_options['initial'] = option_value

            fields[field_name] = field_class(
                **field_options)

        return type('ReviewBotToolOptionsForm', (forms.Form,), fields)

    def _get_field_class(self, class_str):
        """Import and return the field class.

        Given the module path to a field class in class_str,
        imports the class and returns it.
        """
        field_class_path = str(class_str).split('.')
        if len(field_class_path) > 1:
            field_module_name = '.'.join(field_class_path[:-1])
        else:
            field_module_name = '.'

        field_module = __import__(field_module_name, {}, {},
                                field_class_path[-1])
        return getattr(field_module, field_class_path[-1])
