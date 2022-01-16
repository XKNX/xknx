local p_knx = Proto("usbhid.knx", "KNX HID Data");

local vs_sequence_number = {
	[0] = "reserved; shall not be used",
	[1] = "1st packet (start packet)",
	[2] = "2nd packet",
	[3] = "3rd packet",
	[4] = "4th packet",
	[5] = "5th packet",
}

local vs_packet_type = {
	[0] = "reserved / not allowed",
	[3] = "(0011b) start & end packet (1st and last packet in one)",
	[4] = "(0100b) partial packet (not start & not end packet)",
	[5] = "(0101b) start & partial packet",
	[6] = "(0110b) partial & end packet",
}

local vs_service_id = {
	[0x00] = "reserved, not used",
	[0x01] = "Device Feature Get",
	[0x02] = "Device Feature Response",
	[0x03] = "Device Feature Set",
	[0x04] = "Device Feature Info",
	[0xEF] = "reserved, not used",
	[0xFF] = "reserved (ESCAPE for future extension)",
}

local vs_emi_type_support = {
	[0x00] = "EMI Type not supported",
	[0x01] = "EMI Type is supported",
}

local vs_service_feature_id = {
	[0x01] = "Supported EMI type - Getting the supported EMI type(s) - 2 octets (B16)",
	[0x02] = "Host Device Device Descriptor Type 0 - Getting the local Device Descriptor Type 0 for possible local device management. - 2 octets (U4U4U4U4)",
	[0x03] = "Bus connection status - Getting and informing on the bus connection status. - 1 bit (B1)",
	[0x04] = "KNX Manufacturer Code - Getting the manufacturer code of the Bus Access Server. - 2 octets (U16)",
	[0x05] = "Active EMI type - Getting and Setting the EMI type to use. - 1 octet (N8)",
}

local vs_protocol_id = {
	[0] = "Reserved",
	[1] = "KNX Tunnel",
	[2] = "M-Bus Tunnel (Metering-Bus, acc. to CEN TC294)",
	[3] = "BatiBus Tunnel",
	[15] = "Bus Access Server Feature Service",  -- 0x0F
	[239] = "Reserved",  -- 0xEF
	[255] = "Reserved",  -- 0xFF
}

local vs_emi_id = {
	[0] = "Reserved",
	[1] = "EMI1",
	[2] = "EMI2",
	[3] = "common EMI",
	[4] = "not used",
	[5] = "not used",
	[239] = "not used",  -- 0xEF
	[255] = "reserved (ESCAPE for future extensions)",  -- 0xFF
}

