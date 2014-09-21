from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from djblets.db.fields import JSONField, ModificationTimestampField
from reviewboard.scmtools.models import Repository
from reviewboard.site.models import LocalSite

from reviewbotext.managers import AutomaticRunGroupManager


class Tool(models.Model):
    """Information about a tool installed on a worker.

    `tool_option` is a JSON list describing the options a tool may take. Each
    entry is a dictionary which may define the following fields:

    {
        'name': The name of the option
        'field_type': The django form field class for the option
        'default': The default value
        'field_options': An object containing fields to be passed to the form
                         class, e.g.:
        {
            'label': A label for the field
            'help_text': Help text
            'required': If the field is required
        }
    }

    Each entry in the database will be unique for the values of `entry_point`
    and `version`. Any backwards incompatible changes to a Tool will result
    in a version bump, allowing multiple versions of a tool to work with a
    Review Board instance.
    """
    name = models.CharField(max_length=128, blank=False)
    entry_point = models.CharField(max_length=128, blank=False)
    version = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default="", blank=True)
    enabled = models.BooleanField(default=True)
    in_last_update = models.BooleanField()
    tool_options = JSONField()

    def __unicode__(self):
        return "%s - v%s" % (self.name, self.version)

    class Meta:
        unique_together = ('entry_point', 'version')


class Profile(models.Model):
    """A configuration of a tool.

    Each Profile may have distinct settings for the associated tool and rules
    about who may run the tool manually.
    """
    tool = models.ForeignKey(Tool)
    name = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default="", blank=True)

    allow_manual = models.BooleanField(default=False)
    allow_manual_submitter = models.BooleanField(default=False)
    allow_manual_group = models.BooleanField(default=False)

    ship_it = models.BooleanField(
        default=False,
        help_text=_("Ship it! If no issues raised."))
    open_issues = models.BooleanField(default=False)
    comment_unmodified = models.BooleanField(
        default=False,
        verbose_name=_("Comment on unmodified code"))
    tool_settings = JSONField()

    local_site = models.ForeignKey(LocalSite, blank=True, null=True,
                                   related_name='reviewbot_profiles')

    def __unicode__(self):
        return self.name


class ToolExecution(models.Model):
    """Status of a tool execution.

    This represents the request for and status of a tool's execution.
    """
    QUEUED = 'Q'
    RUNNING = 'R'
    SUCCEEDED = 'S'
    FAILED = 'F'
    TIMED_OUT = 'T'

    STATUSES = (
        (QUEUED, _('Queued')),
        (RUNNING, _('Running')),
        (SUCCEEDED, _('Succeeded')),
        (FAILED, _('Failed')),
        (TIMED_OUT, _('Timed-out')),
    )

    profile = models.ForeignKey(Profile)
    review_request_id = models.IntegerField(null=True)
    diff_revision = models.IntegerField(null=True)
    last_updated = ModificationTimestampField(_("last updated"))
    status = models.CharField(max_length=1, choices=STATUSES, blank=True)

    # Review Information
    result = JSONField()

    def __unicode__(self):
        return '%s (%s)' % (self.profile.name, self.status)

    class Meta:
        ordering = ['-last_updated', 'review_request_id', 'diff_revision']


class AutomaticRunGroup(models.Model):
    """A set of Tool Profiles to be executed automatically.

    An Automatic Run Group is a set of tool profiles, and rules for when they
    will be run automatically on review requests. The tools will be executed
    on a review request when the diff modifies a file matching the
    ``file_regex`` pattern specified.

    A ``file_regex`` of ``".*"`` will run the tools for every review request.

    Note that this is keyed off the same LocalSite as its "repository" member.
    """
    name = models.CharField(max_length=128, blank=False)
    file_regex = models.CharField(
        _('file regex'),
        max_length=256,
        help_text=_('File paths are matched against this regular expression '
                    'to determine if these tool profiles should be run.'))
    profile = models.ManyToManyField(Profile, blank=False)
    repository = models.ManyToManyField(Repository, blank=True)
    local_site = models.ForeignKey(
        LocalSite,
        blank=True,
        null=True,
        related_name='reviewbot_automatic_run_groups')

    objects = AutomaticRunGroupManager()

    def __unicode__(self):
        return self.name


class ManualPermission(models.Model):
    """Manual execution permissions for a user on a local site.

    A user with this permission will be allowed to manually execute all tool
    profiles which have ``allow_manual_group`` set to True.
    """
    user = models.ForeignKey(User, unique=True, blank=False)
    local_site = models.ForeignKey(LocalSite, blank=True, null=True,
                                   related_name='reviewbot_manual_permissions')
    allow = models.BooleanField(
        default=False,
        verbose_name=_('Allow manual execution'),
        help_text=_('Designates whether the user can manually execute tool '
                    'profiles which have the "Allow manual group" setting '
                    'checked.'))

    def __unicode__(self):
        return self.user.username


# TODO: This is a temporary fix that should be removed once /r/6224 is in.
Repository._meta._fill_related_many_to_many_cache()
Repository._meta.init_name_map()
