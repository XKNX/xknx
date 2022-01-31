"""
This package contains objects for programming a device.

- NetworkManagement provides the management functions.
- ProgDevice is the proxy for the programming device.
"""
from .device import ProgDevice

# flake8: noqa
from .management import NetworkManagement

__all__ = [
    "NetworkManagement",
    "ProgDevice",
]
