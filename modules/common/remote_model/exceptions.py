# -*- coding: utf-8 -*-

class CodeFail(Exception):
    """
    Bug in code.
    """

    def __init__(self, msg):
        super(CodeFail, self).__init__(msg)


class IllegalOperation(Exception):
    """
    No, no, no!
    """

    def __init__(self, msg):
        super(IllegalOperation, self).__init__(msg)


class InvalidConfiguration(Exception):
    """
    Mucked up something.
    """

    def __init__(self, msg):
        super(InvalidConfiguration, self).__init__(msg)


class RemoteEndFailed(Exception):
    """
    The remote side failed
    """

    def __init__(self, msg):
        super(RemoteEndFailed, self).__init__(msg)


class WhatTheHeck(Exception):
    """
    Mucked up something.
    """

    def __init__(self, msg):
        super(WhatTheHeck, self).__init__(msg)
