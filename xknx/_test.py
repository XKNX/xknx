"""
This is a helper class to support async testcases.
"""

from asyncio import coroutine

import unittest
from unittest.mock import MagicMock

class Testcase:
    def __getattr__(self,k):
        if k.startswith("assert"):
            if not hasattr(self,"_unittest_"):
                self._unittest_ = unittest.TestCase()
            return getattr(self._unittest_,k)
        raise AttributeError(k)
    pass

class CoroMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
