"""
This package contains objects for programming a device.

- NetworkManagement provides the management functions.
- ProgDevice is the proxy for the programming device.
"""
# flake8: noqa
from .management import NetworkManagement
from .device import ProgDevice

__all__ = [
    "NetworkManagement",
    "ProgDevice",
]
