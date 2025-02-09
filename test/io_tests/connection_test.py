"""Unit test for xknx.io.connection module."""

from xknx.io.connection import ConnectionConfig, SecureConfig


def test_connection_config_compare() -> None:
    """Test ConnectionConfig comparison."""
    assert ConnectionConfig() == ConnectionConfig()
    assert ConnectionConfig() != ConnectionConfig(individual_address="1.1.1")


def test_secure_config_compare() -> None:
    """Test SecureConfig comparison."""
    assert SecureConfig() == SecureConfig()
    assert SecureConfig() != SecureConfig(user_id=5)
