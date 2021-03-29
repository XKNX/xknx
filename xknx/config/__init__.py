"""Module for managing xknx config parsing and validation."""
# flake8: noqa
from .config import Config
from .config_v1 import ConfigV1

__all__ = [
    "Config",
    "ConfigV1",
]