local vs_emi1_message_code = {
	-- [0x] = "Ph_Data.req",
	-- [0x] = "Ph_Data.con",
	-- [0x] = "Ph_Data.ind",
	[0x49] = "L_Busmon.ind",
	[0x11] = "L_Data.req",
	[0x4E] = "L_Data.con",
	[0x49] = "L_Data.ind",
	[0x15] = "L_SystemBroadcast.req",
	[0x4C] = "L_SystemBroadcast.con",
	[0x4D] = "L_SystemBroadcast.ind",
	-- [0x] = "L_Plain_Data.req",
	-- [0x] = "L_Raw.req",
	-- [0x] = "L_Raw.ind",
	-- [0x] = "L_Raw.con",
	-- [0x] = "L_Poll_Data.req",
	-- [0x] = "L_Poll_Data.con",
	-- [0x] = "L_Meter.ind",
	-- [0x] = "N_Data_Individual.req",
	-- [0x] = "N_Data_Individual.con",
	-- [0x] = "N_Data_Individual.ind",
	-- [0x] = "N_Data_Group.req",
	-- [0x] = "N_Data_Group.con",
	-- [0x] = "N_Data_Group.ind",
	-- [0x] = "N_Data_Broadcast.req",
	-- [0x] = "N_Data_Broadcast.con",
	-- [0x] = "N_Data_Broadcast.ind",
	-- [0x] = "N_Poll_Data.req",
	-- [0x] = "N_Poll_Data.con",
	[0x23] = "T_Connect.req",
	-- [0x] = "T_Connect.con",
	[0x43] = "T_Connect.ind",
	[0x24] = "T_Disconnect.req",
	-- [0x] = "T_Disconnect.con",
	[0x44] = "T_Disconnect.ind",
	[0x21] = "T_Data_Connected.req",
	-- [0x] = "T_Data_Connected.con",
	[0x49] = "T_Data_Connected.ind",
	[0x22] = "T_Data_Group.req",
	[0x4E] = "T_Data_Group.con",
	[0x4A] = "T_Data_Group.ind",
	[0x2B] = "T_Data_Broadcast.req",
	-- [0x] = "T_Data_Broadcast.con",
	[0x48] = "T_Data_Broadcast.ind",
	[0x25] = "T_Data_SystemBroadcast.req",
	[0x4C] = "T_Data_SystemBroadcast.con",
	[0x4D] = "T_Data_SystemBroadcast.ind",
	[0x2A] = "T_Data_Individual.req",
	[0x4F] = "T_Data_Individual.con",
	[0x42] = "T_Data_Individual.ind",
	-- [0x] = "T_Poll_Data.req",
	-- [0x] = "T_Poll_Data.con",
	-- [0x] = "M_Connect.req",
	-- [0x] = "M_Connect.con",
	-- [0x] = "M_Connect.ind",
	-- [0x] = "M_Disconnect.req",
	-- [0x] = "M_Disconnect.con",
	-- [0x] = "M_Disconnect.ind",
	[0x31] = "M_User_Data_Connected.req",
	-- [0x] = "M_User_Data_Connected.con",
	[0x49] = "M_User_Data_Connected.ind",
	-- [0x] = "A_Data_Group.req",
	-- [0x] = "A_Data_Group.con",
	-- [0x] = "A_Data_Group.ind",
	-- [0x] = "M_User_Data_Individual.req",
	-- [0x] = "M_User_Data_Individual.con",
	-- [0x] = "M_User_Data_Individual.ind",
	-- [0x] = "A_Poll_Data.req",
	-- [0x] = "A_Poll_Data.con",
	-- [0x] = "M_InterfaceObj_Data.req",
	-- [0x] = "M_InterfaceObj_Data.con",
	-- [0x] = "M_InterfaceObj_Data.ind",
	[0x35] = "U_Value_Read.req",
	[0x45] = "U_Value_Read.con",
	[0x37] = "U_Flags_Read.req",
	[0x47] = "U_Flags_Read.con",
	[0x4D] = "U_Event.ind",
	[0x36] = "U_Value_Write.req",
	-- [0x] = "U_User_Data",
	[0x46] = "PC_Set_Value.req",
	[0x46] = "PC_Get_Value.req",
	[0x4B] = "PC_Get_Value.con",
	-- [0x] = "PEI_Identify.req",
	-- [0x] = "PEI_Identify.con",
	-- [0x] = "PEI_Switch.req",
	-- [0x] = "TM_Timer.ind",
	-- [0x] = "M_PropRead.req",
	-- [0x] = "M_PropRead.con",
	-- [0x] = "M_PropWrite.req",
	-- [0x] = "M_PropWrite.con",
	-- [0x] = "M_PropInfo.ind",
	-- [0x] = "M_FuncPropCommand.req",
	-- [0x] = "M_FuncPropStateRead.req",
	-- [0x] = "M_FuncPropCommand.con",
	-- [0x] = "M_FuncPropStateread.con",
	-- [0x] = "M_Reset.req",
	-- [0x] = "M_Reset.ind"
}

