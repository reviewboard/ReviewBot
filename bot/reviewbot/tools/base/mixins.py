"""Useful mixins for code checking tools."""

from __future__ import unicode_literals

import logging
import os

from reviewbot.utils.filesystem import chdir, ensure_dirs_exist


class FullRepositoryToolMixin(object):
    """Mixin for tools that need access to the entire repository.

    This will take care of checking out a copy of the repository and applying
    patches from the diff being reviewed.

    Version Added:
        3.0:
        This replaced the legacy :py:class:`reviewbot.tools.RepositoryTool`.
    """

    working_directory_required = True

    def execute(self, review, settings={}, repository=None,
                base_commit_id=None):
        """Perform a review using the tool.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.

            settings (dict, optional):
                Tool-specific settings.

            repository (reviewbot.repositories.Repository, optional):
                The repository.

            base_commit_id (unicode, optional):
                The ID of the commit that the patch should be applied to.
        """
        repository.sync()
        working_dir = repository.checkout(base_commit_id)

        # Patch all the files first.
        with chdir(working_dir):
            for f in review.files:
                logging.info('Patching %s', f.dest_file)

                ensure_dirs_exist(os.path.abspath(f.dest_file))

                with open(f.dest_file, 'wb') as fp:
                    fp.write(f.patched_file_contents)

                f.patched_file_path = f.dest_file

            # Now run the tool for everything.
            self.handle_files(review.files, settings)
