import io
import os
from unittest.mock import patch

import pytest
from xknx.config import yaml_loader
from xknx.exceptions import XKNXException
import yaml

from test.util import patch_yaml_files


def test_simple_list():
    """Test simple list."""
    conf = "config:\n  - simple\n  - list"
    with io.StringIO(conf) as file:
        doc = yaml_loader.yaml.safe_load(file)
    assert doc["config"] == ["simple", "list"]


def test_simple_dict():
    """Test simple dict."""
    conf = "key: value"
    with io.StringIO(conf) as file:
        doc = yaml_loader.yaml.safe_load(file)
    assert doc["key"] == "value"


@patch("xknx.config.yaml_loader.open", create=True)
def test_load_yaml_encoding_error(mock_open):
    """Test raising a UnicodeDecodeError."""
    mock_open.side_effect = UnicodeDecodeError("", b"", 1, 0, "")
    with pytest.raises(XKNXException):
        yaml_loader.load_yaml("test")


@patch("xknx.config.yaml_loader.open", create=True)
def test_load_yaml_loading_error(mock_open):
    """Test raising a YAMLError."""
    mock_open.side_effect = yaml.error.YAMLError
    with pytest.raises(XKNXException):
        yaml_loader.load_yaml("test")


@patch("xknx.config.yaml_loader.os.walk")
def test_include_dir_list(mock_walk):
    """Test include dir list yaml."""
    mock_walk.return_value = [["/test", [], ["two.yaml", "one.yaml"]]]

    with patch_yaml_files({"/test/one.yaml": "one", "/test/two.yaml": "two"}):
        conf = "key: !include_dir_list /test"
        with io.StringIO(conf) as file:
            doc = yaml_loader.yaml.safe_load(file)
            assert doc["key"] == sorted(["one", "two"])


def test_environment_variable():
    """Test config file with environment variable."""
    os.environ["XKNX_HOST"] = "192.168.30.32"
    conf = "host: !env_var XKNX_HOST"
    with io.StringIO(conf) as file:
        doc = yaml_loader.yaml.safe_load(file)
    assert doc["host"] == "192.168.30.32"
    del os.environ["XKNX_HOST"]


def test_environment_variable_default():
    """Test config file with default value for environment variable."""
    conf = "host: !env_var XKNX_HOST 127.0.0.1"
    with io.StringIO(conf) as file:
        doc = yaml_loader.yaml.safe_load(file)
    assert doc["host"] == "127.0.0.1"


def test_invalid_environment_variable():
    """Test config file with no environment variable sat."""
    conf = "host: !env_var XKNX_HOST"
    with pytest.raises(XKNXException):
        with io.StringIO(conf) as file:
            yaml_loader.yaml.safe_load(file)


def test_include_yaml():
    """Test include yaml."""
    with patch_yaml_files({"test.yaml": "value"}):
        conf = "key: !include test.yaml"
        with io.StringIO(conf) as file:
            doc = yaml_loader.yaml.safe_load(file)
            assert doc["key"] == "value"

    with patch_yaml_files({"test.yaml": None}):
        conf = "key: !include test.yaml"
        with io.StringIO(conf) as file:
            doc = yaml_loader.yaml.safe_load(file)
            assert doc["key"] == {}


def test_include_yaml_error():
    """Test include yaml error."""
    with patch_yaml_files({"test.yaml": "value"}):
        conf = "key: !include test2.yaml"
        with io.StringIO(conf) as file:
            with pytest.raises(XKNXException):
                doc = yaml_loader.yaml.safe_load(file)
                assert doc["key"] == "value"
