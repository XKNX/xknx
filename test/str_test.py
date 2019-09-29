"""Unit test for String representations."""
import asyncio
import unittest

from xknx import XKNX
from xknx.devices import (
    Action, ActionBase, ActionCallback, BinarySensor, Climate, ClimateMode,
    Cover, DateTime, ExposeSensor, Fan, Light, Notification, Scene, Sensor,
    Switch)
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import (
    ConversionError, CouldNotParseAddress, CouldNotParseKNXIP,
    CouldNotParseTelegram, DeviceIllegalValue)
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI, CEMIFrame, ConnectionStateRequest, ConnectionStateResponse,
    ConnectRequest, ConnectRequestType, ConnectResponse, DIBDeviceInformation,
    DIBGeneric, DIBServiceFamily, DIBSuppSVCFamilies, DisconnectRequest,
    DisconnectResponse, KNXIPFrame, KNXIPHeader, KNXIPServiceType, KNXMedium,
    SearchRequest, SearchResponse, TunnellingAck, TunnellingRequest)
from xknx.remote_value import RemoteValue
from xknx.telegram import (
    GroupAddress, PhysicalAddress, Telegram, TelegramDirection)


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
            device_name="MyDevice",
            group_address_state='1/2/4')
        self.assertEqual(
            str(remote_value),
            '<RemoteValue device_name="MyDevice" GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None/>')
        remote_value.payload = DPTArray([0x01, 0x02])
        self.assertEqual(
            str(remote_value),
            '<RemoteValue device_name="MyDevice" GroupAddress("1/2/3")/GroupAddress("1/2/4")/<DPTArray value="[0x1,0x2]" />/None/>')

    def test_binary_sensor(self):
        """Test string representation of binary sensor object."""
        xknx = XKNX(loop=self.loop)
        binary_sensor = BinarySensor(
            xknx,
            name='Fnord',
            group_address_state='1/2/3',
            device_class='motion')
        self.assertEqual(
            str(binary_sensor),
            '<BinarySensor group_address_state="GroupAddress("1/2/3")" name="Fnord" state="BinarySensorState.OFF"/>')

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
            group_address_on_off='1/2/14',
            group_address_on_off_state='1/2/15')
        self.assertEqual(
            str(climate),
            '<Climate name="Wohnzimmer" temperature="None/GroupAddress("1/2/1")/None/None" '
            'target_temperature="GroupAddress("1/2/2")/None/None/None" '
            'setpoint_shift="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" '
            'setpoint_shift_step="0.1" setpoint_shift_max="20" setpoint_shift_min="-20" '
            'group_address_on_off="GroupAddress("1/2/14")/GroupAddress("1/2/15")/None/None" />')

    def test_climate_mode(self):
        """Test string representation of climate mode object."""
        xknx = XKNX(loop=self.loop)
        climate_mode = ClimateMode(
            xknx,
            name="Wohnzimmer Mode",
            group_address_operation_mode='1/2/5',
            group_address_operation_mode_state='1/2/6',
            group_address_operation_mode_protection='1/2/7',
            group_address_operation_mode_night='1/2/8',
            group_address_operation_mode_comfort='1/2/9',
            group_address_controller_status='1/2/10',
            group_address_controller_status_state='1/2/11',
            group_address_controller_mode='1/2/12',
            group_address_controller_mode_state='1/2/13')
        self.assertEqual(
            str(climate_mode),
            '<ClimateMode name="Wohnzimmer Mode" '
            'group_address_operation_mode="GroupAddress("1/2/5")" group_address_operation_mode_state="GroupAddress("1/2/6")'
            '" group_address_controller_status="GroupAddress("1/2/10")" group_address_controller_status_state="GroupAddress("1/2/11")" '
            'group_address_controller_mode="GroupAddress("1/2/12")" group_address_controller_mode_state="GroupAddress("1/2/13")" />')

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
            '<Cover name="Rolladen" updown="GroupAddress("1/2/3")/None/None/None" step="GroupAddress("1/2/4")/None/None/None" position="Group'
            'Address("1/2/5")/GroupAddress("1/2/6")/None/None" angle="GroupAddress("1/2/7")/GroupAddress("1/2/8")/None/None" travel_time_down="8'
            '" travel_time_up="10" />')

    def test_fan(self):
        """Test string representation of fan object."""
        xknx = XKNX(loop=self.loop)
        fan = Fan(
            xknx,
            name='Dunstabzug',
            group_address_speed='1/2/3',
            group_address_speed_state='1/2/4')
        self.assertEqual(
            str(fan),
            '<Fan name="Dunstabzug" speed="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" />')

    def test_light(self):
        """Test string representation of non dimmable light object."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            name='Licht',
            group_address_switch='1/2/3',
            group_address_switch_state='1/2/4')
        self.assertEqual(
            str(light),
            '<Light name="Licht" switch="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" />')

    def test_light_dimmable(self):
        """Test string representation of dimmable light object."""
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
            '<Light name="Licht" switch="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" '
            'brightness="GroupAddress("1/2/5")/GroupAddress("1/2/6")/None/None" />')

    def test_light_color(self):
        """Test string representation of dimmable light object."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            name='Licht',
            group_address_switch='1/2/3',
            group_address_switch_state='1/2/4',
            group_address_color='1/2/5',
            group_address_color_state='1/2/6')
        self.assertEqual(
            str(light),
            '<Light name="Licht" '
            'switch="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" '
            'color="GroupAddress("1/2/5")/GroupAddress("1/2/6")/None/None" />')

    def test_notification(self):
        """Test string representation of notification object."""
        xknx = XKNX(loop=self.loop)
        notification = Notification(
            xknx,
            name='Alarm',
            group_address='1/2/3',
            group_address_state='1/2/4')
        self.assertEqual(
            str(notification),
            '<Notification name="Alarm" group_address="GroupAddress("1/2/3")" group_address_state="GroupAddress("1/2/4")" message="" />')
        notification.message = 'Einbrecher im Haus'
        self.assertEqual(
            str(notification),
            '<Notification name="Alarm" group_address="GroupAddress("1/2/3")" group_address_state="GroupAddress("1/2/4")" '
            'message="Einbrecher im Haus" />')

    def test_scene(self):
        """Test string representation of scene object."""
        xknx = XKNX(loop=self.loop)
        scene = Scene(
            xknx,
            name='Romantic',
            group_address='1/2/3',
            scene_number=23)
        self.assertEqual(
            str(scene),
            '<Scene name="Romantic" scene_value="GroupAddress("1/2/3")/None/None/None" scene_number="23" />')

    def test_sensor(self):
        """Test string representation of sensor object."""
        xknx = XKNX(loop=self.loop)
        sensor = Sensor(
            xknx,
            name='MeinSensor',
            group_address_state='1/2/3',
            value_type='percent')
        self.assertEqual(
            str(sensor),
            '<Sensor name="MeinSensor" sensor="None/GroupAddress("1/2/3")/None/None" value="None" unit="%"/>')
        # self.loop.run_until_complete(asyncio.Task(sensor.sensor_value.set(25)))
        telegram = Telegram(group_address=GroupAddress('1/2/3'),
                            direction=TelegramDirection.INCOMING,
                            payload=DPTArray((0x40)))
        self.loop.run_until_complete(asyncio.Task(sensor.process_group_write(telegram)))
        self.assertEqual(
            str(sensor),
            '<Sensor name="MeinSensor" sensor="None/GroupAddress("1/2/3")/<DPTArray value="[0x40]" />/25" value="25" unit="%"/>')

    def test_expose_sensor(self):
        """Test string representation of expose sensor object."""
        xknx = XKNX(loop=self.loop)
        sensor = ExposeSensor(
            xknx,
            name='MeinSensor',
            group_address='1/2/3',
            value_type='percent')
        self.assertEqual(
            str(sensor),
            '<ExposeSensor name="MeinSensor" sensor="GroupAddress("1/2/3")/None/None/None" value="None" unit="%"/>')
        self.loop.run_until_complete(asyncio.Task(sensor.set(25)))
        self.assertEqual(
            str(sensor),
            '<ExposeSensor name="MeinSensor" sensor="GroupAddress("1/2/3")/None/<DPTArray value="[0x40]" />/25" value="25" unit="%"/>')

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
            '<Switch name="Schalter" switch="GroupAddress("1/2/3")/GroupAddress("1/2/4")/None/None" />')

    def test_datetime(self):
        """Test string representation of datetime object."""
        xknx = XKNX(loop=self.loop)
        dateTime = DateTime(
            xknx,
            name="Zeit",
            group_address="1/2/3")
        self.assertEqual(
            str(dateTime),
            '<DateTime name="Zeit" group_address="GroupAddress("1/2/3")" broadcast_type="TIME" />')

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

    def test_could_not_parse_telegramn_exception_parameter(self):
        """Test string representation of CouldNotParseTelegram exception."""
        exception = CouldNotParseTelegram(description='Fnord', one="one", two="two")
        self.assertEqual(
            str(exception),
            '<CouldNotParseTelegram description="Fnord" one="one" two="two"/>')

    def test_could_not_parse_knxip_exception(self):
        """Test string representation of CouldNotParseKNXIP exception."""
        exception = CouldNotParseKNXIP(description='Fnord')
        self.assertEqual(
            str(exception),
            '<CouldNotParseKNXIP description="Fnord" />')

    def test_conversion_error_exception(self):
        """Test string representation of ConversionError exception."""
        exception = ConversionError(description='Fnord')
        self.assertEqual(
            str(exception),
            '<ConversionError description="Fnord" />')

    def test_conversion_error_exception_parameter(self):
        """Test string representation of ConversionError exception."""
        exception = ConversionError(description='Fnord', one="one", two="two")
        self.assertEqual(
            str(exception),
            '<ConversionError description="Fnord" one="one" two="two"/>')

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
        address = GroupAddress("1/2/3")
        self.assertEqual(
            repr(address),
            'GroupAddress("1/2/3")')
        self.assertEqual(
            str(address),
            '1/2/3')

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
            group_address=GroupAddress('1/2/3'),
            payload=DPTBinary(7))
        self.assertEqual(
            str(telegram),
            '<Telegram group_address="GroupAddress("1/2/3")", payload="<DPTBinary value="7" />" telegramtype="TelegramType.GROUP_WRITE" direction='
            '"TelegramDirection.OUTGOING" />')

    def test_dib_generic(self):
        """Test string representation of DIBGeneric."""
        dib = DIBGeneric()
        dib.dtc = 0x01
        dib.data = [0x02, 0x03, 0x04]
        self.assertEqual(
            str(dib),
            '<DIB dtc="1" data="0x02, 0x03, 0x04" />')

    def test_dib_supp_svc_families(self):
        """Test string representation of DIBSuppSVCFamilies."""
        dib = DIBSuppSVCFamilies()
        dib.families.append(DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, "1"))
        dib.families.append(DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, "2"))
        self.assertEqual(
            str(dib),
            '<DIBSuppSVCFamilies families="[DIBServiceFamily.CORE version: 1, DIBServiceFamily.DEVICE_MANAGEMENT version: 2]" />')

    def test_dib_device_informatio(self):
        """Test string representation of DIBDeviceInformation."""
        dib = DIBDeviceInformation()
        dib.knx_medium = KNXMedium.TP1
        dib.programming_mode = False
        dib.individual_address = PhysicalAddress('1.1.0')
        dib.name = 'Gira KNX/IP-Router'
        dib.mac_address = '00:01:02:03:04:05'
        dib.multicast_address = '224.0.23.12'
        dib.serial_number = '13:37:13:37:13:37'
        dib.project_number = 564
        dib.installation_number = 2
        self.assertEqual(
            str(dib),
            '<DIBDeviceInformation \n'
            '\tknx_medium="KNXMedium.TP1" \n'
            '\tprogramming_mode="False" \n'
            '\tindividual_address="PhysicalAddress("1.1.0")" \n'
            '\tinstallation_number="2" \n'
            '\tproject_number="564" \n'
            '\tserial_number="13:37:13:37:13:37" \n'
            '\tmulticast_address="224.0.23.12" \n'
            '\tmac_address="00:01:02:03:04:05" \n'
            '\tname="Gira KNX/IP-Router" />')

    def test_hpai(self):
        """Test string representation of HPAI."""
        hpai = HPAI(ip_addr='192.168.42.1', port=33941)
        self.assertEqual(
            str(hpai),
            '<HPAI 192.168.42.1:33941 />')

    def test_header(self):
        """Test string representation of KNX/IP-Header."""
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        header.total_length = 42
        self.assertEqual(
            str(header),
            '<KNXIPHeader HeaderLength="6" ProtocolVersion="16" KNXIPServiceType="KNXIPServiceType.ROUTING_INDICATION" Reserve="0" TotalLength="42" '
            '/>')

    def test_connect_request(self):
        """Test string representation of KNX/IP ConnectRequest."""
        xknx = XKNX(loop=self.loop)
        connect_request = ConnectRequest(xknx)
        connect_request.request_type = ConnectRequestType.TUNNEL_CONNECTION
        connect_request.control_endpoint = HPAI(ip_addr='192.168.42.1', port=33941)
        connect_request.data_endpoint = HPAI(ip_addr='192.168.42.2', port=33942)
        self.assertEqual(
            str(connect_request),
            '<ConnectRequest control_endpoint="<HPAI 192.168.42.1:33941 />" data_endpoint="<HPAI 192.168.42.2:33942 />" request_type="ConnectRequest'
            'Type.TUNNEL_CONNECTION" />')

    def test_connect_response(self):
        """Test string representatoin of KNX/IP ConnectResponse."""
        xknx = XKNX(loop=self.loop)
        connect_response = ConnectResponse(xknx)
        connect_response.communication_channel = 13
        connect_response.request_type = ConnectRequestType.TUNNEL_CONNECTION
        connect_response.control_endpoint = HPAI(ip_addr='192.168.42.1', port=33941)
        connect_response.identifier = 42
        self.assertEqual(
            str(connect_response),
            '<ConnectResponse communication_channel="13" status_code="ErrorCode.E_NO_ERROR" control_endpoint="<HPAI 192.168.42.1:33941 />" request_t'
            'ype="ConnectRequestType.TUNNEL_CONNECTION" identifier="42" />')

    def test_disconnect_request(self):
        """Test string representation of KNX/IP DisconnectRequest."""
        xknx = XKNX(loop=self.loop)
        disconnect_request = DisconnectRequest(xknx)
        disconnect_request.communication_channel_id = 13
        disconnect_request.control_endpoint = HPAI(ip_addr='192.168.42.1', port=33941)
        self.assertEqual(
            str(disconnect_request),
            '<DisconnectRequest CommunicationChannelID="13" control_endpoint="<HPAI 192.168.42.1:33941 />" />')

    def test_disconnect_response(self):
        """Test string representation of KNX/IP DisconnectResponse."""
        xknx = XKNX(loop=self.loop)
        disconnect_response = DisconnectResponse(xknx)
        disconnect_response.communication_channel_id = 23
        self.assertEqual(
            str(disconnect_response),
            '<DisconnectResponse CommunicationChannelID="23" status_code="ErrorCode.E_NO_ERROR" />')

    def test_connectionstate_request(self):
        """Test string representation of KNX/IP ConnectionStateRequest."""
        xknx = XKNX(loop=self.loop)
        connectionstate_request = ConnectionStateRequest(xknx)
        connectionstate_request.communication_channel_id = 23
        connectionstate_request.control_endpoint = HPAI(ip_addr='192.168.42.1', port=33941)
        self.assertEqual(
            str(connectionstate_request),
            '<ConnectionStateRequest CommunicationChannelID="23", control_endpoint="<HPAI 192.168.42.1:33941 />" />')

    def test_connectionstate_response(self):
        """Test string representation of KNX/IP ConnectionStateResponse."""
        xknx = XKNX(loop=self.loop)
        connectionstate_response = ConnectionStateResponse(xknx)
        connectionstate_response.communication_channel_id = 23
        self.assertEqual(
            str(connectionstate_response),
            '<ConnectionStateResponse CommunicationChannelID="23" status_code="ErrorCode.E_NO_ERROR" />')

    def test_search_reqeust(self):
        """Test string representation of KNX/IP SearchRequest."""
        xknx = XKNX(loop=self.loop)
        search_request = SearchRequest(xknx)
        self.assertEqual(
            str(search_request),
            '<SearchRequest discovery_endpoint="<HPAI 224.0.23.12:3671 />" />')

    def test_search_response(self):
        """Test string representation of KNX/IP SearchResponse."""
        xknx = XKNX(loop=self.loop)
        search_response = SearchResponse(xknx)
        search_response.control_endpoint = HPAI(ip_addr='192.168.42.1', port=33941)
        search_response.dibs.append(DIBGeneric())
        search_response.dibs.append(DIBGeneric())
        self.assertEqual(
            str(search_response),
            '<SearchResponse control_endpoint="<HPAI 192.168.42.1:33941 />" dibs="[\n'
            '<DIB dtc="None" data="" />,\n'
            '<DIB dtc="None" data="" />\n'
            ']" />')

    def test_tunnelling_request(self):
        """Test string representation of KNX/IP TunnellingRequest."""
        xknx = XKNX(loop=self.loop)
        tunnelling_request = TunnellingRequest(xknx)
        tunnelling_request.communication_channel_id = 23
        tunnelling_request.sequence_counter = 42
        self.assertEqual(
            str(tunnelling_request),
            '<TunnellingRequest communication_channel_id="23" sequence_counter="42" cemi="<CEMIFrame SourceAddress="GroupAddress("0/0/0")" Destina'
            'tionAddress="GroupAddress("0/0/0")" Flags="               0" Command="APCICommand.GROUP_READ" payload="None" />" />')

    def test_tunnelling_ack(self):
        """Test string representation of KNX/IP TunnellingAck."""
        xknx = XKNX(loop=self.loop)
        tunnelling_ack = TunnellingAck(xknx)
        tunnelling_ack.communication_channel_id = 23
        tunnelling_ack.sequence_counter = 42
        self.assertEqual(
            str(tunnelling_ack),
            '<TunnellingAck communication_channel_id="23" sequence_counter="42" status_code="ErrorCode.E_NO_ERROR" />')

    def test_cemi_frame(self):
        """Test string representation of KNX/IP CEMI Frame."""
        xknx = XKNX(loop=self.loop)
        cemi_frame = CEMIFrame(xknx)
        cemi_frame.src_addr = GroupAddress("1/2/3")
        cemi_frame.telegram = Telegram(
            group_address=GroupAddress('1/2/5'),
            payload=DPTBinary(7))
        self.assertEqual(
            str(cemi_frame),
            '<CEMIFrame SourceAddress="GroupAddress("1/2/3")" DestinationAddress="GroupAddress("1/2/5")" Flags="1011110011100000" Command="APCIC'
            'ommand.GROUP_WRITE" payload="<DPTBinary value="7" />" />')

    def test_knxip_frame(self):
        """Test string representation of KNX/IP Frame."""
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.init(KNXIPServiceType.SEARCH_REQUEST)
        self.assertEqual(
            str(knxipframe),
            '<KNXIPFrame <KNXIPHeader HeaderLength="6" ProtocolVersion="16" KNXIPServiceType="KNXIPServiceType.SEARCH_REQUEST" Reserve="0" TotalLeng'
            'th="0" />\n'
            ' body="<SearchRequest discovery_endpoint="<HPAI 224.0.23.12:3671 />" />" />')

    #
    # Gateway Scanner
    #
    def test_gateway_descriptor(self):
        """Test string representation of GatewayDescriptor."""
        gateway_descriptor = GatewayDescriptor(name='KNX-Interface',
                                               ip_addr='192.168.2.3',
                                               port=1234,
                                               local_interface='en1',
                                               local_ip='192.168.2.50',
                                               supports_tunnelling=True,
                                               supports_routing=False)
        self.assertEqual(
            str(gateway_descriptor),
            '<GatewayDescriptor name="KNX-Interface" addr="192.168.2.3:1234" local="192.168.2.50@en1" routing="False" tunnelling="True" />'
        )
