"""Celery and Review Bot worker setup and management."""

from __future__ import absolute_import, unicode_literals

import os
import sys
import textwrap

from celery import (Celery,
                    VERSION as CELERY_VERSION,
                    __version__ as celery_version_str,
                    concurrency as celery_concurrency,
                    maybe_patch_concurrency)
from celery.platforms import maybe_drop_privileges
from celery.signals import celeryd_after_setup, celeryd_init
from kombu import Exchange, Queue

try:
    # Celery 5, Python 3+
    from celery.bin.worker import detach as detach_process
except ImportError:
    # Celery 3, Python 2.7
    from celery.bin.celeryd_detach import detach as detach_process

from reviewbot import VERSION
from reviewbot.config import config, get_config_file_path, load_config
from reviewbot.repositories import repositories, init_repositories
from reviewbot.tools.base.registry import (get_tool_classes,
                                           load_tool_classes)
from reviewbot.utils.log import get_root_logger


celery = None
logger = get_root_logger()


_manual_url = 'https://www.reviewboard.org/docs/reviewbot/%s.%s/' % VERSION[:2]


class ReviewBotCelery(Celery):
    """A Celery specialization for Review Bot.

    This takes care of initializing Celery with the right options.

    Version Added:
        3.0
    """

    def __init__(self):
        """Initialize Celery."""
        super(ReviewBotCelery, self).__init__(
            main='reviewbot.celery',
            include=['reviewbot.tasks'])


def create_queues(hostname):
    """Create the celery queues.

    Returns:
        list of kombu.Queue:
        The queues that this worker will listen to.
    """
    default_exchange = Exchange('celery', type='direct')
    queues = [
        Queue('celery', default_exchange, routing_key='celery'),
    ]

    found_tools = []
    missing_dep_tools = []
    working_dir_tools = []

    # Detect the installed tools and select the corresponding queues to
    # consume from.
    for tool_class in get_tool_classes():
        tool_id = tool_class.tool_id
        tool = tool_class()
        queue_name = '%s.%s' % (tool_id, tool_class.version)

        if tool.check_dependencies():
            found_tools.append(tool_id)

            if tool.working_directory_required:
                # Set up a queue for each configured repository. This way only
                # workers which have the relevant repository configured will
                # pick up applicable tasks.
                working_dir_tools.append(tool_id)

                for repo_name in repositories:
                    repo_queue_name = '%s.%s' % (queue_name, repo_name)

                    queues.append(Queue(
                        repo_queue_name,
                        Exchange(repo_queue_name, type='direct'),
                        routing_key=repo_queue_name))
            else:
                queues.append(Queue(
                    queue_name,
                    Exchange(queue_name, type='direct'),
                    routing_key=queue_name))
        else:
            missing_dep_tools.append(tool_id)

    s = [
        'Welcome!',
        '',
        'Review Bot will connect to %s' % celery.connection().as_uri(),
        'as %s.' % hostname,
        '',
    ]

    python_version_str = '%s.%s' % sys.version_info[:2]

    if sys.version_info[0] == 2:
        compat_text = (
            'Note that you are running Review Bot using Python '
            '%(python_version)s and Celery %(celery_version)s, both of '
            'which are out-of-date and are no longer receiving security '
            'fixes. We recommend upgrading to a modern Python 3. '
            'Review Bot 3 is the last release that will support these '
            'versions.'
            % {
                'python_version': python_version_str,
                'celery_version': celery_version_str,
            })
    else:
        compat_text = (
            'You are running Review Bot using Python %(python_version)s '
            'and Celery %(celery_version)s. Make sure to keep up on the '
            'latest supported versions of Python 3 and Celery '
            '%(celery_major_version)s in order to stay nice and secure.'
            % {
                'python_version': python_version_str,
                'celery_version': celery_version_str,
                'celery_major_version': CELERY_VERSION[0],
            })

    s += [
        textwrap.fill(compat_text,
                      width=75),
        '',
    ]

    if found_tools:
        s += [
            'The following tools are available:',
            '',
        ] + [
            '  * %s' % _tool_id
            for _tool_id in found_tools
        ] + ['']

    if missing_dep_tools:
        s += [
            'The following tools are missing dependencies:',
            '',
        ] + [
            '  * %s' % _tool_id
            for _tool_id in missing_dep_tools
        ] + [
            '',
            'See %stools/ for help on installing tools.'
            % _manual_url,
            '',
        ]

    if working_dir_tools:
        if not repositories:
            s += [
                'The following tools cannot be used without one or more '
                'configured repositories in %s:'
                % get_config_file_path(),
                '',
            ] + [
                '  * %s' % _tool_id
                for _tool_id in working_dir_tools
            ]
        else:
            s += [
                'The following tools require a configured repository in %s:'
                % get_config_file_path(),
                '',
            ] + [
                '  * %s' % _tool_id
                for _tool_id in working_dir_tools
            ]

            s += [
                '',
                'Configured repositories include:',
                '',
            ] + [
                '  * %s' % _repository
                for _repository in repositories
            ]

        s += [
            '',
            'See %sconfiguration/#worker-configuration-repositories for '
            'help on configuring repositories.'
            % _manual_url,
            '',
        ]

    logger.info('\n'.join(s))

    return queues


