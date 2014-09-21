from django.db.models import Manager


class AutomaticRunGroupManager(Manager):
    """A manager for AutomaticRunGroup models."""

    def for_repository(self, repository, local_site):
        """Returns all AutomaticRunGroups associated with the repository."""
        return self.filter(local_site=local_site, repository=repository)

    def can_create(self, user, local_site=None):
        """Returns whether the user can create an AutomaticRunGroup."""
        return (user.is_superuser or
                (local_site and local_site.is_mutable_by(user)))
