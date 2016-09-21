from __future__ import unicode_literals

from django.db.models import Manager


class AutomaticRunGroupManager(Manager):
    """A manager for AutomaticRunGroup models."""

    def for_repository(self, repository, local_site):
        """Return all AutomaticRunGroups associated with the repository.

        Args:
            repository (reviewboard.scmtools.models.Repository):
                The repository to search for.

            local_site (reviewboard.site.models.LocalSite):
                The local site to limit to.
        """
        return self.filter(local_site=local_site, repository=repository)

    def can_create(self, user, local_site=None):
        """Return whether the user can create an AutomaticRunGroup.

        Args:
            user (django.contrib.auth.models.User):
                The user to check.

            local_site (reviewboard.site.models.LocalSite, optional):
                The current local site, if appropriate.
        """
        return (user.is_superuser or
                (local_site and local_site.is_mutable_by(user)))