local vs_emi2_message_code = {
	[0x01] = "Ph_Data.req",
	[0x1E] = "Ph_Data.con",
	[0x19] = "Ph_Data.ind",
	[0x2B] = "L_Busmon.ind",
	[0x11] = "L_Data.req",
	[0x2E] = "L_Data.con",
	[0x29] = "L_Data.ind",
	[0x17] = "L_SystemBroadcast.req",
	[0x26] = "L_SystemBroadcast.con",
	[0x28] = "L_SystemBroadcast.ind",
	[0x10] = "L_Plain_Data.req",
	-- [0x] = "L_Raw.req",
	-- [0x] = "L_Raw.ind",
	-- [0x] = "L_Raw.con",
	[0x13] = "L_Poll_Data.req",
	[0x25] = "L_Poll_Data.con",
	[0x24] = "L_Meter.ind",
	[0x21] = "N_Data_Individual.req",
	[0x4E] = "N_Data_Individual.con",
	[0x49] = "N_Data_Individual.ind",
	[0x22] = "N_Data_Group.req",
	[0x3E] = "N_Data_Group.con",
	[0x3A] = "N_Data_Group.ind",
	[0x2C] = "N_Data_Broadcast.req",
	[0x4F] = "N_Data_Broadcast.con",
	[0x4D] = "N_Data_Broadcast.ind",
	[0x23] = "N_Poll_Data.req",
	[0x35] = "N_Poll_Data.con",
	[0x43] = "T_Connect.req",
	[0x86] = "T_Connect.con",
	[0x85] = "T_Connect.ind",
	[0x44] = "T_Disconnect.req",
	[0x88] = "T_Disconnect.con",
	[0x87] = "T_Disconnect.ind",
	[0x41] = "T_Data_Connected.req",
	[0x8E] = "T_Data_Connected.con",
	[0x89] = "T_Data_Connected.ind",
	[0x32] = "T_Data_Group.req",
	[0x7E] = "T_Data_Group.con",
	[0x7A] = "T_Data_Group.ind",
	[0x4C] = "T_Data_Broadcast.req",
	[0x8F] = "T_Data_Broadcast.con",
	[0x8D] = "T_Data_Broadcast.ind",
	-- [0x] = "T_Data_SystemBroadcast.req",
	-- [0x] = "T_Data_SystemBroadcast.con",
	-- [0x] = "T_Data_SystemBroadcast.ind",
	[0x4A] = "T_Data_Individual.req",
	[0x9C] = "T_Data_Individual.con",
	[0x94] = "T_Data_Individual.ind",
	[0x33] = "T_Poll_Data.req",
	[0x75] = "T_Poll_Data.con",
	-- [0x] = "M_Connect.req",
	-- [0x] = "M_Connect.con",
	[0xD5] = "M_Connect.ind",
	-- [0x] = "M_Disconnect.req",
	-- [0x] = "M_Disconnect.con",
	[0xD7] = "M_Disconnect.ind",
	[0x82] = "M_User_Data_Connected.req",
	[0xD1] = "M_User_Data_Connected.con",
	[0xD2] = "M_User_Data_Connected.ind",
	[0x72] = "A_Data_Group.req",
	[0xEE] = "A_Data_Group.con",
	[0xEA] = "A_Data_Group.ind",
	[0x81] = "M_User_Data_Individual.req",
	[0xDE] = "M_User_Data_Individual.con",
	[0xD9] = "M_User_Data_Individual.ind",
	[0x73] = "A_Poll_Data.req",
	[0xE5] = "A_Poll_Data.con",
	[0x9A] = "M_InterfaceObj_Data.req",
	[0xDC] = "M_InterfaceObj_Data.con",
	[0xD4] = "M_InterfaceObj_Data.ind",
	[0x74] = "U_Value_Read.req",
	[0xE4] = "U_Value_Read.con",
	[0x7C] = "U_Flags_Read.req",
	[0xEC] = "U_Flags_Read.con",
	[0xE7] = "U_Event.ind",
	[0x71] = "U_Value_Write.req",
	[0xD0] = "U_User_Data",
	[0xA6] = "PC_Set_Value.req",
	[0xAC] = "PC_Get_Value.req",
	[0xAB] = "PC_Get_Value.con",
	[0xA7] = "PEI_Identify.req",
	[0xA8] = "PEI_Identify.con",
	[0xA9] = "PEI_Switch.req",
	[0xC1] = "TM_Timer.ind",
	-- [0x] = "M_PropRead.req",
	-- [0x] = "M_PropRead.con",
	-- [0x] = "M_PropWrite.req",
	-- [0x] = "M_PropWrite.con",
	-- [0x] = "M_PropInfo.ind",
	-- [0x] = "M_FuncPropCommand.req",
	-- [0x] = "M_FuncPropStateRead.req",
	-- [0x] = "M_FuncPropCommand.con",
	-- [0x] = "M_FuncPropStateread.con",
	-- [0x] = "M_Reset.req",
	-- [0x] = "M_Reset.ind"
}