def setup_cookies():
    """Set up cookie storage for API communication.

    This will ensure that the cookie directory exists and that the cookie
    file can be written to.

    Raises:
        IOError:
            The cookie directories could not be created or there's a
            permission error with cookie storage. The specific error will
            be in the exception message.
    """
    cookie_dir = config['cookie_dir']
    cookie_path = config['cookie_path']

    logger.debug('Checking cookie storage at %s', cookie_path)

    # Create the cookie storage directory, if it doesn't exist.
    if not os.path.exists(cookie_dir):
        try:
            os.makedirs(cookie_dir, 0o755)
        except OSError as e:
            raise IOError('Unable to create cookies directory "%s": %s'
                          % (cookie_dir, e))

    can_write_cookies = True

    if os.path.exists(cookie_path):
        # See if we have write access to the file.
        can_write_cookies = os.access(cookie_path, os.W_OK)
    else:
        # Try writing to the file. We'll append, just in case there's another
        # process that managed to write just before this (super unlikely).
        try:
            with open(cookie_path, 'a'):
                pass

            os.chmod(cookie_path, 0o600)
        except (IOError, OSError):
            can_write_cookies = False

    if not can_write_cookies:
        raise IOError('Unable to write to cookie file "%s". Please make '
                      'sure Review Bot has the proper permissions.'
                      % cookie_path)

    logger.debug('Cookies can be stored at %s', cookie_path)


@celeryd_init.connect
def setup_logging(instance, conf, **kwargs):
    """Set up logging for Celery and Review Bot.

    This will configure the log formats we want Celery to use. This differs
    from Celery's defaults not just in the structure of the log entries, but
    also in the addition of the logger name (used to identify different
    tools).

    Args:
        instance (celery.app.base.Celery):
            The Celery instance.

        conf (celery.app.utils.Settings):
            The Celery configuration.

        **kwargs (dict, unused):
            Additional keyword arguments passed to the signal.
    """
    log_format = (
        '%(asctime)s - [%(levelname)s] %(name)s: %(message)s'
    )

    task_log_format = (
        '%(asctime)s - %(processName)s: %(task_name)s(%(task_id)s) - '
        '[%(levelname)s] %(name)s: %(message)s'
    )

    if CELERY_VERSION >= (5, 0):
        conf.update({
            'worker_log_format': log_format,
            'worker_task_log_format': task_log_format,
        })
    else:
        conf.update({
            'CELERYD_LOG_FORMAT': log_format,
            'CELERYD_TASK_LOG_FORMAT': task_log_format,
        })


@celeryd_after_setup.connect
def setup_reviewbot(instance, conf, **kwargs):
    """Set up Review Bot and Celery.

    This will load the Review Bot configuration, store any repository state,
    and set up the queues for the enabled tools.

    Args:
        instance (celery.app.base.Celery):
            The Celery instance.

        conf (celery.app.utils.Settings):
            The Celery configuration.

        **kwargs (dict, unused):
            Additional keyword arguments passed to the signal.
    """
    load_config()

    try:
        setup_cookies()
    except IOError as e:
        logger.error(e)
        sys.exit(1)

    load_tool_classes()
    init_repositories()

    if CELERY_VERSION >= (5, 0):
        conf.accept_content = ['json']
    else:
        conf.CELERY_ACCEPT_CONTENT = ['json']

    instance.app.amqp.queues = create_queues(hostname=instance.hostname)


