from django.db import models
from djblets.util.fields import JSONField


class ReviewBotTool(models.Model):
    """Information about a tool installed on a worker."""
    name = models.CharField(max_length=128, blank=False)
    entry_point = models.CharField(max_length=128, blank=False)
    version = models.CharField(max_length=128, blank=False)
    description = models.CharField(max_length=512, default="", blank=True)
    enabled = models.BooleanField(default=True)
    run_automatically = models.BooleanField(default=False)
    allow_run_manually = models.BooleanField(default=False)
    in_last_update = models.BooleanField()
    tool_options = JSONField()
    tool_settings = JSONField()

    class Meta:
        unique_together = ('entry_point', 'version')
