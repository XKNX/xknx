"""Unit test for String representations."""
from unittest.mock import patch

from xknx import XKNX
from xknx.cemi import (
    CEMIFrame,
    CEMILData,
    CEMIMessageCode,
    CEMIMPropInfo,
    CEMIMPropReadResponse,
)
from xknx.devices import (
    BinarySensor,
    Climate,
    ClimateMode,
    Cover,
    DateTime,
    ExposeSensor,
    Fan,
    Light,
    Notification,
    Scene,
    Sensor,
    Switch,
    Weather,
)
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import (
    ConversionError,
    CouldNotParseAddress,
    CouldNotParseKNXIP,
    CouldNotParseTelegram,
    DeviceIllegalValue,
    IncompleteKNXIPFrame,
)
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ConnectRequest,
    ConnectRequestType,
    ConnectResponse,
    ConnectResponseData,
    DIBDeviceInformation,
    DIBGeneric,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    DisconnectRequest,
    DisconnectResponse,
    HostProtocol,
    KNXIPFrame,
    KNXIPHeader,
    KNXMedium,
    RoutingIndication,
    SearchRequest,
    SearchResponse,
    SearchResponseExtended,
    TunnellingAck,
    TunnellingFeatureGet,
    TunnellingFeatureInfo,
    TunnellingFeatureResponse,
    TunnellingFeatureSet,
    TunnellingFeatureType,
    TunnellingRequest,
)
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType
from xknx.remote_value import RemoteValue
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite


