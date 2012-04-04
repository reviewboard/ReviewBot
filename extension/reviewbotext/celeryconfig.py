from reviewboard.extensions.base import get_extension_manager

from reviewbotext.extension import ReviewBotExtension

extension_manager = get_extension_manager()
extension = extension_manager.get_enabled_extension(ReviewBotExtension.id)

BROKER_URL = extension.settings['BROKER_URL']
