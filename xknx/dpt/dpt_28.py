"""Implementation of KNX v02.02.01 - Datapoint Types 03.07.02 - §3.27 Unicode UTF-8 String A[n]."""

from __future__ import annotations

from .dpt_24 import DPTVariableLatin1


class DPTUTF8(DPTVariableLatin1):
    """
    Abstraction for a KNX variable length UTF-8 string.

    DPT 28.001

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.27.1: encoded with UTF-8, "the string
    shall be terminated by the NULL- character (00h). No length information shall be
    transmitted in the APDU." Like DPT 24.001, apart from the encoding.
    """

    dpt_main_number = 28
    dpt_sub_number = 1
    value_type = "utf_8"

    _encoding = "utf_8"
