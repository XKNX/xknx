"""
This is a helper class to support async testcases.
"""

from asyncio import coroutine

import unittest
from unittest.mock import Mock

class Testcase:
    def __getattr__(self,k):
        if k.startswith("assert"):
            if not hasattr(self,"_unittest_"):
                self._unittest_ = unittest.TestCase()
            return getattr(self._unittest_,k)
        raise AttributeError(k)
    pass

def CoroMock():
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    return corofunc
