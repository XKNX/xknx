"""Basis class for all KNX/IP bodies."""
from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING, ClassVar, cast

from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class KNXIPBody(ABC):
    """Base class for all KNX/IP bodies."""

    SERVICE_TYPE: ClassVar[KNXIPServiceType] = cast(KNXIPServiceType, None)

    def __init__(self, xknx: XKNX):
        """Initialize KNXIPBody object."""
        self.xknx = xknx

    @abstractmethod
    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""

    @abstractmethod
    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

    @abstractmethod
    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__


class KNXIPBodyResponse(KNXIPBody):
    """Base class for all KNX/IP response bodies."""

    status_code: ErrorCode = cast(ErrorCode, None)
