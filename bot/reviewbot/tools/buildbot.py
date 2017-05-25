from __future__ import unicode_literals

from reviewbot.tools import Tool
from reviewbot.utils.process import execute


class BuildBotTool(Tool):
    """Review Bot tool to do a build using `buildbot try`."""

    name = 'BuildBot try'
    version = '1.0'
    description = ('Runs the buildbot try command and posts the result of the '
                   'build.')
    options = [
        {
            'name': 'address',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'Buildmaster Address',
                'help_text': ('The address of the buildmaster. Used by both '
                              'PB and SSH.'),
                'required': True,
            },
        },
        {
            'name': 'connect_method',
            'field_type': 'django.forms.ChoiceField',
            'field_options': {
                'label': 'Connect Method',
                'help_text': ('Connection method used by buildbot to contact '
                              'the try server.'),
                'required': True,
                'choices': (('PB', 'PB authentication'),
                            ('SSH', 'SSH authentication')),
            }
        },
        {
            'name': 'port',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'Port',
                'help_text': ('Port used to communicate with buildbot. Not '
                              'the the ssh connection port.'),
                'required': False,
            },
        },
        {
            'name': 'username',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'Username',
                'help_text': ('Username, used by both PB and SSH '
                              'authentication.'),
                'required': True,
            },
        },
        {
            'name': 'password',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'PB Password',
                'help_text': ('PB Password: Stored as plaintext in database. '
                              'Use with extreme caution.'),
                'required': False,
            },
        },
        {
            'name': 'jobdir',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'Job directory',
                'help_text': ('SSH Job dir: Directory chosen in buildbot '
                              'config to be writeable by all allowed users.'),
                'required': False,
            },
        },
        {
            'name': 'pblistener',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'PB listener port',
                'help_text': ('Required when using SSH. Indicate port used to '
                              'check build status.'),
                'required': False,
            },
        },
        {
            'name': 'buildbotbin',
            'field_type': 'django.forms.CharField',
            'default': None,
            'field_options': {
                'label': 'buildbot binary location',
                'help_text': ('SSH buildbot binary location: path to buildbot '
                              'if not in user\'s path. For use with '
                              'virtualenv.'),
                'required': False,
            },
        },
        {
            'name': 'use_branch',
            'field_type': 'django.forms.BooleanField',
            'default': False,
            'field_options': {
                'label': 'Use Branch Field',
                'help_text': ('Tell BuildBot to use the contents of the '
                              'branch field in the review request. WARNING: '
                              'this field is free-form and may not contain '
                              'a valid branch name.'),
                'required': False,
            },

        },
        {
            'name': 'default_branch',
            'field_type': 'django.forms.CharField',
            'field_options': {
                'label': 'Default Branch',
                'help_text': ('Default branch to build off of. Uses master by '
                              'default.'),
                'required': False,
            },
        },
        {
            'name': 'builder',
            'field_type': 'django.forms.CharField',
            'field_options': {
                'label': 'Builder',
                'help_text': ('Comma-separated list of builders to use. '
                              'Required when using SSH.'),
                'required': False,
            },
        },
    ]

    def execute(self, review, settings={}, repository=None,
                base_commit_id=None):
        """Perform a review using the tool.

        Args:
            review (reviewbot.processing.review.Review):
                The review object.

            settings (dict):
                Tool-specific settings.

            repository (reviewbot.repositories.Repository):
                The repository.

            base_commit_id (unicode):
                The ID of the commit that the patch should be applied to.
        """
        cmd = [
            'buildbot',
            'try',
            '--wait',
            '--quiet',
            '--diff=%s' % review.get_patch_file_path(),
            '--patchlevel=1',
            '--username=%s' % settings['username'],
            '--master=%s:%s' % (settings['address'],
                                settings['port']
                                ),
        ]

        branch = review.api_root.get_review_request(
            review_request_id=review.request_id).branch

        if branch != '' and settings['use_branch']:
            cmd.append('--branch=%s' % branch)
        elif 'default_branch' in settings:
            cmd.append('--branch=%s' % settings['default_branch'])

        if settings['connect_method'] == 'PB':
            cmd.extend([
                '--connect=pb',
                '--passwd=%s' % settings['password'],
            ])
        else:
            # Assume SSH
            cmd.extend([
                '--connect=ssh',
                '--jobdir=%s' % settings['jobdir'],
                '--host=%s' % settings['address'],
            ])

            for builder in settings['builders'].split(','):
                cmd.append('--builder=%s' % builder.strip())

            if settings['buildbotbin'] != '':
                cmd.append('--buildbotbin=%s' % settings['buildbotbin'])

        review.body_top = execute(cmd, ignore_errors=True)
