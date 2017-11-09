"""
KNX Group related tools.

Most tools inside this submodule are usefull helpers for XKNX Devices
and KNX Groups.
"""


def is_group(group_address):
    """
    Check if `group_address` could be a valid KNX Group Adress.

    Returns `True` if `group_address` is a object useable as input for
    and KNX Group or XKNX Device.
    """
    # True/False are also a instance of int, but not valid as group address
    if isinstance(group_address, bool):
        pass
    elif isinstance(group_address, str):
        # An empty string can never be a group address
        # TODO: Check strings with regular expressions
        if not group_address == '':
            return True
    elif isinstance(group_address, int):
        # Group addresses as integer, have an allowed range of 1-65536
        if group_address >= 1 and group_address <= 65536:
            return True
    return False
