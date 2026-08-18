"""Constants shared by the DMP_InterfaceObject* procedures."""

from __future__ import annotations

# nr_of_elem field is 4 bits in both A_PropertyValue_Read (KNX v02.01.01 -
# Application Layer 03.03.07 - §3.4.4 Figure 46) and A_PropertyValue_Write
# (Figure 48), max value 2^4 - 1
MAX_ELEMENTS_PER_REQUEST = (1 << 4) - 1

# Fixed non-data octets of a PropertyValue*-PDU, in the same units as
# PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 - §4.3.7) and
# apci.PropertyValueWrite.calculated_length(): the APCI-carrying octet +
# object_index + property_id + (count|start_index_hi) + start_index_lo = 5.
# This excludes the leading TPCI octet - see cemi/const.py
# STANDARD_FRAME_MAX_NPDU_LENGTH, which caps calculated_length() the same way
# ("an L_Data_Standard frame can carry at most 15 octets after the TPCI
# octet"). Subtracting this from a max_apdu_length budget gives the octets
# left over for `data`.
PROPERTY_VALUE_HEADER_OCTETS = 5
