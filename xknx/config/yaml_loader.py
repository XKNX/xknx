"""Custom YAML loader."""
from collections import OrderedDict
import fnmatch
import logging
import os
from typing import Dict, Iterator, List, TypeVar, Union

from xknx.config.objects import NodeListClass, NodeStrClass
from xknx.exceptions import XKNXException
import yaml

logger = logging.getLogger("xknx.log")

JSON_TYPE = Union[List, Dict, str]  # pylint: disable=invalid-name
DICT_T = TypeVar("DICT_T", bound=Dict)  # pylint: disable=invalid-name


class SafeLineLoader(yaml.SafeLoader):
    """Loader class that keeps track of line numbers."""

    def compose_node(self, parent: yaml.nodes.Node, index: int) -> yaml.nodes.Node:
        """Annotate a node with the first line it was seen."""
        last_line: int = self.line
        node: yaml.nodes.Node = super().compose_node(parent, index)
        node.__line__ = last_line + 1  # type: ignore
        return node


def _add_reference(obj, loader: SafeLineLoader, node: yaml.nodes.Node):  # type: ignore
    """Add file reference information to an object."""
    if isinstance(obj, list):
        obj = NodeListClass(obj)
    if isinstance(obj, str):
        obj = NodeStrClass(obj)
    setattr(obj, "__config_file__", loader.name)
    setattr(obj, "__line__", node.start_mark.line)
    return obj


def load_yaml(fname: str) -> JSON_TYPE:
    """Load a YAML file."""
    try:
        with open(fname, encoding="utf-8") as conf_file:
            # If configuration file is empty YAML returns None
            # We convert that to an empty dict
            return yaml.load(conf_file, Loader=SafeLineLoader) or OrderedDict()
    except yaml.YAMLError as exc:
        logger.error(str(exc))
        raise XKNXException(exc) from exc
    except UnicodeDecodeError as exc:
        logger.error("Unable to read file %s: %s", fname, exc)
        raise XKNXException(exc) from exc


def _include_yaml(loader: SafeLineLoader, node: yaml.nodes.Node) -> JSON_TYPE:
    """Load another YAML file and embeds it using the !include tag.

    Example:
        device_tracker: !include device_tracker.yaml

    """
    fname = os.path.join(os.path.dirname(loader.name), node.value)
    try:
        return _add_reference(load_yaml(fname), loader, node)
    except FileNotFoundError as exc:
        raise XKNXException(f"{node.start_mark}: Unable to read file {fname}.") from exc


def _is_file_valid(name: str) -> bool:
    """Decide if a file is valid."""
    return not name.startswith(".")


def _find_files(directory: str, pattern: str) -> Iterator[str]:
    """Recursively load files in a directory."""
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if _is_file_valid(d)]
        for basename in sorted(files):
            if _is_file_valid(basename) and fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def _construct_seq(loader: SafeLineLoader, node: yaml.nodes.Node) -> JSON_TYPE:
    """Add line number and file name to Load YAML sequence."""
    (obj,) = loader.construct_yaml_seq(node)
    return _add_reference(obj, loader, node)


def _include_dir_list_yaml(
    loader: SafeLineLoader, node: yaml.nodes.Node
) -> List[JSON_TYPE]:
    """Load multiple files from directory as a list."""
    loc = os.path.join(os.path.dirname(loader.name), node.value)
    return [load_yaml(f) for f in _find_files(loc, "*.yaml")]


def _env_var_yaml(loader: SafeLineLoader, node: yaml.nodes.Node) -> str:
    """Load environment variables and embed it into the configuration YAML."""
    args = node.value.split()

    # Check for a default value
    if len(args) > 1:
        return os.getenv(args[0], " ".join(args[1:]))
    if args[0] in os.environ:
        return os.environ[args[0]]
    logger.error("Environment variable %s not defined", node.value)
    raise XKNXException(node.value)


SafeLineLoader.add_constructor("!include", _include_yaml)
SafeLineLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, _construct_seq
)
SafeLineLoader.add_constructor("!env_var", _env_var_yaml)
SafeLineLoader.add_constructor("!include_dir_list", _include_dir_list_yaml)
