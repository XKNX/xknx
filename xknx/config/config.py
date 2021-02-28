"""
Module for reading config files (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any, Dict

from .config_v1 import ConfigV1
from .yaml_loader import load_yaml

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Version(Enum):
    """The used xknx.yaml structure version."""

    VERSION_1 = 1
    VERSION_2 = 2


class Config:
    """Class for parsing xknx.yaml."""

    def __init__(self, xknx: "XKNX") -> None:
        """Initialize Config class."""
        self.xknx = xknx

    def read(self, file: str = "xknx.yaml") -> None:
        """Read config."""
        logger.debug("Reading %s", file)
        doc = load_yaml(file)
        assert isinstance(doc, dict)
        self.parse(doc)

    @staticmethod
    def parse_version(doc: Dict[str, Any]) -> Version:
        """Parse the version of the xknx.yaml."""
        if "version" in doc:
            return Version(doc["version"])
        return Version.VERSION_1

    def parse(self, doc: Dict[str, Any]) -> None:
        """Parse the config from the YAML."""
        version = Config.parse_version(doc)
        if version is Version.VERSION_1:
            ConfigV1(xknx=self.xknx).parse(doc)
        elif version is Version.VERSION_2:
            raise NotImplementedError("Version 2 not yet implemented.")
