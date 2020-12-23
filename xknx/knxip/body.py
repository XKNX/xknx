"""Basis class for all KNX/IP bodies."""
from abc import ABC, abstractmethod
import logging
from typing import ClassVar, cast

from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType

logger = logging.getLogger("xknx.log")


class KNXIPBody(ABC):
    """Base class for all KNX/IP bodies."""

    service_type: ClassVar[KNXIPServiceType] = cast(KNXIPServiceType, None)

    def __init__(self, xknx):
        """Initialize KNXIPBody object."""
        self.xknx = xknx

    @abstractmethod
    def calculated_length(self):
        """Get length of KNX/IP body."""

    @abstractmethod
    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""

    @abstractmethod
    def to_knx(self):
        """Serialize to KNX/IP raw data."""

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__


class KNXIPBodyResponse(KNXIPBody):
    """Base class for all KNX/IP response bodies."""

    status_code: ErrorCode = cast(ErrorCode, None)