class TestStringRepresentations:
    """Test class for Configuration logic."""

    @patch.multiple(RemoteValue, __abstractmethods__=set())
    def test_remote_value(self):
        """Test string representation of remote value."""
        xknx = XKNX()
        remote_value = RemoteValue(
            xknx,
            group_address="1/2/3",
            device_name="MyDevice",
            group_address_state="1/2/4",
        )
        assert (
            str(remote_value)
            == '<RemoteValue device_name="MyDevice" feature_name="Unknown" <1/2/3, 1/2/4, [], None /> />'
        )

        remote_value.value = 34
        assert (
            str(remote_value)
            == '<RemoteValue device_name="MyDevice" feature_name="Unknown" '
            "<1/2/3, 1/2/4, [], 34 /> />"
        )

        remote_value_passive = RemoteValue(
            xknx,
            group_address=["1/2/3", "1/2/4", "i-test"],
            device_name="MyDevice",
        )
        assert (
            str(remote_value_passive)
            == "<RemoteValue device_name=\"MyDevice\" feature_name=\"Unknown\" <1/2/3, None, ['1/2/4', 'i-test'], None /> />"
        )

    def test_binary_sensor(self):
        """Test string representation of binary sensor object."""
        xknx = XKNX()
        binary_sensor = BinarySensor(xknx, name="Fnord", group_address_state="1/2/3")
        assert (
            str(binary_sensor)
            == '<BinarySensor name="Fnord" remote_value=<None, 1/2/3, [], None /> state=None />'
        )

    def test_climate(self):
        """Test string representation of climate object."""
        xknx = XKNX()
        climate = Climate(
            xknx,
            name="Wohnzimmer",
            group_address_temperature="1/2/1",
            group_address_target_temperature="1/2/2",
            group_address_setpoint_shift="1/2/3",
            group_address_setpoint_shift_state="1/2/4",
            temperature_step=0.1,
            setpoint_shift_max=20,
            setpoint_shift_min=-20,
            group_address_on_off="1/2/14",
            group_address_on_off_state="1/2/15",
        )
        assert (
            str(climate) == '<Climate name="Wohnzimmer" '
            "temperature=<None, 1/2/1, [], None /> "
            "target_temperature=<1/2/2, None, [], None /> "
            'temperature_step="0.1" '
            "setpoint_shift=<1/2/3, 1/2/4, [], None /> "
            'setpoint_shift_max="20" setpoint_shift_min="-20" '
            "group_address_on_off=<1/2/14, 1/2/15, [], None /> />"
        )

    def test_climate_mode(self):
        """Test string representation of climate mode object."""
        xknx = XKNX()
        climate_mode = ClimateMode(
            xknx,
            name="Wohnzimmer Mode",
            group_address_operation_mode="1/2/5",
            group_address_operation_mode_state="1/2/6",
            group_address_operation_mode_protection="1/2/7",
            group_address_operation_mode_night="1/2/8",
            group_address_operation_mode_comfort="1/2/9",
            group_address_controller_status="1/2/10",
            group_address_controller_status_state="1/2/11",
            group_address_controller_mode="1/2/12",
            group_address_controller_mode_state="1/2/13",
        )
        assert (
            str(climate_mode) == '<ClimateMode name="Wohnzimmer Mode" '
            "operation_mode=<1/2/5, 1/2/6, [], None /> "
            "controller_mode=<1/2/12, 1/2/13, [], None /> "
            "controller_status=<1/2/10, 1/2/11, [], None /> />"
        )

    def test_cover(self):
        """Test string representation of cover object."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            name="Rolladen",
            group_address_long="1/2/2",
            group_address_short="1/2/3",
            group_address_stop="1/2/4",
            group_address_position="1/2/5",
            group_address_position_state="1/2/6",
            group_address_angle="1/2/7",
            group_address_angle_state="1/2/8",
            group_address_locked_state="1/2/9",
            travel_time_down=8,
            travel_time_up=10,
        )
        assert (
            str(cover) == '<Cover name="Rolladen" '
            "updown=<1/2/2, None, [], None /> "
            "step=<1/2/3, None, [], None /> "
            "stop_=<1/2/4, None, [], None /> "
            "position_current=<None, 1/2/6, [], None /> "
            "position_target=<1/2/5, None, [], None /> "
            "angle=<1/2/7, 1/2/8, [], None /> "
            "locked=<None, 1/2/9, [], None /> "
            'travel_time_down="8" '
            'travel_time_up="10" />'
        )

    def test_fan(self):
        """Test string representation of fan object."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="Dunstabzug",
            group_address_speed="1/2/3",
            group_address_speed_state="1/2/4",
            group_address_oscillation="1/2/5",
            group_address_oscillation_state="1/2/6",
        )
        assert (
            str(fan)
            == '<Fan name="Dunstabzug" speed=<1/2/3, 1/2/4, [], None /> oscillation=<1/2/5, 1/2/6, [], None /> />'
        )

    def test_light(self):
        """Test string representation of non dimmable light object."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="Licht",
            group_address_switch="1/2/3",
            group_address_switch_state="1/2/4",
        )
        assert str(light) == '<Light name="Licht" switch=<1/2/3, 1/2/4, [], None /> />'

    def test_light_dimmable(self):
        """Test string representation of dimmable light object."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="Licht",
            group_address_switch="1/2/3",
            group_address_switch_state="1/2/4",
            group_address_brightness="1/2/5",
            group_address_brightness_state="1/2/6",
        )
        assert (
            str(light) == '<Light name="Licht" '
            "switch=<1/2/3, 1/2/4, [], None /> "
            "brightness=<1/2/5, 1/2/6, [], None /> />"
        )

    def test_light_color(self):
        """Test string representation of dimmable light object."""
        xknx = XKNX()
        light = Light(
            xknx,
            name="Licht",
            group_address_switch="1/2/3",
            group_address_switch_state="1/2/4",
            group_address_color="1/2/5",
            group_address_color_state="1/2/6",
        )
        assert (
            str(light) == '<Light name="Licht" '
            "switch=<1/2/3, 1/2/4, [], None /> "
            "color=<1/2/5, 1/2/6, [], None /> />"
        )

    async def test_notification(self):
        """Test string representation of notification object."""
        xknx = XKNX()
        notification = Notification(
            xknx, name="Alarm", group_address="1/2/3", group_address_state="1/2/4"
        )
        assert (
            str(notification)
            == '<Notification name="Alarm" message=<1/2/3, 1/2/4, [], None /> />'
        )
        await notification.set("Einbrecher im Haus")
        await notification.process(xknx.telegrams.get_nowait())
        assert (
            str(notification) == '<Notification name="Alarm" '
            "message=<1/2/3, 1/2/4, [], 'Einbrecher im ' /> />"
        )

    def test_scene(self):
        """Test string representation of scene object."""
        xknx = XKNX()
        scene = Scene(xknx, name="Romantic", group_address="1/2/3", scene_number=23)
        assert (
            str(scene)
            == '<Scene name="Romantic" scene_value=<1/2/3, None, [], None /> scene_number="23" />'
        )

    async def test_sensor(self):
        """Test string representation of sensor object."""
        xknx = XKNX()
        sensor = Sensor(
            xknx, name="MeinSensor", group_address_state="1/2/3", value_type="percent"
        )
        assert (
            str(sensor)
            == '<Sensor name="MeinSensor" sensor=<None, 1/2/3, [], None /> value=None unit="%"/>'
        )
        # self.loop.run_until_complete(sensor.sensor_value.set(25))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTArray(0x40)),
        )
        await sensor.process_group_write(telegram)
        assert (
            str(sensor)
            == '<Sensor name="MeinSensor" sensor=<None, 1/2/3, [], 25 /> value=25 unit="%"/>'
        )

    async def test_expose_sensor(self):
        """Test string representation of expose sensor object."""
        xknx = XKNX()
        sensor = ExposeSensor(
            xknx, name="MeinSensor", group_address="1/2/3", value_type="percent"
        )
        assert (
            str(sensor)
            == '<ExposeSensor name="MeinSensor" sensor=<1/2/3, None, [], None /> value=None unit="%"/>'
        )
        await sensor.set(25)
        await sensor.process(xknx.telegrams.get_nowait())
        assert (
            str(sensor)
            == '<ExposeSensor name="MeinSensor" sensor=<1/2/3, None, [], 25 /> value=25 unit="%"/>'
        )

    def test_switch(self):
        """Test string representation of switch object."""
        xknx = XKNX()
        switch = Switch(
            xknx, name="Schalter", group_address="1/2/3", group_address_state="1/2/4"
        )
        assert (
            str(switch)
            == '<Switch name="Schalter" switch=<1/2/3, 1/2/4, [], None /> />'
        )

    async def test_weather(self):
        """Test string representation of switch object."""
        xknx = XKNX()
        weather = Weather(
            xknx,
            "Home",
            group_address_temperature="7/0/1",
            group_address_brightness_south="7/0/5",
            group_address_brightness_east="7/0/4",
            group_address_brightness_west="7/0/3",
            group_address_wind_speed="7/0/2",
            group_address_wind_bearing="7/0/6",
            group_address_day_night="7/0/7",
            group_address_rain_alarm="7/0/0",
            group_address_frost_alarm="7/0/8",
            group_address_air_pressure="7/0/9",
            group_address_humidity="7/0/9",
            group_address_wind_alarm="7/0/10",
        )
        assert (
            str(weather)
            == '<Weather name="Home" temperature=<None, 7/0/1, [], None /> '
            "brightness_south=<None, 7/0/5, [], None /> brightness_north=<None, None, [], None /> "
            "brightness_west=<None, 7/0/3, [], None /> "
            "brightness_east=<None, 7/0/4, [], None /> wind_speed=<None, 7/0/2, [], None /> "
            "wind_bearing=<None, 7/0/6, [], None /> rain_alarm=<None, 7/0/0, [], None /> "
            "wind_alarm=<None, 7/0/10, [], None /> frost_alarm=<None, 7/0/8, [], None /> "
            "day_night=<None, 7/0/7, [], None /> air_pressure=<None, 7/0/9, [], None /> "
            "humidity=<None, 7/0/9, [], None /> />"
        )

        telegram = Telegram(
            destination_address=GroupAddress("7/0/10"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await weather.process_group_write(telegram)

        assert (
            str(weather)
            == '<Weather name="Home" temperature=<None, 7/0/1, [], None /> '
            "brightness_south=<None, 7/0/5, [], None /> brightness_north=<None, None, [], None /> "
            "brightness_west=<None, 7/0/3, [], None /> "
            "brightness_east=<None, 7/0/4, [], None /> wind_speed=<None, 7/0/2, [], None /> "
            "wind_bearing=<None, 7/0/6, [], None /> rain_alarm=<None, 7/0/0, [], None /> "
            "wind_alarm=<None, 7/0/10, [], True /> "
            "frost_alarm=<None, 7/0/8, [], None /> day_night=<None, 7/0/7, [], None /> "
            "air_pressure=<None, 7/0/9, [], None /> humidity=<None, 7/0/9, [], None /> />"
        )

    def test_datetime(self):
        """Test string representation of datetime object."""
        xknx = XKNX()
        date_time = DateTime(xknx, name="Zeit", group_address="1/2/3", localtime=False)
        assert (
            str(date_time)
            == '<DateTime name="Zeit" remote_value=<1/2/3, None, [], None /> broadcast_type="TIME" />'
        )

    def test_could_not_parse_telegramn_exception(self):
        """Test string representation of CouldNotParseTelegram exception."""
        exception = CouldNotParseTelegram(description="Fnord")
        assert str(exception) == '<CouldNotParseTelegram description="Fnord" />'

    def test_could_not_parse_telegramn_exception_parameter(self):
        """Test string representation of CouldNotParseTelegram exception."""
        exception = CouldNotParseTelegram(description="Fnord", one="one", two="two")
        assert (
            str(exception)
            == '<CouldNotParseTelegram description="Fnord" one="one" two="two"/>'
        )

    def test_could_not_parse_knxip_exception(self):
        """Test string representation of CouldNotParseKNXIP exception."""
        exception = CouldNotParseKNXIP(description="Fnord")
        assert str(exception) == '<CouldNotParseKNXIP description="Fnord" />'

    def test_conversion_error_exception(self):
        """Test string representation of ConversionError exception."""
        exception = ConversionError(description="Fnord")
        assert str(exception) == '<ConversionError description="Fnord" />'

    def test_conversion_error_exception_parameter(self):
        """Test string representation of ConversionError exception."""
        exception = ConversionError(description="Fnord", one="one", two="two")
        assert (
            str(exception)
            == '<ConversionError description="Fnord" one="one" two="two"/>'
        )

    def test_could_not_parse_address_exception(self):
        """Test string representation of CouldNotParseAddress exception."""
        exception = CouldNotParseAddress(address="1/2/1000")
        assert str(exception) == '<CouldNotParseAddress address="1/2/1000" />'

    def test_device_illegal_value_exception(self):
        """Test string representation of DeviceIllegalValue exception."""
        exception = DeviceIllegalValue(value=12, description="Fnord exceeded")
        assert (
            str(exception)
            == '<DeviceIllegalValue description="12" value="Fnord exceeded" />'
        )

    def test_incomplete_knxip_frame_excetpion(self):
        """Test string representation of IncompleteKNXIPFrame exception."""
        exception = IncompleteKNXIPFrame("Hello")
        assert str(exception) == '<IncompleteKNXIPFrame description="Hello" />'

    def test_address(self):
        """Test string representation of address object."""
        address = GroupAddress("1/2/3")
        assert repr(address) == 'GroupAddress("1/2/3")'
        assert str(address) == "1/2/3"

    def test_dpt_array(self):
        """Test string representation of DPTBinary."""
        dpt_array = DPTArray([0x01, 0x02])
        assert str(dpt_array) == '<DPTArray value="[0x1,0x2]" />'

    def test_dpt_binary(self):
        """Test string representation of DPTBinary."""
        dpt_binary = DPTBinary(7)
        assert str(dpt_binary) == '<DPTBinary value="7" />'

    def test_telegram(self):
        """Test string representation of Telegram."""
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(7)),
        )
        assert (
            str(telegram) == '<Telegram direction="Outgoing" source_address="0.0.0" '
            'destination_address="1/2/3" payload="<GroupValueWrite value="<DPTBinary value="7" />" />" />'
        )

    def test_dib_generic(self):
        """Test string representation of DIBGeneric."""
        dib = DIBGeneric()
        dib.dtc = 0x01
        dib.data = [0x02, 0x03, 0x04]
        assert str(dib) == '<DIB dtc="1" data="0x02, 0x03, 0x04" />'

    def test_dib_supp_svc_families(self):
        """Test string representation of DIBSuppSVCFamilies."""
        dib = DIBSuppSVCFamilies()
        dib.families.append(DIBSuppSVCFamilies.Family(DIBServiceFamily.CORE, "1"))
        dib.families.append(
            DIBSuppSVCFamilies.Family(DIBServiceFamily.DEVICE_MANAGEMENT, "2")
        )
        assert (
            str(dib)
            == '<DIBSuppSVCFamilies families="[DIBServiceFamily.CORE version: 1, DIBServiceFamily.DEVICE_MANAGEMENT version: 2]" />'
        )

    def test_dib_device_informatio(self):
        """Test string representation of DIBDeviceInformation."""
        dib = DIBDeviceInformation()
        dib.knx_medium = KNXMedium.TP1
        dib.programming_mode = False
        dib.individual_address = IndividualAddress("1.1.0")
        dib.name = "Gira KNX/IP-Router"
        dib.mac_address = "00:01:02:03:04:05"
        dib.multicast_address = "224.0.23.12"
        dib.serial_number = "13:37:13:37:13:37"
        dib.project_number = 564
        dib.installation_number = 2
        assert (
            str(dib) == "<DIBDeviceInformation \n"
            '\tknx_medium="KNXMedium.TP1" \n'
            '\tprogramming_mode="False" \n'
            '\tindividual_address="1.1.0" \n'
            '\tinstallation_number="2" \n'
            '\tproject_number="564" \n'
            '\tserial_number="13:37:13:37:13:37" \n'
            '\tmulticast_address="224.0.23.12" \n'
            '\tmac_address="00:01:02:03:04:05" \n'
            '\tname="Gira KNX/IP-Router" />'
        )

    def test_hpai(self):
        """Test string representation of HPAI."""
        hpai_udp = HPAI(ip_addr="192.168.42.1", port=33941)
        assert str(hpai_udp) == "192.168.42.1:33941/udp"
        assert repr(hpai_udp) == "HPAI('192.168.42.1', 33941, HostProtocol.IPV4_UDP)"

        hpai_tcp = HPAI(ip_addr="10.1.4.1", port=3671, protocol=HostProtocol.IPV4_TCP)
        assert str(hpai_tcp) == "10.1.4.1:3671/tcp"
        assert repr(hpai_tcp) == "HPAI('10.1.4.1', 3671, HostProtocol.IPV4_TCP)"

    def test_header(self):
        """Test string representation of KNX/IP-Header."""
        header = KNXIPHeader()
        header.total_length = 42
        assert (
            str(header)
            == '<KNXIPHeader HeaderLength="6" ProtocolVersion="16" KNXIPServiceType="ROUTING_INDICATION" TotalLength="42" '
            "/>"
        )

    def test_connect_request(self):
        """Test string representation of KNX/IP ConnectRequest."""
        connect_request = ConnectRequest()
        connect_request.request_type = ConnectRequestType.TUNNEL_CONNECTION
        connect_request.control_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        connect_request.data_endpoint = HPAI(ip_addr="192.168.42.2", port=33942)
        assert (
            str(connect_request)
            == '<ConnectRequest control_endpoint="192.168.42.1:33941/udp" data_endpoint="192.168.42.2:33942/udp" '
            'cri="<ConnectRequestInformation connection_type="TUNNEL_CONNECTION" knx_layer="DATA_LINK_LAYER" />" />'
        )

    def test_connect_response(self):
        """Test string representatoin of KNX/IP ConnectResponse."""
        connect_response = ConnectResponse()
        connect_response.communication_channel = 13
        connect_response.data_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        connect_response.crd = ConnectResponseData(
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            individual_address=IndividualAddress("1.2.3"),
        )
        assert (
            str(connect_response)
            == '<ConnectResponse communication_channel="13" status_code="ErrorCode.E_NO_ERROR" '
            'data_endpoint="192.168.42.1:33941/udp" '
            'crd="<ConnectResponseData request_type="ConnectRequestType.TUNNEL_CONNECTION" individual_address="1.2.3" />" />'
        )

    def test_disconnect_request(self):
        """Test string representation of KNX/IP DisconnectRequest."""
        disconnect_request = DisconnectRequest()
        disconnect_request.communication_channel_id = 13
        disconnect_request.control_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        assert (
            str(disconnect_request)
            == '<DisconnectRequest communication_channel_id="13" control_endpoint="192.168.42.1:33941/udp" />'
        )

    def test_disconnect_response(self):
        """Test string representation of KNX/IP DisconnectResponse."""
        disconnect_response = DisconnectResponse()
        disconnect_response.communication_channel_id = 23
        assert (
            str(disconnect_response)
            == '<DisconnectResponse communication_channel_id="23" status_code="ErrorCode.E_NO_ERROR" />'
        )

    def test_connectionstate_request(self):
        """Test string representation of KNX/IP ConnectionStateRequest."""
        connectionstate_request = ConnectionStateRequest()
        connectionstate_request.communication_channel_id = 23
        connectionstate_request.control_endpoint = HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert (
            str(connectionstate_request)
            == '<ConnectionStateRequest communication_channel_id="23", control_endpoint="192.168.42.1:33941/udp" />'
        )

    def test_connectionstate_response(self):
        """Test string representation of KNX/IP ConnectionStateResponse."""
        connectionstate_response = ConnectionStateResponse()
        connectionstate_response.communication_channel_id = 23
        assert (
            str(connectionstate_response)
            == '<ConnectionStateResponse communication_channel_id="23" status_code="ErrorCode.E_NO_ERROR" />'
        )

    def test_search_reqeust(self):
        """Test string representation of KNX/IP SearchRequest."""
        search_request = SearchRequest()
        assert (
            str(search_request)
            == '<SearchRequest discovery_endpoint="0.0.0.0:0/udp" />'
        )

    def test_search_response(self):
        """Test string representation of KNX/IP SearchResponse."""
        search_response = SearchResponse()
        search_response.control_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        search_response.dibs.append(DIBGeneric())
        search_response.dibs.append(DIBGeneric())
        assert (
            str(search_response)
            == '<SearchResponse control_endpoint="192.168.42.1:33941/udp" dibs="[\n'
            '<DIB dtc="0" data="" />,\n'
            '<DIB dtc="0" data="" />\n'
            ']" />'
        )

    def test_search_response_extended(self):
        """Test string representation of KNX/IP SearchResponseExtended."""
        search_response = SearchResponseExtended()
        search_response.control_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        search_response.dibs.append(DIBGeneric())
        search_response.dibs.append(DIBGeneric())
        assert (
            str(search_response)
            == '<SearchResponseExtended control_endpoint="192.168.42.1:33941/udp" dibs="[\n'
            '<DIB dtc="0" data="" />,\n'
            '<DIB dtc="0" data="" />\n'
            ']" />'
        )

    def test_tunnelling_request(self):
        """Test string representation of KNX/IP TunnellingRequest."""
        tunnelling_request = TunnellingRequest()
        tunnelling_request.communication_channel_id = 23
        tunnelling_request.sequence_counter = 42
        assert (
            str(tunnelling_request)
            == '<TunnellingRequest communication_channel_id="23" sequence_counter="42" cemi="" />'
        )

    def test_tunnelling_ack(self):
        """Test string representation of KNX/IP TunnellingAck."""
        tunnelling_ack = TunnellingAck()
        tunnelling_ack.communication_channel_id = 23
        tunnelling_ack.sequence_counter = 42
        assert (
            str(tunnelling_ack)
            == '<TunnellingAck communication_channel_id="23" sequence_counter="42" status_code="ErrorCode.E_NO_ERROR" />'
        )

    def test_tunnelling_feature_get(self):
        """Test string representation of KNX/IP TunnellingFeatureGet."""
        tunnelling_feature = TunnellingFeatureGet()
        tunnelling_feature.communication_channel_id = 23
        tunnelling_feature.sequence_counter = 42
        tunnelling_feature.feature_type = TunnellingFeatureType.BUS_CONNECTION_STATUS
        assert (
            str(tunnelling_feature)
            == '<TunnellingFeatureGet communication_channel_id="23" sequence_counter="42" '
            'feature_type="TunnellingFeatureType.BUS_CONNECTION_STATUS" />'
        )

    def test_tunnelling_feature_info(self):
        """Test string representation of KNX/IP TunnellingFeatureInfo."""
        tunnelling_feature = TunnellingFeatureInfo()
        tunnelling_feature.communication_channel_id = 23
        tunnelling_feature.sequence_counter = 42
        tunnelling_feature.feature_type = TunnellingFeatureType.BUS_CONNECTION_STATUS
        tunnelling_feature.data = b"\x01\x00"
        assert (
            str(tunnelling_feature)
            == '<TunnellingFeatureInfo communication_channel_id="23" sequence_counter="42" '
            'feature_type="TunnellingFeatureType.BUS_CONNECTION_STATUS" data="0100" />'
        )

    def test_tunnelling_feature_response(self):
        """Test string representation of KNX/IP TunnellingFeatureResponse."""
        tunnelling_feature = TunnellingFeatureResponse()
        tunnelling_feature.communication_channel_id = 23
        tunnelling_feature.sequence_counter = 42
        tunnelling_feature.feature_type = TunnellingFeatureType.BUS_CONNECTION_STATUS
        tunnelling_feature.data = b"\x01\x00"
        assert (
            str(tunnelling_feature)
            == '<TunnellingFeatureResponse communication_channel_id="23" sequence_counter="42" status_code="ErrorCode.E_NO_ERROR" '
            'feature_type="TunnellingFeatureType.BUS_CONNECTION_STATUS" data="0100" />'
        )

    def test_tunnelling_feature_set(self):
        """Test string representation of KNX/IP TunnellingFeatureSet."""
        tunnelling_feature = TunnellingFeatureSet()
        tunnelling_feature.communication_channel_id = 23
        tunnelling_feature.sequence_counter = 42
        tunnelling_feature.feature_type = (
            TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE
        )
        tunnelling_feature.data = b"\x01\x00"
        assert (
            str(tunnelling_feature)
            == '<TunnellingFeatureSet communication_channel_id="23" sequence_counter="42" '
            'feature_type="TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE" data="0100" />'
        )

    def test_cemi_ldata_frame(self):
        """Test string representation of KNX/IP CEMI Frame."""
        cemi_frame = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                telegram=Telegram(
                    destination_address=GroupAddress("1/2/5"),
                    payload=GroupValueWrite(DPTBinary(7)),
                ),
                src_addr=IndividualAddress("1.2.3"),
            ),
        )
        assert (
            str(cemi_frame)
            == '<CEMIFrame code="L_DATA_IND" info="CEMIInfo("")" data="CEMILData(src_addr="IndividualAddress("1.2.3")" '
            'dst_addr="GroupAddress("1/2/5")" flags="1011110011100000" tpci="TDataGroup()" '
            'payload="<GroupValueWrite value="<DPTBinary value="7" />" />")" />'
        )

    def test_cemi_mprop_frame(self):
        """Test string representation of KNX/IP CEMI Frame."""
        cemi_frame = CEMIFrame(
            code=CEMIMessageCode.M_PROP_READ_REQ,
            data=CEMIMPropReadResponse(
                property_info=CEMIMPropInfo(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS,
                ),
                data=IndividualAddress("1.2.3").to_knx(),
            ),
        )
        assert (
            str(cemi_frame)
            == '<CEMIFrame code="M_PROP_READ_REQ" data="CEMIMPropReadResponse(object_type="11" object_instance="1" '
            'property_id="52" number_of_elements="1" start_index="1" error_code="None" data="1203" )" />'
        )

    def test_knxip_frame(self):
        """Test string representation of KNX/IP Frame."""
        search_request = SearchRequest()
        knxipframe = KNXIPFrame.init_from_body(search_request)
        assert (
            str(knxipframe)
            == '<KNXIPFrame <KNXIPHeader HeaderLength="6" ProtocolVersion="16" KNXIPServiceType="SEARCH_REQUEST" '
            'TotalLength="14" /> body="<SearchRequest discovery_endpoint="0.0.0.0:0/udp" />" />'
        )

    #
    # Gateway Scanner
    #
    def test_gateway_descriptor(self):
        """Test string representation of GatewayDescriptor."""
        gateway_descriptor = GatewayDescriptor(
            name="KNX-Interface",
            ip_addr="192.168.2.3",
            port=1234,
            local_interface="en1",
            local_ip="192.168.2.50",
            supports_tunnelling=True,
            supports_routing=False,
            individual_address=IndividualAddress("1.1.1"),
        )
        assert str(gateway_descriptor) == "1.1.1 - KNX-Interface @ 192.168.2.3:1234"

    #
    # Routing Indication
    #
    def test_routing_indication_str(self):
        """Test string representation of GatewayDescriptor."""
        routing_indication = RoutingIndication()
        assert str(routing_indication) == '<RoutingIndication cemi="" />'
