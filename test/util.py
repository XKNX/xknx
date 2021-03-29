"""Utility functions for testing."""
try:
    from unittest.mock import AsyncMock
except ImportError:
    from unittest.mock import MagicMock

    # needed for Python 3.7
    class AsyncMock(MagicMock):
        """Async Mock."""

        # pylint: disable=invalid-overridden-method,useless-super-delegation
        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)
