from django.db.models import Manager, Q


class AutomaticRunGroupManager(Manager):
    """A manager for AutomaticRunGroup models."""

    # def for_repository(self, repository, local_site):
    #     """Returns all DefaultReviewers that represent a repository.

    #     These include both DefaultReviewers that have no repositories
    #     (for backwards-compatibility) and DefaultReviewers that are
    #     associated with the given repository.
    #     """
    #     return self.filter(local_site=local_site).filter(
    #         Q(repository__isnull=True) | Q(repository=repository))

    def can_create(self, user, local_site=None):
        """Returns whether the user can create an AutomaticRunGroup."""
        return (user.is_superuser or
                (local_site and local_site.is_mutable_by(user)))