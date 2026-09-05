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

# Fixed non-data octets of a FunctionPropertyCommand/FunctionPropertyState*-PDU,
# matching apci.FunctionPropertyCommand.calculated_length(): the APCI-carrying
# octet + object_index + property_id = 3. Same units as
# PROPERTY_VALUE_HEADER_OCTETS above. Unlike Property/Memory services, a
# Function Property command is not array-shaped, so an oversized command is
# rejected outright rather than chunked - the spec describes no way to split
# one across multiple PDUs.
FUNCTION_PROPERTY_HEADER_OCTETS = 3

# Fixed non-data octets of a FunctionPropertyExtCommand/FunctionPropertyExt-
# State*-PDU, matching apci.FunctionPropertyExtCommand.calculated_length():
# the extended 2 octet APCI + 2 octet Interface Object Type + 12 bit Object
# Instance/12 bit Property ID packed into 3 octets = 6. Same non-chunking
# rationale as FUNCTION_PROPERTY_HEADER_OCTETS above.
FUNCTION_PROPERTY_EXT_HEADER_OCTETS = 6
