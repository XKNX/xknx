"""Constants shared by the DMP_InterfaceObject* procedures."""

from __future__ import annotations

# nr_of_elem field is 4 bits in both A_PropertyValue_Read (KNX v02.01.01 -
# Application Layer 03.03.07 - §3.4.4 Figure 46) and A_PropertyValue_Write
# (Figure 48), max value 2^4 - 1
MAX_ELEMENTS_PER_REQUEST = (1 << 4) - 1
