

class Tool(object):
    """The base class all Review Bot tools should inherit from.

    """
    def __init__(self, review):
        self.review = review
