"""Utility functions for testing."""
try:
    # pylint: disable=unused-import
    from unittest.mock import AsyncMock
except ImportError:
    # for Python 3.7 backwards compatibility
    # from https://github.com/timsavage/asyncmock
    from unittest.mock import NonCallableMock

    try:
        from unittest.mock import CallableMixin
    except ImportError:
        from unittest.mock import CallableMixin

    class AsyncCallableMixin(CallableMixin):
        def __init__(_mock_self, not_async=False, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _mock_self.not_async = not_async
            _mock_self.aenter_return_value = _mock_self

        def __call__(_mock_self, *args, **kwargs):
            # can't use self in-case a function / method we are mocking uses self
            # in the signature
            if _mock_self.not_async:
                _mock_self._mock_check_sig(*args, **kwargs)
                return _mock_self._mock_call(*args, **kwargs)

            else:

                async def wrapper():
                    _mock_self._mock_check_sig(*args, **kwargs)
                    return _mock_self._mock_call(*args, **kwargs)

                return wrapper()

        async def __aenter__(_mock_self):
            return _mock_self.aenter_return_value

        async def __aexit__(_mock_self, exc_type, exc_val, exc_tb):
            pass

    class AsyncMock(AsyncCallableMixin, NonCallableMock):
        """
        Create a new `AsyncMock` object. `AsyncMock` several options that extends
        the behaviour of the basic `Mock` object:
        * `not_async`: This is a boolean flag used to indicate that when the mock
        is called it should not return a normal Mock instance to make the mock
        non-awaitable. If this flag is set the mock reverts to the default
        behaviour of a `Mock` instance.
        All other arguments are passed directly through to the underlying `Mock`
        object.
        """
