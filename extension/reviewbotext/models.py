from django.db import models
from django.utils.translation import ugettext as _
from djblets.util.fields import JSONField


class ReviewBotTool(models.Model):
    """Information about a tool installed on a worker."""
    name = models.CharField(max_length=128, blank=False)
    entry_point = models.CharField(max_length=128, blank=False)
    version = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default="", blank=True)
    enabled = models.BooleanField(default=True)
    run_automatically = models.BooleanField(
        default=False,
        help_text=_("Run automatically when a review request is updated."))
    allow_run_manually = models.BooleanField(default=False)
    in_last_update = models.BooleanField()
    ship_it = models.BooleanField(
        default=False,
        help_text=_("Ship it! If no issues raised."))
    open_issues = models.BooleanField(default=False)
    comment_unmodified = models.BooleanField(
        default=False,
        verbose_name=_("Comment on unmodified code"))
    tool_options = JSONField()
    tool_settings = JSONField()

    def __unicode__(self):
        return "%s - v%s" % (self.name, self.version)

    class Meta:
        unique_together = ('entry_point', 'version')
