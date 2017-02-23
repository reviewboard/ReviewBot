from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from djblets.db.fields import JSONField


@python_2_unicode_compatible
class Tool(models.Model):
    """Information about a tool installed on a worker.

    Each entry in the database will be unique for the values of `entry_point`
    and `version`. Any backwards incompatible changes to a Tool will result
    in a version bump, allowing multiple versions of a tool to work with a
    Review Board instance.
    """

    name = models.CharField(max_length=128, blank=False)
    entry_point = models.CharField(max_length=128, blank=False)
    version = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default='', blank=True)
    enabled = models.BooleanField(default=True)
    in_last_update = models.BooleanField()
    timeout = models.IntegerField(blank=True, null=True)
    working_directory_required = models.BooleanField(default=False)

    #: A JSON list describing the options a tool make take. Each entry is a
    #: dictionary which may define the following fields:
    #:
    #:     {
    #:         'name': The name of the option
    #:         'field_type': The django form field class for the option
    #:         'default': The default value
    #:         'field_options': An object containing fields to be passed to
    #:                          the form class, e.g.:
    #:         {
    #:             'label': A label for the field
    #:             'help_text': Help text
    #:             'required': If the field is required
    #:         }
    #:     }
    tool_options = JSONField()

    def __str__(self):
        """Return a string representation of the tool.

        Returns:
            unicode:
            The text representation for this model.
        """
        return '%s - v%s' % (self.name, self.version)

    class Meta:
        unique_together = ('entry_point', 'version')
