"""Utility functions for testing."""
from io import StringIO
import logging
from unittest.mock import patch

from xknx.config import yaml_loader

logger = logging.getLogger("xknx.log")


def patch_yaml_files(files_dict, endswith=True):
    """Patch load_yaml with a dictionary of yaml files."""
    # match using endswith, start search with longest string
    matchlist = sorted(list(files_dict.keys()), key=len) if endswith else []

    def mock_open_f(fname, **_):
        """Mock open() in the yaml module, used by load_yaml."""
        # Return the mocked file on full match
        if fname in files_dict:
            logger.debug("patch_yaml_files match %s", fname)
            res = StringIO(files_dict[fname])
            setattr(res, "name", fname)
            return res

        # Match using endswith
        for ends in matchlist:
            if fname.endswith(ends):
                logger.debug("patch_yaml_files end match %s: %s", ends, fname)
                res = StringIO(files_dict[ends])
                setattr(res, "name", fname)
                return res

        # Not found
        raise FileNotFoundError(f"File not found: {fname}")

    return patch.object(yaml_loader, "open", mock_open_f, create=True)
