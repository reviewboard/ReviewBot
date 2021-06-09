"""Tool registration

These functions are used to register and look up known tool classes.

Version Added:
    3.0
"""

from __future__ import unicode_literals

import pkg_resources

import six

from reviewbot.utils.log import get_logger


logger = get_logger(__name__,
                    is_task_logger=False)


#: A mapping of tool IDs to tool classes.
#:
#: Type
#:     dict
_registered_tools = {}


def register_tool_class(tool_cls):
    """Register a tool class for later lookup.

    The tool class must have a ``tool_id`` attribute (either directly set,
    for unit tests, or through :py:meth:`load_tool_classes`), and cannot
    conflict with another tool.

    Args:
        tool_cls (type):
            A tool class to register (subclass of
            :py:class:`reviewbot.tools.base.tool.BaseTool)`.

    Raises:
        ValueError:
            The tool could not be registered, either due to a missing
            ``tool_id`` or due to a conflict with another tool.
    """
    tool_id = getattr(tool_cls, 'tool_id', None)

    if tool_id is None:
        raise ValueError('The tool class %r is missing a tool_id attribute.'
                         % (tool_cls,))

    if tool_id in _registered_tools:
        raise ValueError(
            'Another tool with the ID "%s" is already registered (%r).'
            % (tool_id, _registered_tools[tool_id]))

    _registered_tools[tool_id] = tool_cls


def unregister_tool_class(tool_id):
    """Unregister a tool class by its ID.

    Args:
        tool_id (type):
            The ID of the tool to unregister.

    Raises:
        KeyError:
            The tool could not be found.
    """
    try:
        del _registered_tools[tool_id]
    except KeyError:
        raise KeyError('A tool with the ID "%s" was not registered.'
                       % tool_id)


def get_tool_class(tool_id):
    """Return the tool class with a given ID.

    Args:
        tool_id (unicode):
            The ID of the tool to return.

    Returns:
        type:
        The tool class, or ``None`` if no tool with that ID exists.
    """
    return _registered_tools.get(tool_id)


def get_tool_classes():
    """Return all registered tool classes.

    This will be sorted in alphabetical order, based on the ID.

    Returns:
        list of type:
        A list of tool classes (subclasses of
        :py:class:`reviewbot.tools.base.tool.BaseTool`).
    """
    return sorted(six.itervalues(_registered_tools),
                  key=lambda tool_cls: tool_cls.tool_id)


def load_tool_classes():
    """Load tool classes provided by Review Bot and other packages.

    This will scan for any Python packages that provide ``reviewbot.tools``
    entrypoints, loading the tools into the tool registry.

    Any existing tools will be cleared out before this begins, and any errors
    will be logged.
    """
    _registered_tools.clear()

    for ep in pkg_resources.iter_entry_points(group='reviewbot.tools'):
        try:
            tool_cls = ep.load()
            tool_cls.tool_id = ep.name

            register_tool_class(tool_cls)
        except Exception as e:
            logger.error('Unable to load tool "%s": %s',
                         ep.name, e,
                         exc_info=True)
