# -*- coding: utf-8 -*-

class BadToken(Exception):
    """
    Token is bad
    """

    def __init__(self, msg):
        super(BadToken, self).__init__(msg)


class NoSuchJob(Exception):
    """
    Missing Job
    """

    def __init__(self, msg):
        super(NoSuchJob, self).__init__(msg)


class InvalidConfiguration(Exception):
    """
    Mucked up something.
    """

    def __init__(self, msg):
        super(InvalidConfiguration, self).__init__(msg)
