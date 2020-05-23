"""Unit test for registering custom Device classes"""

import asyncio
import os
import pathlib
import unittest

from xknx import XKNX
from xknx.devices import Device


class CustomDevice(Device):
    def __init__(self,
                 xknx,
                 name,
                 group_address_state=None,
                 my_custom_attribute=""):
        """Initialize CustomDevice class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name)
        self.group_address_state = group_address_state
        self.my_custom_attribute = my_custom_attribute

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_state = \
            config.get('group_address_state')
        my_custom_attribute = \
            config.get('my_custom_attribute')

        return cls(xknx,
                   name,
                   group_address_state=group_address_state,
                   my_custom_attribute=my_custom_attribute)

    def get_my_custom_attribute(self):
        return self.my_custom_attribute


class TestRegisterDeviceClass(unittest.TestCase):
    """Test class for registering new device classes."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # test registration of custom devices
    #
    def test_register_device_class(self):
        """Test registration of a custom device class."""
        xknx = XKNX(
                loop=self.loop,
                custom_device_classes={"custom_device": CustomDevice},
                config=os.path.join(pathlib.Path(__file__).parent.absolute(), "device_class_test.yaml")
            )
        self.assertTrue("my_example_device" in xknx.devices)
        self.assertTrue(xknx.devices["my_example_device"].__class__.__name__ == "CustomDevice")
        self.assertEqual(xknx.devices["my_example_device"].get_my_custom_attribute(), "hello world")
