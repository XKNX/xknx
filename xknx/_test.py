"""This is a helper class to support async testcases."""

import anyio
import unittest
from unittest.mock import MagicMock
from math import log10
from .xknx import XKNX

try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager


class Testcase:
    # pylint: disable=too-few-public-methods
    """A fake-unittest class.

    This class is a replacement for Unittest.Testacse. It allows the user
    to continue to use unittests assertFOO methods without actually
    subclassing `unittest.TestCase`, as that breaks pytest.
    """

    __unittest = None

    def __getattr__(self, k):
        # pylint: disable=attribute-defined-outside-init
        """Redirect assert* functions to unittext."""
        if k.startswith("assert"):
            if self.__unittest is None:
                self.__unittest = unittest.TestCase()
            return getattr(self.__unittest, k)
        raise AttributeError(k)

    def assertAlmostEqual(self, a, b, prec=6):
        if a == b: return
        an = round(a, prec-int(log10(abs(a))))
        bn = round(b, prec-int(log10(abs(b))))
        assert an == bn, (a,an,b,bn)


try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(MagicMock):
        """
        A "cheap" MagicMock subclass which behaves like an async function.

        The real AsyncMock in Python 3.8 is a lot more involved, but this
        is sufficient for us.
        """

        async def __call__(self, *args, **kwargs):
            # no it is not useless.
            # pylint: disable=useless-super-delegation
            """Translate async-to-sync calling convention."""
            side, self._mock_side_effect = self._mock_side_effect, None
            try:
                res = super().__call__(*args, **kwargs)
                if side is not None:
                    await side()
            finally:
                self._mock_side_effect = side
            return res

@asynccontextmanager
async def xknx_running():
    xknx = XKNX()
    async with anyio.create_task_group() as tg:
        xknx.task_group = tg
        try:
            yield xknx
        finally:
            xknx.task_group = None
            await tg.cancel_scope.cancel()

