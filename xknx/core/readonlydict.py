"""Module for the ReadOnlyDict class."""
import copy


class ReadOnlyDict(dict):
    """Dictionary which doesn't allow to add or remove items."""
	# pylint: disable=no-self-use
    def __readonly__(self, *args, **kwargs):
		"""Throw runtime error when trying to modify the dict."""
        raise RuntimeError("Cannot modify ReadOnlyDict")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    popitem = __readonly__
    clear = __readonly__
    update = __readonly__
    setdefault = __readonly__
    del __readonly__
    __copy__ = dict.copy
	# pylint: disable-protected-access
    __deepcopy__ = copy._deepcopy_dispatch.get(dict)
