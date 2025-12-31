# -*- coding: utf-8 -*-

class ImplementationError(Exception):
    """
    Bug in code.
    """

    def __init__(self, msg):
        super(ImplementationError, self).__init__(msg)
