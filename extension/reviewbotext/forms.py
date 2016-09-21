from __future__ import unicode_literals

import re

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.utils.translation import ugettext as _
from djblets.extensions.forms import SettingsForm
from reviewboard.scmtools.models import Repository

from reviewbotext.models import (AutomaticRunGroup, ManualPermission, Profile,
                                 Tool)


class ReviewBotSettingsForm(SettingsForm):
    """Settings form for Review Bot."""

    broker_url = forms.CharField(
        max_length=512,
        label=_('Broker URL'),
        help_text=_('The Celery configuration BROKER_URL'))

    max_comments = forms.IntegerField(
        required=False,
        label=_('Maximum Comments'),
        help_text=_('The maximum number of comments allowed per review. '
                    'If a review exceeds this maximum, the extra comments '
                    'will be truncated and a warning will be displayed in '
                    'the review. Large values can cause browsers to slow '
                    'considerably if a tool generates many comments.'))

    user = forms.IntegerField(
        label=_('User ID'),
        help_text=_('The id of the user account Review Bot will use.'))


class ToolForm(forms.ModelForm):
    """Form for the :py:class:`~reviewbotext.models.Tool` model."""

    class Meta:
        model = Tool


class ProfileForm(forms.ModelForm):
    """Form for the :py:class:`~reviewbotext.models.Profile` model."""

    TOOL_OPTIONS_FIELDSET = 'Tool Specific Settings'

    def __init__(self, tool_options=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        self.options = tool_options

        if tool_options is not None:
            if 'instance' in kwargs:
                settings = kwargs['instance'].tool_settings
            else:
                settings = {}

            form_class = self._make_tool_opt_form(tool_options, settings)
            self.tool_opt_form = form_class(self.data or None)
        else:
            self.tool_opt_form = None

    def is_valid(self):
        """Return whether or not the form is valid.

        Returns:
            boolean:
            True if the form is valid.
        """
        return (super(ProfileForm, self).is_valid() and
                self.tool_opt_form.is_valid())

    def save(self, commit=True, *args, **kwargs):
        """Save the profile.

        Args:
            commit (boolean):
                True if the model should be saved in addition to having its
                fields updated. This is used to batch all updates from super-
                and sub-classes into a single transaction.
        """
        tool_profile = super(ProfileForm, self).save(
            commit=False, *args, **kwargs)

        options = self.options
        settings = tool_profile.tool_settings

        for option in options:
            field_name = option['name']
            settings[field_name] = self.tool_opt_form.cleaned_data[field_name]

        tool_profile.tool_settings = settings

        if commit:
            tool_profile.save()

        return tool_profile

    def _make_tool_opt_form(self, options, settings):
        """Construct the tool specific settings form.

        Args:
            options (dict):
                The tool's :py:attr:`~reviewbotext.models.Tool.tool_options`.

            settings (dict):
                The profile's settings for the tool.

        Returns:
            ReviewBotToolOptionsForm:
            The new form.
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

        Args:
            class_str (unicode):
                The name of the class to import.

        Returns:
            class:
            The imported class.

        Raises:
            TypeErrror:
                The specified class was not a subclass of
                :py:class:`django.forms.fields.Field`.
        """
        field_class = self._get_class(class_str)

        if not issubclass(field_class, Field):
            raise TypeError('%s is not a Field class.' % class_str)

        return field_class

    def _get_widget_class(self, widget_str):
        """Import and returns the widget class.

        Args:
            widget_class (unicode):
                The name of the class to import.

        Returns:
            class:
            The imported class.

        Raises:
            TypeErrror:
                The specified class was not a subclass of
                :py:class:`django.forms.widgets.Widget`.
        """
        widget_class = self._get_class(widget_str)

        if not issubclass(widget_class, Widget):
            raise TypeError('%s is not a Widget class.' % widget_str)

        return widget_class

    def _get_class(self, class_str):
        """Import and returns the class, given the module path to a class.

        Args:
            class_str (unicode):
                The name of the class to import.

        Returns:
            class:
            The imported class.
        """
        class_path = str(class_str).split('.')

        if len(class_path) > 1:
            module_name = '.'.join(class_path[:-1])
        else:
            module_name = '.'

        module = __import__(module_name, {}, {}, class_path[-1])
        return getattr(module, class_path[-1])

    class Meta:
        model = Profile


def _regex_validator(regex):
    """Validate the provided regular expression.

    Args:
        regex (unicode):
            The regular expression to validate.

    Raises:
        ValidationError:
        The provided regular expression could not be compiled.
    """
    try:
        re.compile(regex)
    except Exception as e:
        raise ValidationError('This regex is invalid: %s' % e)


class AutomaticRunGroupForm(forms.ModelForm):
    """Form for the :py:class:`~reviewbotext.models.AutomaticRunGroup` model.
    """

    name = forms.CharField(
        label=_('Name'),
        max_length=128,
        widget=forms.TextInput(attrs={'size': '30'}))

    file_regex = forms.CharField(
        label=_('File regular expression'),
        max_length=256,
        widget=forms.TextInput(attrs={'size': '60'}),
        validators=[_regex_validator],
        help_text=_('File paths are matched against this regular expression '
                    'to determine if the tool profiles specified below should '
                    'be run automatically.'))

    repository = forms.ModelMultipleChoiceField(
        label=_('Repositories'),
        required=False,
        queryset=Repository.objects.filter(visible=True).order_by('name'),
        help_text=_('The list of repositories this automatic run group will '
                    'match. If left empty, this automatic run group will not '
                    'apply to any repositories.'),
        widget=FilteredSelectMultiple(_("Repositories"), False))

    def clean(self):
        """Validate the current state of the form.

        Returns:
            dict:
            The cleaned form data.
        """
        # Check that the profiles are valid.
        local_site = self.cleaned_data.get('local_site')
        profiles = self.cleaned_data.get('profile', [])

        for profile in profiles:
            if profile.local_site != local_site:
                self._errors['profile'] = self.error_class([
                    _('The profile %s does not exist on the local site.')
                    % profile.name
                ])
                break

        # Check that the repositories are valid.
        repositories = self.cleaned_data.get('repository', [])

        for repository in repositories:
            if repository.local_site != local_site:
                self._errors['repository'] = self.error_class([
                    _('The repository %s does not exist on the local site.')
                    % repository.name
                ])
                break

        return self.cleaned_data

    class Meta:
        model = AutomaticRunGroup


class ManualPermissionForm(forms.ModelForm):
    """Form for the :py:class:`~reviewbotext.models.ManualPermission` model.
    """

    def clean_user(self):
        """Clean the user field.

        Returns:
            django.contrib.auth.models.User:
            The cleaned user.

        Raises:
            ValidationError:
            There was an error with the selected user.
        """
        user = self.cleaned_data['user']

        if (ManualPermission.objects
                .filter(user=user)
                .exclude(pk=self.instance.pk)
                .exists()):
            raise forms.ValidationError(_('This user already has a Manual '
                                          'Permission entry.'))

        return user

    def clean(self):
        """Validate the current state of the form.

        Returns:
            dict:
            The cleaned form data.
        """
        local_site = self.cleaned_data.get('local_site')
        user = self.cleaned_data.get('user')

        if (local_site and not local_site.is_accessible_by(user)):
            self._errors['user'] = self.error_class([
                _('The user %s does not exist on the local site.')
                % user.username
            ])

        return self.cleaned_data

    class Meta:
        model = ManualPermission
