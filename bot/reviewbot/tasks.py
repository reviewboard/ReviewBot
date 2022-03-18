"""Core task handling."""

from __future__ import absolute_import, unicode_literals

import json

from celery.worker.control import Panel

from reviewbot.celery import get_celery
from reviewbot.processing.review import Review
from reviewbot.repositories import repositories
from reviewbot.tools.base.registry import get_tool_class, get_tool_classes
from reviewbot.utils.api import get_api_root
from reviewbot.utils.filesystem import cleanup_tempfiles
from reviewbot.utils.log import get_logger


# Status Update states
PENDING = 'pending'
DONE_SUCCESS = 'done-success'
DONE_FAILURE = 'done-failure'
ERROR = 'error'


celery = get_celery()
logger = get_logger(__name__)


@celery.task(ignore_result=True)
def RunTool(server_url='',
            session='',
            username='',
            review_request_id=-1,
            diff_revision=-1,
            status_update_id=-1,
            review_settings={},
            tool_options={},
            repository_name='',
            base_commit_id='',
            *args, **kwargs):
    """Execute an automated review on a review request.

    Args:
        server_url (unicode):
            The URL of the Review Board server.

        session (unicode):
            The encoded session identifier.

        username (unicode):
            The name of the user who owns the ``session``.

        review_request_id (int):
            The ID of the review request being reviewed (ID for use in the
            API, which is the "display_id" field).

        diff_revision (int):
            The ID of the diff revision being reviewed.

        status_update_id (int):
            The ID of the status update for this invocation of the tool.

        review_settings (dict):
            Settings for how the review should be created.

        tool_options (dict):
            The tool-specific settings.

        repository_name (unicode):
            The name of the repository to clone to run the tool, if the tool
            requires full working directory access.

        base_commit_id (unicode):
            The ID of the commit that the patch should be applied to.

        *args (tuple):
            Any additional positional arguments (perhaps used by a newer
            version of the Review Bot extension).

        **kwargs (dict):
            Any additional keyword arguments (perhaps used by a newer version
            of the Review Bot extension).

    Returns:
        bool:
        Whether the task completed successfully.
    """
    try:
        routing_key = RunTool.request.delivery_info['routing_key']
        route_parts = routing_key.partition('.')
        tool_name = route_parts[0]

        log_detail = ('(server=%s, review_request_id=%s, diff_revision=%s)'
                      % (server_url, review_request_id, diff_revision))

        logger.debug('Running tool "%s" %s', tool_name, log_detail)

        try:
            logger.debug('Initializing RB API %s', log_detail)
            api_root = get_api_root(url=server_url,
                                    session=session)
        except Exception as e:
            logger.error('Could not contact Review Board server: %s %s',
                         e, log_detail)
            return False

        logger.debug('Loading requested tool "%s" %s', tool_name, log_detail)
        tool_cls = get_tool_class(tool_name)

        if tool_cls is None:
            logger.error('Tool "%s" not found %s', tool_name, log_detail)
            return False

        repository = None

        try:
            logger.debug('Creating status update %s', log_detail)
            status_update = api_root.get_status_update(
                review_request_id=review_request_id,
                status_update_id=status_update_id)
        except Exception as e:
            logger.exception('Unable to create status update: %s %s',
                             e, log_detail)
            return False

        if tool_cls.working_directory_required:
            if not base_commit_id:
                logger.error('Working directory is required but the diffset '
                             'has no base_commit_id %s', log_detail)
                status_update.update(
                    state=ERROR,
                    description='Diff does not include parent commit '
                                'information.')
                return False

            try:
                repository = repositories[repository_name]
            except KeyError:
                logger.error('Unable to find configured repository "%s" %s',
                             repository_name, log_detail)
                return False

        try:
            logger.debug('Initializing review %s', log_detail)
            review = Review(api_root=api_root,
                            review_request_id=review_request_id,
                            diff_revision=diff_revision,
                            settings=review_settings)
            status_update.update(description='running...')
        except Exception as e:
            logger.exception('Failed to initialize review: %s %s', e, log_detail)
            status_update.update(state=ERROR, description='internal error.')
            return False

        try:
            logger.debug('Initializing tool "%s %s" %s',
                         tool_cls.name, tool_cls.version, log_detail)
            tool = tool_cls(settings=tool_options,
                            in_task=True)
        except Exception as e:
            logger.exception('Error initializing tool "%s": %s %s',
                             tool_cls.name, e, log_detail)
            status_update.update(state=ERROR, description='internal error.')
            return False

        try:
            # TODO: In Review Bot 4.0, remove the settings argument.
            logger.debug('Executing tool "%s" %s', tool.name, log_detail)
            tool.execute(review,
                         settings=tool_options,
                         repository=repository,
                         base_commit_id=base_commit_id)
            logger.debug('Tool "%s" completed successfully %s',
                         tool.name, log_detail)
        except Exception as e:
            logger.exception('Error executing tool "%s": %s %s',
                             tool.name, e, log_detail)
            status_update.update(state=ERROR, description='internal error.')
            return False

        if tool.output:
            file_attachments = \
                api_root.get_user_file_attachments(username=username)
            attachment = \
                file_attachments.upload_attachment(filename='tool-output',
                                                   content=tool.output)

            status_update.update(url=attachment.absolute_url,
                                 url_text='Tool console output')

        try:
            if not review.has_comments:
                status_update.update(state=DONE_SUCCESS,
                                     description='passed.')
            else:
                logger.debug('Publishing review %s', log_detail)
                review_id = review.publish().id

                status_update.update(state=DONE_FAILURE,
                                     description='failed.',
                                     review_id=review_id)
        except Exception as e:
            logger.exception('Error when publishing review: %s %s', e, log_detail)
            status_update.update(state=ERROR, description='internal error.')
            return False

        logger.debug('Review completed successfully %s', log_detail)
        return True
    finally:
        cleanup_tempfiles()


