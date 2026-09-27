"""Module for KNX Telegrams."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic

from xknx.dpt import DPTBase, DPTComplexData, DPTEnumData
from xknx.typing import TypeVar

from .address import GroupAddress, IndividualAddress, InternalGroupAddress
from .apci import APCI, GroupValueRead, GroupValueResponse, GroupValueWrite
from .tpci import TPCI, TDataBroadcast, TDataGroup, TDataIndividual

APCIT_co = TypeVar("APCIT_co", bound=APCI | None, default=APCI | None, covariant=True)

_current_telegram_context: ContextVar[Any] = ContextVar(
    "xknx_telegram_context", default=None
)


@contextmanager
def telegram_context(context: Any) -> Iterator[None]:
    """
    Attach an application defined context to outgoing telegrams created in this scope.

    Every outgoing `Telegram` created inside the `with` block - and inside tasks
    started from it - carries `context` in `Telegram.context`. xknx never reads it;
    it is passed on to device callbacks in `DeviceUpdate.context`.

        with telegram_context(my_context):
            await light.set_on()
    """
    token = _current_telegram_context.set(context)
    try:
        yield
    finally:
        _current_telegram_context.reset(token)


def current_telegram_context() -> Any:
    """Return the context set by the innermost active `telegram_context()`."""
    return _current_telegram_context.get()


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


@dataclass(slots=True)
class TelegramDecodedData:
    """Context for a telegram."""

    transcoder: type[DPTBase]
    value: bool | int | float | str | DPTComplexData | DPTEnumData

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f"{self.value}{' ' + self.transcoder.unit if self.transcoder.unit is not None else ''}"
            f" ({self.transcoder.dpt_name()})"
        )


@dataclass(slots=True)
class Telegram(Generic[APCIT_co]):
    """
    Data transfer object for KNX telegrams.

    Represents a message exchanged on the KNX bus between the business logic
    (Devices, Management, etc.) and the underlying KNX/IP abstraction layer.

    Attributes:
        destination_address: Target GroupAddress, IndividualAddress, or
            InternalGroupAddress.
        direction: Communication direction (INCOMING or OUTGOING).
        payload: APCi payload containing the actual data (e.g., GroupValueWrite,
            GroupValueResponse). None for control information only telegrams -
            parametrize as `Telegram[SomeAPCI]` where a payload is guaranteed.
        source_address: IndividualAddress of the sender. When default of 0.0.0 is
            used, it will be set automatically when sent.
        tpci: Transport Layer Control Information (TDataBroadcast, TDataGroup, or
            TDataIndividual). If not provided, it will be automatically inferred
            based on destination_address type.
        decoded_data: Optional decoded version of the payload including the
            transcoder class and decoded value. Set externally by GroupAddressDPT
            for convenience when the payload has already been decoded.
        data_secure: Flag indicating if the telegram was sent or received as
            DataSecure. Set externally by CEMIHandler. None if not yet processed.
        context: Application defined object identifying the origin of the telegram.
            Never read by xknx. Outgoing telegrams default to the context of the
            active `telegram_context()`; for incoming telegrams it may be set by
            a telegram received callback, which runs before devices process it.

    """

    destination_address: GroupAddress | IndividualAddress | InternalGroupAddress
    direction: TelegramDirection = TelegramDirection.OUTGOING
    payload: APCIT_co = None  # type: ignore[assignment]  # None only if APCIT_co allows it
    source_address: IndividualAddress = field(
        default_factory=lambda: IndividualAddress(0)
    )
    tpci: TPCI = None  # type: ignore[assignment]  # set by initializer or in __post_init__
    context: Any = field(default=None, compare=False, hash=False, repr=False)
    # set by GroupAddressDPT
    decoded_data: TelegramDecodedData | None = field(
        init=False, default=None, compare=False, hash=False
    )
    # flag if telegram was sent or received as DataSecure, set by CEMIHandler
    data_secure: bool | None = field(
        init=False, default=None, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        """Initialize Telegram class."""
        if self.context is None and self.direction is TelegramDirection.OUTGOING:
            self.context = _current_telegram_context.get()
        if self.tpci is None:
            if isinstance(self.destination_address, GroupAddress):  # type: ignore[unreachable]
                if self.destination_address.raw == 0:
                    self.tpci = TDataBroadcast()
                else:
                    self.tpci = TDataGroup()
            elif isinstance(self.destination_address, IndividualAddress):
                self.tpci = TDataIndividual()
            else:  # InternalGroupAddress
                self.tpci = TDataGroup()

    def __str__(self) -> str:
        """Return object as readable string."""
        data = f'payload="{self.payload}"' if self.payload else f'tpci="{self.tpci}"'
        decoded_data = (
            f' data="{self.decoded_data}"' if self.decoded_data is not None else ""
        )
        return (
            "<Telegram "
            f'direction="{self.direction.value}" '
            f'source_address="{self.source_address}" '
            f'destination_address="{self.destination_address}" '
            f"{data}{decoded_data} />"
        )


# Telegram carrying a value payload - the union `Device.process_group_write()` and
# `RemoteValue.process()` accept, since a GroupValueResponse is treated like a
# GroupValueWrite by default (see `Device.process_group_response()`).
GroupValueTelegram = Telegram[GroupValueWrite] | Telegram[GroupValueResponse]
GroupReadTelegram = Telegram[GroupValueRead]
