from django import forms
from django.utils.translation import ugettext as _

from djblets.extensions.forms import SettingsForm

from reviewbotext.models import Tool, ToolProfile


class ReviewBotSettingsForm(SettingsForm):
    BROKER_URL = forms.CharField(
        max_length=512,
        label=_("Broker URL"),
        help_text=_("The Celery configuration BROKER_URL"))
    max_comments = forms.IntegerField(
        required=False,
        label=_("Maximum Comments"),
        help_text=_("The maximum number of comments allowed per review. "
                    "If a review exceeds this maximum, the extra comments "
                    "will be truncated and a warning will be displayed in "
                    "the review. Large values can cause browsers to slow "
                    "considerably if a tool generates many comments."))
    user = forms.IntegerField(
        label=_("User id"),
        help_text=_("The id of the user account Review Bot will use."))


class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool


class ToolProfileFormset(forms.models.BaseInlineFormSet):
    def __init__(self, **kwargs):
        self.tool_options = kwargs.get('instance').tool_options
        return super(ToolProfileFormset, self).__init__(**kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['tool_options'] = self.tool_options
        print "CONSTRUCTING A FORM"
        print kwargs
        print ""
        return super(ToolProfileFormset, self)._construct_form(i, **kwargs)


class ToolProfileForm(forms.ModelForm):
    class Meta:
        model = ToolProfile

    TOOL_OPTIONS_FIELDSET = 'Tool Specific Settings'

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('tool_options', None)
        super(ToolProfileForm, self).__init__(*args, **kwargs)
        self.tool_opt_form = None

        if self.options is None:
            return

        options = self.options
        instance = kwargs.get('instance', None)
        settings = {}

        if instance:
            settings = instance.tool_settings

        form_class = self._make_tool_opt_form(options, settings)
        self.tool_opt_form = form_class(self.data or None)

    def is_valid(self):
        """Returns whether or not the form is valid."""
        return (super(ToolProfileForm, self).is_valid() and
                self.tool_opt_form.is_valid())

    def save(self, commit=True, *args, **kwargs):
        tool_profile = super(ToolProfileForm, self).save(commit=False,
                                                         *args, **kwargs)

        # options = tool_profile.tool_options
        options = self.options
        settings = tool_profile.tool_settings

        for option in options:
            print option
            field_name = option['name']
            settings[field_name] = self.tool_opt_form.cleaned_data[field_name]

        tool_profile.tool_settings = settings

        if commit:
            tool_profile.save()

        return tool_profile


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

            fields[field_name] = field_class(**field_options)

        print fields
        return type('ReviewBotToolOptionsForm', (forms.Form,), fields)

    def _get_field_class(self, class_str):
        """Import and return the field class.

        Given the module path to a field class in class_str,
        imports the class and returns it.

        TODO: It might be a good idea to check if the class
        is actually a field.
        """
        field_class_path = str(class_str).split('.')
        if len(field_class_path) > 1:
            field_module_name = '.'.join(field_class_path[:-1])
        else:
            field_module_name = '.'

        field_module = __import__(field_module_name, {}, {},
                                field_class_path[-1])
        return getattr(field_module, field_class_path[-1])