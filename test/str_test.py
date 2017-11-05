"""Unit test for String representations."""
import unittest
import asyncio

from xknx import XKNX
from xknx.devices import Light, Switch, Cover, Climate, Time, \
    BinarySensor, Action, Sensor, Notification, RemoteValue, \
    ActionBase, ActionCallback
from xknx.knx import DPTArray, DPTBinary, Address, Telegram
from xknx.exceptions import CouldNotParseTelegram, CouldNotParseKNXIP, \
    ConversionError, CouldNotParseAddress, DeviceIllegalValue
from xknx.knxip import DIB, DIBGeneric, DIBDeviceInformation, \
    DIBSuppSVCFamilies, DIBTypeCode, KNXMedium, DIBServiceFamily

# pylint: disable=too-many-public-methods,invalid-name
class TestStringRepresentations(unittest.TestCase):
    """Test class for Configuration logic."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_remote_value(self):
        """Test string representation of remote value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValue(
            xknx,
            group_address='1/2/3',
            group_address_state='1/2/4')
        self.assertEqual(
            str(remote_value),
            '<RemoteValue <Address str="1/2/3" />/<Address str="1/2/4" />/None/None/>')
        remote_value.payload = DPTArray([0x01, 0x02])
        self.assertEqual(
            str(remote_value),
            '<RemoteValue <Address str="1/2/3" />/<Address str="1/2/4" />/<DPTArray value="[0x1,0x2]" />/None/>')

    def test_binary_sensor(self):
        """Test string representation of binary sensor object."""
        xknx = XKNX(loop=self.loop)
        binary_sensor = BinarySensor(
            xknx,
            name='Fnord',
            group_address='1/2/3',
            device_class='motion')
        self.assertEqual(
            str(binary_sensor),
            '<BinarySensor group_address="<Address str="1/2/3" />" name="Fnord" state="BinarySensorState.OFF"/>')

    def test_climate(self):
        """Test string representation of climate object."""
        xknx = XKNX(loop=self.loop)
        climate = Climate(
            xknx,
            name="Wohnzimmer",
            group_address_temperature='1/2/1',
            group_address_target_temperature='1/2/2',
            group_address_setpoint_shift='1/2/3',
            group_address_setpoint_shift_state='1/2/4',
            setpoint_shift_step=0.1,
            setpoint_shift_max=20,
            setpoint_shift_min=-20,
            group_address_operation_mode='1/2/5',
            group_address_operation_mode_state='1/2/6',
            group_address_operation_mode_protection='1/2/7',
            group_address_operation_mode_night='1/2/8',
            group_address_operation_mode_comfort='1/2/9',
            group_address_controller_status='1/2/10',
            group_address_controller_status_state='1/2/11')
        self.assertEqual(
            str(climate),
            '<Climate name="Wohnzimmer" temperature="<Address str="1/2/1" />/None/None/None"  target_temperature="<Address str="1/2/2" />/None/None/'
            'None"  setpoint_shift="<Address str="1/2/3" />/<Address str="1/2/4" />/None/None" setpoint_shift_step="0.1" setpoint_shift_max="20" set'
            'point_shift_min="-20" group_address_operation_mode="<Address str="1/2/5" />" group_address_operation_mode_state="<Address str="1/2/6" /'
            '>" group_address_controller_status="<Address str="1/2/10" />" group_address_controller_status_state="<Address str="1/2/11" />" />')

    def test_cover(self):
        """Test string representation of cover object."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            name='Rolladen',
            group_address_long='1/2/3',
            group_address_short='1/2/4',
            group_address_position='1/2/5',
            group_address_position_state='1/2/6',
            group_address_angle='1/2/7',
            group_address_angle_state='1/2/8',
            travel_time_down=8,
            travel_time_up=10)
        self.assertEqual(
            str(cover),
            '<Cover name="Rolladen" updown"<Address str="1/2/3" />/None/None/None" step="<Address str="1/2/4" />/None/None/None" position="<Address '
            'str="1/2/5" />/<Address str="1/2/6" />/None/None" angle="<Address str="1/2/7" />/<Address str="1/2/8" />/None/None" travel_time_down="8'
            '" travel_time_up="10" />')

    def test_light(self):
        """Test string representation of light object."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            name='Licht',
            group_address_switch='1/2/3',
            group_address_switch_state='1/2/4',
            group_address_brightness='1/2/5',
            group_address_brightness_state='1/2/6')
        self.assertEqual(
            str(light),
            '<Light name="Licht" switch="<Address str="1/2/3" />/<Address str="1/2/4" />/None/None" group_address_brightness="<Address str="1/2/5" /'
            '>" group_address_brightness_state="<Address str="1/2/6" />" brightness="0" />')

    def test_notification(self):
        """Test string representation of notification object."""
        xknx = XKNX(loop=self.loop)
        notification = Notification(
            xknx,
            name='Alarm',
            group_address='1/2/3')
        self.assertEqual(
            str(notification),
            '<Notification name="Alarm" group_address="<Address str="1/2/3" />" message="" />')
        notification.message = 'Einbrecher im Haus'
        self.assertEqual(
            str(notification),
            '<Notification name="Alarm" group_address="<Address str="1/2/3" />" message="Einbrecher im Haus" />')

    def test_sensor(self):
        """Test string representation of sensor object."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            name='MeinSensor',
            group_address='1/2/3',
            value_type='percent')
        self.assertEqual(
            str(sensor),
            '<Sensor name="MeinSensor" group_address="<Address str="1/2/3" />" state="None" resolve_state="None" />')
        self.loop.run_until_complete(asyncio.Task(sensor._set_internal_state(DPTArray((0x23)))))  # pylint: disable=protected-access
        self.assertEqual(
            str(sensor),
            '<Sensor name="MeinSensor" group_address="<Address str="1/2/3" />" state="<DPTArray value="[0x23]" />" resolve_state="14" />')

    def test_switch(self):
        """Test string representation of switch object."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(
            xknx,
            name="Schalter",
            group_address="1/2/3",
            group_address_state="1/2/4")
        self.assertEqual(
            str(switch),
            '<Switch name="Schalter" switch="<Address str="1/2/3" />/<Address str="1/2/4" />/None/None" />')

    def test_time(self):
        """Test string representation of time object."""
        xknx = XKNX(loop=self.loop)
        time = Time(
            xknx,
            name="Zeit",
            group_address="1/2/3")
        self.assertEqual(
            str(time),
            '<Time name="Zeit" group_address="<Address str="1/2/3" />" />')

    def test_action_base(self):
        """Test string representation of action base."""
        xknx = XKNX(loop=self.loop)
        action_base = ActionBase(
            xknx,
            hook='off',
            counter='2')
        self.assertEqual(
            str(action_base),
            '<ActionBase hook="off" counter="2"/>')

    def test_action(self):
        """Test string representation of action."""
        xknx = XKNX(loop=self.loop)
        action = Action(
            xknx,
            hook="on",
            target='Licht1',
            method='off',
            counter=2)
        self.assertEqual(
            str(action),
            '<Action target="Licht1" method="off" <ActionBase hook="on" counter="2"/>/>')

    def test_action_callback(self):
        """Test string representation of action callback."""
        xknx = XKNX(loop=self.loop)

        def cb():
            """Callback."""
            pass

        action = ActionCallback(
            xknx,
            callback=cb,
            hook="on",
            counter=2)
        self.assertEqual(
            str(action),
            '<ActionCallback callback="cb" <ActionBase hook="on" counter="2"/>/>')

    def test_could_not_parse_telegramn_exception(self):
        """Test string representation of CouldNotParseTelegram exception."""
        exception = CouldNotParseTelegram(description='Fnord')
        self.assertEqual(
            str(exception),
            '<CouldNotParseTelegram description="Fnord" />')

    def test_could_not_parse_knxip_exception(self):
        """Test string representation of CouldNotParseKNXIP exception."""
        exception = CouldNotParseKNXIP(description='Fnord')
        self.assertEqual(
            str(exception),
            '<CouldNotParseKNXIP description="Fnord" />')

    def test_conversion_error_exception(self):
        """Test string representation of ConversionError exception."""
        exception = ConversionError(value='Fnord')
        self.assertEqual(
            str(exception),
            '<ConversionError value="Fnord" />')

    def test_could_not_parse_address_exception(self):
        """Test string representation of CouldNotParseAddress exception."""
        exception = CouldNotParseAddress(address='1/2/1000')
        self.assertEqual(
            str(exception),
            '<CouldNotParseAddress address="1/2/1000" />')

    def test_device_illegal_value_exception(self):
        """Test string representation of DeviceIllegalValue exception."""
        exception = DeviceIllegalValue(value=12, description='Fnord exceeded')
        self.assertEqual(
            str(exception),
            '<DeviceIllegalValue description="12" value="Fnord exceeded" />')

    def test_address(self):
        """Test string representation of address object."""
        address = Address("1/2/3")
        self.assertEqual(
            str(address),
            '<Address str="1/2/3" />')

    def test_dpt_array(self):
        """Test string representation of DPTBinary."""
        dpt_array = DPTArray([0x01, 0x02])
        self.assertEqual(
            str(dpt_array),
            '<DPTArray value="[0x1,0x2]" />')

    def test_dpt_binary(self):
        """Test string representation of DPTBinary."""
        dpt_binary = DPTBinary(7)
        self.assertEqual(
            str(dpt_binary),
            '<DPTBinary value="7" />')

    def test_telegram(self):
        """Test string representation of Telegram."""
        telegram = Telegram(
            group_address=Address('1/2/3'),
            payload=DPTBinary(7))
        self.assertEqual(
            str(telegram),
            '<Telegram group_address="<Address str="1/2/3" />", payload="<DPTBinary value="7" />" telegramtype="TelegramType.GROUP_WRITE" direction='
            '"TelegramDirection.OUTGOING" />')


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestStringRepresentations)
unittest.TextTestRunner(verbosity=2).run(SUITE)
