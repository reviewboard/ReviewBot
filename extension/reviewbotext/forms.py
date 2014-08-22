from django import forms
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm

from reviewbotext.models import Tool, Profile


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


class ProfileFormset(forms.models.BaseInlineFormSet):
    def __init__(self, **kwargs):
        self.tool_options = kwargs.get('instance').tool_options
        return super(ProfileFormset, self).__init__(**kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['tool_options'] = self.tool_options
        print "CONSTRUCTING A FORM"
        print kwargs
        print ""
        return super(ProfileFormset, self)._construct_form(i, **kwargs)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

    TOOL_OPTIONS_FIELDSET = 'Tool Specific Settings'

    def __init__(self, *args, **kwargs):
        self.options = kwargs.pop('tool_options', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
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
        return (super(ProfileForm, self).is_valid() and
                self.tool_opt_form.is_valid())

    def save(self, commit=True, *args, **kwargs):
        tool_profile = super(ProfileForm, self).save(commit=False,
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

            # If this field specifies which widget it wants to use, we must
            # instantiate the widget and pass it to the field constructor.
            widget = option.get('widget', None)

            if widget is not None:
                widget_class = self._get_widget_class(widget['type'])

                widget_attrs = widget.get('attrs', None)
                widget = widget_class(attrs=widget_attrs)

            field_options = option.get('field_options', {})
            option_value = settings.get(field_name, None)

            if option_value is not None:
                field_options['initial'] = option_value

            # Note: We pass the widget separately instead of including it in
            # field_options because field_options must be serializable.
            # (field_options is referenced by the tool's actual tool_options
            # JSON field.)
            fields[field_name] = field_class(widget=widget, **field_options)

        return type('ReviewBotToolOptionsForm', (forms.Form,), fields)

    def _get_field_class(self, class_str):
        """Import and return the field class.

        Given the module path to a field class in class_str, imports the class
        and returns it. If class_str does not specify a valid field class, an
        exception is raised.
        """
        field_class = self._get_class(class_str)

        if not issubclass(field_class, Field):
            raise TypeError('%s is not a Field class.' % class_str)

        return field_class

    def _get_widget_class(self, widget_str):
        """Imports and returns the widget class.

        If widget_str does not specify a valid widget class, an exception is
        raised.
        """
        widget_class = self._get_class(widget_str)

        if not issubclass(widget_class, Widget):
            raise TypeError('%s is not a Widget class.' % widget_str)

        return widget_class

    def _get_class(self, class_str):
        """Imports and returns the class, given the module path to a class."""
        class_path = str(class_str).split('.')

        if len(class_path) > 1:
            module_name = '.'.join(class_path[:-1])
        else:
            module_name = '.'

        module = __import__(module_name, {}, {}, class_path[-1])
        return getattr(module, class_path[-1])
