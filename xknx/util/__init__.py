"""Helper functions for XKNX."""
import sys

# Backport of `asyncio.timeout` to be able to replace `asyncio.wait_for`
# in py3.9 and py3.10 see https://github.com/python/cpython/pull/98518
if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout
else:
    from asyncio import timeout as asyncio_timeout


__all__ = ["asyncio_timeout"]