@Panel.register
def update_tools_list(panel, payload):
    """Update the list of installed tools.

    This will detect the installed analysis tool plugins
    and inform Review Board of them.

    Args:
        panel (celery.worker.control.Panel):
            The worker control panel.

        payload (dict):
            The payload as assembled by the extension.

    Returns:
        bool:
        Whether the task completed successfully.
    """
    logger.debug('Request to refresh installed tools from "%s"',
                 payload['url'])

    logger.debug('Iterating Tools')
    tools = []

    for tool_class in get_tool_classes():
        tool_id = tool_class.tool_id
        tool = tool_class()
        logger.debug('Tool: %s', tool_id)

        if tool.check_dependencies():
            # NOTE: We return the tool ID as the "entry_point". This sounds
            #       wrong, but it's correct. "entry_point" referes to the
            #       entrypoint name, aka tool ID. We'll probably want to
            #       revisit this naming down the road.
            tools.append({
                'name': tool_class.name,
                'entry_point': tool_id,
                'version': tool_class.version,
                'description': tool_class.description,
                'tool_options': json.dumps(tool_class.options,
                                           sort_keys=True),
                'timeout': tool_class.timeout,
                'working_directory_required':
                    tool_class.working_directory_required,
            })
        else:
            logger.warning('%s dependency check failed.',
                           tool_id)

    logger.debug('Done iterating Tools')
    hostname = panel.hostname

    try:
        api_root = get_api_root(url=payload['url'],
                                session=payload['session'])
    except Exception as e:
        logger.exception('Could not reach RB server: %s', e)

        return {
            'status': 'error',
            'error': 'Could not reach Review Board server: %s' % e,
        }

    try:
        api_tools = _get_extension_resource(api_root).get_tools()
        api_tools.create(hostname=hostname, tools=json.dumps(tools))
    except Exception as e:
        logger.exception('Problem POSTing tools: %s', e)

        return {
            'status': 'error',
            'error': 'Problem uploading tools: %s' % e,
        }

    return {
        'status': 'ok',
        'tools': tools,
    }


def _get_extension_resource(api_root):
    """Return the Review Bot extension resource.

    Args:
        api_root (rbtools.api.resource.Resource):
            The server API root.

    Returns:
        rbtools.api.resource.Resource:
        The extension's API resource.
    """
    # TODO: Cache this. We only use this resource as a link to sub-resources.
    return api_root.get_extension(
        extension_name='reviewbotext.extension.ReviewBotExtension')
