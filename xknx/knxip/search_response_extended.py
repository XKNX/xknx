"""
Module for Serialization and Deserialization of KNX Search Response Extended.

Search Requests Extended are used to search for KNX/IP devices within the network.
A search response extended contains all information of a found device (Name, serial number, supported features.).
It supports an array-style access to the DIBs (use classname as index). Every KNXnet/ip server shall send
a search response extended and one device supporting multiple KNX connections may send multiple search responses.

If there were any SRPs (Search Request Parameters) in the Search Request Extended and those were marked as mandatory
the server shall only reply to those requests if it can fulfill the requirements in the SRP.
"""
from __future__ import annotations

from .knxip_enum import KNXIPServiceType
from .search_response import SearchResponse


class SearchResponseExtended(SearchResponse):
    """Representation of a KNX Search Extended."""

    SERVICE_TYPE = KNXIPServiceType.SEARCH_RESPONSE_EXTENDED

    def __repr__(self) -> str:
        """Return object as readable string."""
        _dibs_str = ",\n".join(dib.__str__() for dib in self.dibs)
        return (
            "<SearchResponseExtended "
            f'control_endpoint="{self.control_endpoint}" '
            f'dibs="[\n{_dibs_str}\n]" />'
        )