-- 4.1.3.2 Overview of the cEMI Message Codes
-- The codes for the Data Link Layer messages shall be the same as used for EMI 2. Please refer to Table 1
-- for the overview of the EMI message codes and the message code set supported by cEMI.
-- NOTE Codes for cEMI Transport Layer services are not yet listed in Table 1. If needed later (if the cEMI specification is 
-- extended with the corresponding definitions in clause 4.1.6, “Transport Layer messages”), the same codes as defined for EMI 2 
-- shall be used for the Transport Layer services.
local vs_cemi_message_code = {
	-- [0x] = "Ph_Data.req",
	-- [0x] = "Ph_Data.con",
	-- [0x] = "Ph_Data.ind",
	[0x2B] = "L_Busmon.ind",
	[0x11] = "L_Data.req",
	[0x2E] = "L_Data.con",
	[0x29] = "L_Data.ind",
	-- [0x] = "L_SystemBroadcast.req",
	-- [0x] = "L_SystemBroadcast.con",
	-- [0x] = "L_SystemBroadcast.ind",
	-- [0x] = "L_Plain_Data.req",
	[0x10] = "L_Raw.req",
	[0x2D] = "L_Raw.ind",
	[0x2F] = "L_Raw.con",
	[0x13] = "L_Poll_Data.req",
	[0x25] = "L_Poll_Data.con",
	-- [0x] = "L_Meter.ind",
	-- [0x] = "N_Data_Individual.req",
	-- [0x] = "N_Data_Individual.con",
	-- [0x] = "N_Data_Individual.ind",
	-- [0x] = "N_Data_Group.req",
	-- [0x] = "N_Data_Group.con",
	-- [0x] = "N_Data_Group.ind",
	-- [0x] = "N_Data_Broadcast.req",
	-- [0x] = "N_Data_Broadcast.con",
	-- [0x] = "N_Data_Broadcast.ind",
	-- [0x] = "N_Poll_Data.req",
	-- [0x] = "N_Poll_Data.con",
	[0x43] = "T_Connect.req",
	[0x86] = "T_Connect.con",
	[0x85] = "T_Connect.ind",
	[0x44] = "T_Disconnect.req",
	[0x88] = "T_Disconnect.con",
	[0x87] = "T_Disconnect.ind",
	[0x41] = "T_Data_Connected.req",
	[0x8E] = "T_Data_Connected.con",
	[0x89] = "T_Data_Connected.ind",
	[0x32] = "T_Data_Group.req",
	[0x7E] = "T_Data_Group.con",
	[0x7A] = "T_Data_Group.ind",
	[0x4C] = "T_Data_Broadcast.req",
	[0x8F] = "T_Data_Broadcast.con",
	[0x8D] = "T_Data_Broadcast.ind",
	-- [0x] = "T_Data_SystemBroadcast.req",
	-- [0x] = "T_Data_SystemBroadcast.con",
	-- [0x] = "T_Data_SystemBroadcast.ind",
	[0x4A] = "T_Data_Individual.req",
	-- [0x] = "T_Data_Individual.con",
	[0x94] = "T_Data_Individual.ind",
	[0x33] = "T_Poll_Data.req",
	[0x75] = "T_Poll_Data.con",
	-- [0x] = "M_Connect.req",
	-- [0x] = "M_Connect.con",
	-- [0x] = "M_Connect.ind",
	-- [0x] = "M_Disconnect.req",
	-- [0x] = "M_Disconnect.con",
	-- [0x] = "M_Disconnect.ind",
	-- [0x] = "M_User_Data_Connected.req",
	-- [0x] = "M_User_Data_Connected.con",
	-- [0x] = "M_User_Data_Connected.ind",
	-- [0x] = "A_Data_Group.req",
	-- [0x] = "A_Data_Group.con",
	-- [0x] = "A_Data_Group.ind",
	-- [0x] = "M_User_Data_Individual.req",
	-- [0x] = "M_User_Data_Individual.con",
	-- [0x] = "M_User_Data_Individual.ind",
	-- [0x] = "A_Poll_Data.req",
	-- [0x] = "A_Poll_Data.con",
	-- [0x] = "M_InterfaceObj_Data.req",
	-- [0x] = "M_InterfaceObj_Data.con",
	-- [0x] = "M_InterfaceObj_Data.ind",
	-- [0x] = "U_Value_Read.req",
	-- [0x] = "U_Value_Read.con",
	-- [0x] = "U_Flags_Read.req",
	-- [0x] = "U_Flags_Read.con",
	-- [0x] = "U_Event.ind",
	-- [0x] = "U_Value_Write.req",
	-- [0x] = "U_User_Data",
	-- [0x] = "PC_Set_Value.req",
	-- [0x] = "PC_Get_Value.req",
	-- [0x] = "PC_Get_Value.con",
	-- [0x] = "PEI_Identify.req",
	-- [0x] = "PEI_Identify.con",
	-- [0x] = "PEI_Switch.req",
	-- [0x] = "TM_Timer.ind",
	[0xFC] = "M_PropRead.req",
	[0xFB] = "M_PropRead.con",
	[0xF6] = "M_PropWrite.req",
	[0xF5] = "M_PropWrite.con",
	[0xF7] = "M_PropInfo.ind",
	[0xF8] = "M_FuncPropCommand.req",
	[0xF9] = "M_FuncPropStateRead.req",
	[0xFA] = "M_FuncPropCommand.con",
	[0xFA] = "M_FuncPropStateread.con",
	[0xF1] = "M_Reset.req",
	[0xF0] = "M_Reset.ind"
}