def get_celery():
    """Return a Celery instance.

    This will only be constructed the first time this is called. All
    subsequent calls will reuse a cached instance.

    Version Added:
        3.0

    Returns:
        ReviewBotCelery:
        The Celery instance.
    """
    global celery

    if celery is None:
        celery = ReviewBotCelery()

    return celery


def start_worker(broker, hostname, loglevel, logfile, detach, pidfile, uid,
                 gid, umask, concurrency, pool_cls, autoscale):
    """Start a worker.

    This will take in the requested arguments and start a Celery worker,
    running either in the current process or in a detached process.

    This also takes care to patch the concurrency module, as per Celery's
    requirements, and to drop privileges if needed.

    Version Added:
        3.0

    Args:
        broker (unicode):
            The broker URI.

        hostname (unicode):
            The local hostname Review Bot will identify with when talking to
            the broker.

        loglevel (unicode):
            The minimum log level.

        logfile (unicode):
            The path to a log file to write to.

        detach (bool):
            Whether to run the worker in a detached process.

        pidfile (unicode):
            The path to a PID file to write to when detaching.

        uid (unicode):
            The user ID to use when detaching.

        gid (unicode):
            The group ID to use when detaching.

        umask (unicode):
            The umask (in octal string format) to use for the process when
            detaching.

        concurrency (int):
            The number of concurrent processes to run.

        pool_cls (unicode):
            The pool implementation.

        autoscale (unicode):
            The autoscale settings, in the form of
            ``max_concurrency,min_concurrency``.

    Returns:
        int:
        The worker's exit code.
    """
    # We're running in modern (Review Bot 3+) mode.
    #
    # First thing to do is trigger a patch to the concurrency modules.
    # Normally, Celery will do this but ONLY if executing from the main
    # 'celery' command or through 'execute_from_commandline' (which we can't
    # use -- see below).
    maybe_patch_concurrency()

    # Check if we need to/can drop privileges, and do so.
    maybe_drop_privileges(uid=uid,
                          gid=gid)

    # The broker is configured through the environment, not through a setting.
    #
    # The way Celery command classes normally handle this is through a
    # separate argument parsing step, before the main one. It assumes a lot
    # about how things are invoked, and handles setting a lot of options. We
    # don't care about any of those, and want to avoid the assumptions, so
    # we'll just set what we need here.
    # do that, so
    os.environ['CELERY_BROKER_URL'] = broker

    if detach:
        detach_argv = [sys.argv[0]]

        # Some options are passed to detach() directly. Some are passed as
        # command line arguments. Some are both.
        for name, value in (('autoscale', autoscale),
                            ('broker', broker),
                            ('concurrency', concurrency),
                            ('hostname', hostname),
                            ('logfile', logfile),
                            ('loglevel', loglevel),
                            ('pidfile', pidfile),
                            ('pool', pool_cls)):
            if value is not None:
                detach_argv.append('--%s=%s' % (name, value))

        return detach_process(
            app=celery,
            path=sys.executable,
            argv=detach_argv,
            logfile=logfile,
            pidfile=pidfile,
            uid=uid,
            gid=gid,
            umask=umask,
            executable=sys.executable,
            hostname=hostname)
    else:
        pool_cls = (celery_concurrency.get_implementation(pool_cls) or
                    celery.conf.CELERYD_POOL)

        worker = celery.Worker(
            hostname=hostname,
            loglevel=loglevel,
            logfile=logfile,
            detach=detach,
            pidfile=pidfile,
            uid=uid,
            gid=gid,
            umask=umask,
            concurrency=concurrency,
            pool_cls=pool_cls,
            autoscale=autoscale,
            quiet=True)

        if CELERY_VERSION >= (5, 0):
            worker.start()
            return worker.exitcode
        else:
            return worker.start()
