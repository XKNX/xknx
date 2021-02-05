import pytest
@pytest.fixture
def anyio_backend():
    return "trio"