-- KNX HID Report Header
local f_report_id = ProtoField.uint8("usbhid.knx.reportid", "Report ID", base.HEX)
local f_sequence_number = ProtoField.uint8("usbhid.knx.sequence_number", "Sequence Number", base.DEC, vs_sequence_number, 0xf0)
local f_packet_type = ProtoField.uint8("usbhid.knx.packet_type", "Packet type", base.DEC, vs_packet_type, 0x0f)
local f_data_length = ProtoField.uint8("usbhid.knx.data_length", "Data length", base.DEC)
local f_report_body = ProtoField.bytes("usbhid.knx.knx_hid_report_body", "KNX HID Report Body")
-- KNX HID Report Body
-- KNX USB Transfer Protocol Header
local f_protocol_version = ProtoField.uint8("usbhid.knx.protocol_version", "Protocol version", base.HEX)
local f_header_length = ProtoField.uint8("usbhid.knx.header_length", "Header length", base.DEC)
local f_body_length = ProtoField.uint16("usbhid.knx.body_length", "Body length", base.DEC)
local f_protocol_id = ProtoField.uint8("usbhid.knx.protocol_id", "Protocol ID", base.HEX, vs_protocol_id)
local f_service_id = ProtoField.uint8("usbhid.knx.service_id", "Service ID", base.HEX, vs_service_id)
local f_supported_emi_type_emi1 = ProtoField.uint16("usbhid.knx.supported_emi_type_emi1", "EMI1", base.HEX, vs_emi_type_support, 0x0001)
local f_supported_emi_type_emi2 = ProtoField.uint16("usbhid.knx.supported_emi_type_emi2", "EMI2", base.HEX, vs_emi_type_support, 0x0002)
local f_supported_emi_type_cemi = ProtoField.uint16("usbhid.knx.supported_emi_type_cemi", "cEMI", base.HEX, vs_emi_type_support, 0x0004)
local f_emi_id = ProtoField.uint8("usbhid.knx.emi_id", "EMI ID", base.HEX, vs_emi_id)
local f_manufacturer_code = ProtoField.uint16("usbhid.knx.manufacturer_code", "Manufacturer code", base.HEX)
-- KNX USB Transfer Protocol Body
local f_emi1_message_code = ProtoField.uint8("usbhid.knx.emi1_message_code", "EMI1 message code", base.HEX, vs_emi1_message_code)
local f_emi2_message_code = ProtoField.uint8("usbhid.knx.emi2_message_code", "EMI2 message code", base.HEX, vs_emi2_message_code)
local f_cemi_message_code = ProtoField.uint8("usbhid.knx.cemi_message_code", "cEMI message code", base.HEX, vs_cemi_message_code)
local f_service_feature_id = ProtoField.uint8("usbhid.knx.service_feature_id", "Feature ID", base.HEX, vs_service_feature_id)
local f_emi_data = ProtoField.bytes("usbhid.knx.data", "Data (cEMI/EMI1/EMI2)")
local f_feature_data = ProtoField.bytes("usbhid.knx.data", "Feature data")

