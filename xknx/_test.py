"""
This is a helper class to support async testcases.
"""

import unittest
from unittest.mock import MagicMock

class Testcase:
    # pylint: disable=too-few-public-methods
    """
    A fake-unittest class which allows the user to use unittests assertFOO
    methods without subclassing `unittest.TestCase`.
    """
    __unittest = None

    def __getattr__(self, k):
        # pylint: disable=attribute-defined-outside-init
        if k.startswith("assert"):
            if self.__unittest is None:
                self.__unittest = unittest.TestCase()
            return getattr(self.__unittest, k)
        raise AttributeError(k)

