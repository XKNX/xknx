"""Constants shared by the DMP_* device management procedures."""

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

# Fixed non-data octets of a Memory*-PDU (KNX v02.01.01 - Application Layer
# 03.03.07 - §3.5.3 A_Memory_Read / §3.5.4 A_Memory_Write, Figures 74-76):
# octet 6 is TPCI, octet 7 the APCI-carrying octet + count, octets 8-9 the 16
# bit address, data from octet 10 - so 3 octets of header after the TPCI
# octet, matching apci.MemoryRead.calculated_length() and the spec's own
# error-handling clause ("number... greater than Maximum APDU Length - 3").
# Same units as PROPERTY_VALUE_HEADER_OCTETS above.
MEMORY_HEADER_OCTETS = 3
# count is 6 bits in A_Memory_Read/_Write/_Response (1-63 octets, §3.5.3/4),
# max value 2^6 - 1
MEMORY_MAX_COUNT = (1 << 6) - 1

# Fixed non-data octets of a UserMemory*-PDU (KNX v02.01.01 - Application
# Layer 03.03.07 - §3.5.6.2 A_UserMemory_Read / §3.5.6.3 A_UserMemory_Write,
# Figures 79-81): the extended 2 octet APCI (its second octet packing the 4
# bit address extension and 4 bit count) + a 2 octet address = 4 octets of
# header after the TPCI octet, matching apci.UserMemoryRead.calculated_length()
# and the spec's own error-handling clause ("number... greater than Maximum
# APDU Length - 4"). Same units as PROPERTY_VALUE_HEADER_OCTETS above.
USER_MEMORY_HEADER_OCTETS = 4
# count is 4 bits in A_UserMemory_Read/_Write/_Response (1-15 octets,
# §3.5.6.2/3), max value 2^4 - 1
USER_MEMORY_MAX_COUNT = (1 << 4) - 1

# The value written to PID_LOAD_STATE_CONTROL is always 10 octets: the event,
# then additional information for it - KNX v01.10.01 - Resources 03.05.01 -
# §4.2.5 and KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.
LOAD_CONTROL_LENGTH = 10
# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.1: "The transitions between the
# states shall be less than 30 seconds. This time shall be the minimum delay
# during which a MaC shall wait after sending a load event until
# interpretation of the load event with the expected state transition to be
# failed."
LOAD_STATE_TRANSITION_TIMEOUT = 30.0
# KNX v01.10.01 - Resources 03.05.01 - §4.23.2.4.1: the period for reading the
# load state during LoadCompleting "shall not exceed half the TL-timeout, i.e.
# 3 seconds".
LOAD_STATE_MAX_POLL_INTERVAL = 3.0
LOAD_STATE_POLL_INTERVAL = 1.0

# Memory mapped Load State Machines of mask version 070nh (BIM M112) - KNX
# v02.01.02 - Management Procedures 03.05.02 - §3.31.2, §3.32.2 and §3.33.2.
MEM_MANAGEMENT_CONTROL_ADDRESS = 0x0104