p_knx.fields = { f_report_id, f_sequence_number, f_packet_type, f_data_length, f_report_body,
                 f_protocol_version, f_header_length, f_body_length, f_protocol_id, f_service_id, f_supported_emi_type_emi1, f_supported_emi_type_emi2, f_supported_emi_type_cemi, f_emi_id, f_manufacturer_code,
                 f_emi1_message_code, f_emi2_message_code, f_cemi_message_code, f_service_feature_id, f_emi_data, f_feature_data 
               }

function p_knx.dissector(buf, pkt, tree)
	local PROTOCOL_ID_Bus_Access_Server_Feature_Service = 0x0F
	local EMI_ID_EMI1 = 0x01
	local EMI_ID_EMI2 = 0x02
	local EMI_ID_cEMI = 0x03
	local sequence_number = buf(1,1):uint()
	sequence_number = bit.rshift(sequence_number, 4)

	-- KNX HID Report Header
	local knx_hid_report_header_length = 3
	local knx_hid_data_tree = tree:add(p_knx, buf(0, buf:len()))
	local knx_hid_report_header_tree = knx_hid_data_tree:add(p_knx, buf(0, knx_hid_report_header_length))
	knx_hid_report_header_tree:set_text("KNX HID Report Header")
	knx_hid_report_header_tree:add(f_report_id, buf(0,1))
	knx_hid_report_header_tree:add(f_sequence_number, buf(1,1))
	knx_hid_report_header_tree:add(f_packet_type, buf(1,1))
	knx_hid_report_header_tree:add(f_data_length, buf(2,1))
	
	-- KNX HID Report Body
	local knx_hid_report_body_tree = knx_hid_data_tree:add(p_knx, buf(knx_hid_report_header_length, buf:len() - knx_hid_report_header_length))
	knx_hid_report_body_tree:set_text("KNX HID Report Body")
	
	-- KNX USB Transfer Protocol Header
	local knx_usb_transfer_protocol_header_length = 0
	local knx_usb_transfer_protocol_body_start = 0
	local protocol_id = buf(7, 1):uint()
	if sequence_number == 1 then
		knx_usb_transfer_protocol_header_length = 8
		knx_usb_transfer_protocol_body_start = knx_hid_report_header_length + knx_usb_transfer_protocol_header_length
		local knx_usb_transfer_protocol_header = knx_hid_report_body_tree:add(p_knx, buf(3, knx_usb_transfer_protocol_header_length))
		knx_usb_transfer_protocol_header:set_text("KNX USB Transfer Protocol Header")
		knx_usb_transfer_protocol_header:add(f_protocol_version, buf(3, 1))
		knx_usb_transfer_protocol_header:add(f_header_length, buf(4, 1))
		knx_usb_transfer_protocol_header:add(f_body_length, buf(5, 2))
		knx_usb_transfer_protocol_header:add(f_protocol_id, buf(7, 1))
		if protocol_id == PROTOCOL_ID_Bus_Access_Server_Feature_Service then
			knx_usb_transfer_protocol_header:add(f_service_id, buf(8, 1))
		else
			knx_usb_transfer_protocol_header:add(f_emi_id, buf(8, 1))
		end
		knx_usb_transfer_protocol_header:add(f_manufacturer_code, buf(9, 2))
	end
	-- KNX USB Transfer Protocol Body
	local knx_usb_transfer_protocol_body_data_length = buf:len() - knx_usb_transfer_protocol_body_start
	local knx_usb_transfer_protocol_body = knx_hid_report_body_tree:add(p_knx, buf(knx_usb_transfer_protocol_body_start, knx_usb_transfer_protocol_body_data_length))
	local emi_id = buf(8, 1):uint()
	knx_usb_transfer_protocol_body:set_text("KNX USB Transfer Protocol Body")
	if protocol_id == PROTOCOL_ID_Bus_Access_Server_Feature_Service then
		knx_usb_transfer_protocol_body:add(f_service_feature_id, buf(knx_usb_transfer_protocol_body_start, 1))
	else
		if emi_id == EMI_ID_EMI1 then
			knx_usb_transfer_protocol_body:add(f_emi1_message_code, buf(knx_usb_transfer_protocol_body_start, 1))
		elseif emi_id == EMI_ID_EMI2 then
			knx_usb_transfer_protocol_body:add(f_emi2_message_code, buf(knx_usb_transfer_protocol_body_start, 1))
		elseif emi_id == EMI_ID_cEMI then
			knx_usb_transfer_protocol_body:add(f_cemi_message_code, buf(knx_usb_transfer_protocol_body_start, 1))
		else
		end
	end
	-- dissect data
	if protocol_id == PROTOCOL_ID_Bus_Access_Server_Feature_Service then  -- 3.5.3 Level 2: bus access server, 3.5.3.1 Discovery and management
		local FEATURE_ID_Supported_EMI_type = 0x01
		local feature_id = buf(knx_usb_transfer_protocol_body_start, 1):uint()
		if feature_id == FEATURE_ID_Supported_EMI_type then
			local feature_data_length = 2
			knx_usb_transfer_protocol_body:add(f_supported_emi_type_emi1, buf(knx_usb_transfer_protocol_body_start + 1, feature_data_length))
			knx_usb_transfer_protocol_body:add(f_supported_emi_type_emi2, buf(knx_usb_transfer_protocol_body_start + 1, feature_data_length))
			knx_usb_transfer_protocol_body:add(f_supported_emi_type_cemi, buf(knx_usb_transfer_protocol_body_start + 1, feature_data_length))
			knx_usb_transfer_protocol_body:add(f_feature_data, buf(knx_usb_transfer_protocol_body_start + 1 + feature_data_length, knx_usb_transfer_protocol_body_data_length - 1 - feature_data_length))
		else
			knx_usb_transfer_protocol_body:add(f_feature_data, buf(knx_usb_transfer_protocol_body_start + 1, knx_usb_transfer_protocol_body_data_length - 1))
		end
	else
		knx_usb_transfer_protocol_body:add(f_emi_data, buf(knx_usb_transfer_protocol_body_start + 1, knx_usb_transfer_protocol_body_data_length - 1))
	end
end

-- tshark -G dissector-tables
-- ...
-- usb.bulk	USB bulk endpoint	FT_UINT8	BASE_DEC	USB	Decode As not supported
-- usb.control	USB control endpoint	FT_UINT8	BASE_DEC	USB	Decode As not supported
-- usb.descriptor	USB descriptor	FT_UINT8	BASE_DEC	USB	Decode As not supported
-- usb.device	USB device	FT_UINT32	BASE_HEX	USB	Decode As supported
-- usb.interrupt	USB interrupt endpoint	FT_UINT8	BASE_DEC	USB	Decode As not supported
-- usb.product	USB product	FT_UINT32	BASE_HEX	USB	Decode As supported
-- usb.protocol	USB protocol	FT_UINT32	BASE_HEX	USB	Decode As supported
-- ...

local usb_interrupt_table = DissectorTable.get("usb.interrupt")
usb_interrupt_table:add(0x0003, p_knx)  -- 0x0003 is the HID interface class
