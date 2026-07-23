"""Implementation of 3.4 Datapoint Types Character Set."""

from __future__ import annotations

from .dpt_16 import DPTString


class DPTCharacter(DPTString):
    """
    Abstraction for KNX 1 Octet ASCII character.

    A single character is encoded/decoded as a length-1 string, sharing the
    logic of `DPTString` (DPT 16) with a 1-octet payload.

    DPT 4.001
    """

    payload_length = 1
    dpt_main_number = 4
    dpt_sub_number = 1
    value_type = "character"

    _encoding = "ascii"


class DPTCharacterLatin1(DPTCharacter):
    """
    Abstraction for KNX 1 Octet Latin-1 (ISO 8859-1) character.

    DPT 4.002
    """

    dpt_main_number = 4
    dpt_sub_number = 2
    value_type = "character_latin_1"
    _encoding = "latin_1"
