"""
Module for reading config files (xknx.yaml).

* it will parse the given file
* and add the found devices to the devies vector of XKNX.
"""
import logging
from typing import TYPE_CHECKING

import yaml

from .config_v1 import ConfigV1

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Config:
    """Class for parsing xknx.yaml."""

    def __init__(self, xknx: "XKNX") -> None:
        """Initialize Config class."""
        self.xknx = xknx

    def read(self, file: str = "xknx.yaml") -> None:
        """Read config."""
        logger.debug("Reading %s", file)
        try:
            with open(file) as filehandle:
                doc = yaml.safe_load(filehandle)
                ConfigV1(xknx=self.xknx).parse(doc)
        except FileNotFoundError as ex:
            logger.error("Error while reading %s: %s", file, ex)
