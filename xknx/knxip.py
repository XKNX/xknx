import time
from .colors import Colors
from .address import Address,AddressType
from .telegram import Telegram
from enum import Enum

class CouldNotParseCEMI(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotParseCEMI"

class CEMIMessageCode(Enum):
    """
    FROM NETWORK LAYER TO DATA LINK LAYER
    Data Link Layer  Message
    Primitive    Code
    ---------------  -------
    L_Raw.req          0x10
    L_Data.req         0x11  Data Service. Primitive used for transmitting a data frame
    L_Poll_Data.req    0x13  Poll Data Service
 
    FROM DATA LINK LAYER TO NETWORK LAYER
    Data Link Layer  Message
    Primitive    Code
    ---------------  -------
    L_Poll_Data.con    0x25  Poll Data Service
    L_Data.ind         0x29  Data Service. Primitive used for receiving a data frame
    L_Busmon.ind       0x2B  Bus Monitor Service
    L_Raw.ind          0x2D
    L_Data.con         0x2E  Data Service. Primitive used for local confirmation that a frame was sent
                             (does not indicate a successful receive though)
    L_Raw.con          0x2F		
    """
    L_RAW_REQ       =   0x10
    L_Data_REQ      =   0x11
    L_POLL_DATA_REQ =   0x13
    L_POLL_DATA_CON =   0x25
    L_DATA_IND      =   0x29
    L_BUSMON_IND    =   0x2B
    L_RAW_IND       =   0x2D
    L_DATA_CON      =   0x2E
    L_RAW_CON       =   0x2F

class APCI_COMMAND(Enum):
    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3
    UNKNOWN = 0xff

class ServiceType(Enum):
    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0111
    TUNNELING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531
    UNKNOWN = 0x0000

class CEMIFrame():
    """Representation of a CEMI Frame."""

    def __init__(self, cemi = None):      
        """CEMIFrame __init__ object."""
        self.code = 0
        self.ctl1 = 0
        self.ctl2 = 0
        self.cmd = APCI_COMMAND.UNKNOWN
        self.src_addr = Address()
        self.dst_addr = Address()
        self.tpci_apci = 0
        self.mpdu_len = 0
        self.data = [0]
        if cemi != None:
            self._from_cemi_frame(cemi)


    def _init_group(self, dst_addr = Address()):
        """CEMIMessage _init_group"""
        """
		Control Field 1
         Bit  |
		------+---------------------------------------------------------------
          7   | Frame Type  - 0x0 for extended frame
              |               0x1 for standard frame
		------+---------------------------------------------------------------
          6   | Reserved
              |
		------+---------------------------------------------------------------
          5   | Repeat Flag - 0x0 repeat frame on medium in case of an error
              |               0x1 do not repeat
		------+---------------------------------------------------------------
          4   | System Broadcast - 0x0 system broadcast
              |                    0x1 broadcast
		------+---------------------------------------------------------------
          3   | Priority    - 0x0 system
              |               0x1 normal
		------+               0x2 urgent
          2   |               0x3 low
              |
		------+---------------------------------------------------------------
          1   | Acknowledge Request - 0x0 no ACK requested
              | (L_Data.req)          0x1 ACK requested
		------+---------------------------------------------------------------
          0   | Confirm      - 0x0 no error
              | (L_Data.con) - 0x1 error
		------+---------------------------------------------------------------
		 
		Control Field 2
		 
		 Bit  |
		------+---------------------------------------------------------------
          7   | Destination Address Type - 0x0 individual address
              |                          - 0x1 group address
		------+---------------------------------------------------------------
         6-4  | Hop Count (0-7)
		------+---------------------------------------------------------------
         3-0  | Extended Frame Format - 0x0 standard frame
		------+---------------------------------------------------------------
		"""
        # Message Code 
        self.code = CEMIMessageCode.L_Data_REQ
        # Control Field 1 -> frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0, confirm-flag 0
        self.ctl1 = 0xbc
		# Control Field 2 -> dst_addr type 1, hop count 6, extended frame format
        self.ctl2 = 0xe0  
		
        self.src_addr = Address()
        self.dst_addr = dst_addr
			
    def _init_group_read(self, dst_addr):
        """CEMIMessage _init_group_read"""
        """Initialize group read """
        self.init_group(dst_addr)
		# ACPI Value		
        _set_tpci_apci_command_value(APCI_COMMAND.GROUP_READ)
		# DATA
        self.data = [0]
		
    def _init_group_write(self, dst_addr = Address(), data=None):
        """CEMIMessage _init_group_write"""
        """Initialize group write """
        self.init_group(dst_addr)
        # ACPI Value		
        _set_tpci_apci_command_value(APCI_COMMAND.GROUP_WRITE)
		# DATA
        if data is None:
            self.data = [0]
        else:
            self.data = data
		
    def _from_cemi_frame(self, cemi):

        """Create a new CEMIFrame initialized from the given CEMI data."""
        # TODO: check that length matches
        self.code = CEMIMessageCode(cemi[0])
        offset = cemi[1]

        self.ctl1 = cemi[2]
        self.ctl2 = cemi[3]

        self.src_addr = Address((cemi[4 + offset], cemi[5 + offset]), AddressType.PHYSICAL)
        self.dst_addr = Address((cemi[6 + offset], cemi[7 + offset]), AddressType.GROUP)

        self.mpdu_len = cemi[8 + offset]

        self.tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = self.tpci_apci & 0x3ff

        #detect acpi command
        self.cmd = self._detect_acpi_command(apci)

        apdu = cemi[10 + offset:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseCEMI(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))
        #check Date in ACPI Byte
        if len(apdu) == 1:
            self.data = [apci & 0x2f]
        else:
            self.data = cemi[11 + offset:]


    def _to_cemi_frame(self):
        """Convert the CEMI frame object to its byte representation. Not testet"""
        cemi = [self.code.value, 0x00, self.ctl1, self.ctl2,
                self.src_addr.byte1(), self.src_addr.byte2(),
                self.dst_addr.byte1(), self.dst_addr.byte2(),
               ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            cemi.extend([1, (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            cemi.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                         0xff, (self.tpci_apci >> 0) & 0xff])
            cemi.extend(self.data)

        return cemi

    @staticmethod
    def _detect_acpi_command(apci):
        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if apci & 0x080:
            return APCI_COMMAND.GROUP_WRITE
        elif apci == 0:
            return APCI_COMMAND.GROUP_READ
        elif apci & 0x40:
            return APCI_COMMAND.GROUP_RESPONSE
        else:
            return APCI_COMMAND.UNKNOWN
			
    @staticmethod			
    def _set_tpci_apci_command_value(command):
        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if command == APCI_COMMAND.GROUP_WRITE :
            self.cmd = APCI_COMMAND.GROUP_WRITE
            self.tpci_apci =  0x00 * 256 + 0x80
        elif command == APCI_COMMAND.GROUP_READ :
            self.cmd = APCI_COMMAND.GROUP_READ
            self.tpci_apci =   0x00
        else:
            self.cmd = APCI_COMMAND.UNKNOWN
            self.tpci_apci =   0x00

    def __str__(self):
            return "<CEMIFrame SourceAddress={0}, DestinationAddress={1}, Command={2}, Data={3}>".format( self.src_addr, self.dst_addr, self.cmd, self.data)


class KNXIPFrame:
    """Abstraction for KNX telegrams"""


    def __init__(self):
        """Initialize object."""
        self.headerLength = 0
        self.protocolVersion = 0
        self.serviceTypeIdent = ServiceType.UNKNOWN
        self.b4Reserve = 0
        self.totalLength = 0
        self.cemi = CEMIFrame()

        self.payload = bytearray()

    @property
    def sender(self):
        """Return source address"""
        return self.cemi.src_addr

    @sender.setter
    def sender(self, sender):
        self.cemi.src_addr = Address(sender)

    @property
    def group_address(self):
        """Return destination address"""
        return self.cemi.dst_addr

    @group_address.setter
    def group_address(self, group_address):
        self.cemi.dst_addr = Address(group_address)

    @property
    def telegram(self):
        telegram = Telegram()
        telegram.payload = self.payload
        telegram.group_address = self.group_address
        return telegram

    @telegram.setter
    def telegram(self,telegram):
        self.group_address = telegram.group_address
        self.payload = telegram.payload

    def _from_telegram(self, data):

        print(data[0:6])

        self.headerLength = data[0]
        self.protocolVersion = data[1]
        self.serviceTypeIdent = ServiceType(data[2] * 256 + data[3])
        self.b4Reserve = data[4]
        self.totalLength = data[5]
        self.cemi = CEMIFrame(data[6:])

    def read(self, data):

        self.print_data(data)

        self._from_telegram(data)

        print(self)

        len_payload = data[14]
        for x in range(0, len_payload):
            self.payload.append(data[16+x])

    def __str__(self):
        return "<KNXIPFrame HeaderLength={0}, ProtocolVersion={1}, ServiceType={2}, Reserve={3}, TotalLength={4} {5}>".format(self.headerLength, self.protocolVersion, self.serviceTypeIdent, self.b4Reserve, self.totalLength, self.cemi)

    def print_data(self, data):
        i = 0;
        for b in data:
            if i in [10,11]:
                print (Colors.OKBLUE, end="")
            if i in [0,12,13]:
                print (Colors.WARNING, end="")
            if i == 14 or i >= 16:
                print (Colors.BOLD, end="")
            print (format(b, '02x'), end="")
            print (Colors.ENDC+" ", end="")
            i=i+1
        print ("")

    def dump(self):
        #print('Control: {:08b}'.format(self.control))
        print('Sender: {0}'.format( self.sender.__str__()))
        print('Group:   {0}'.format(self.group_address))
        #print('Payload: {:#02x}'.format(self.payload))

        for b in self.payload:
            print('Payload: {:#02x}'.format(b))

    def str(self):
        data = bytearray()

        # See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/tutor_documentation/08_IP%20Communication_E0510a.pdf

        # KNX Header
        data.append(0x06)

        #Protocol version
        data.append(0x10)

        # Service identifier
        # Known values:
        #
        #   0x04 0x20 -> KNXnet/IP Tunnelling: TUNNELLING_REQUEST
        #   0x04 0x21 -> KNXnet/IP Tunnelling: TUNNELLING_ACK
        #   0x05 0x30 KNXnet/IP Routing
        #
        data.append(0x05) # IP Routing 0530
        data.append(0x30)

        # Total length
        total_length = 16 + len(self.payload)
        data.append((total_length>>8)&255)
        data.append(total_length&255)

        # Message code
        data.append(0x29)

        # Length of additional information (for future usage)
        data.append(0x00)

        # Control field
        data.append(0xbc) #b4 ?

        # Type of target address
        data.append(0xd0)

        # Sender address
        data.append( self.sender.byte1() )
        data.append( self.sender.byte2() )

        # Target address
        data.append( self.group_address.byte1() )
        data.append( self.group_address.byte2() )

        # Payload length
        data.append(len(self.payload))

        # Zero
        data.append(0x00)

        # Payload
        for b in self.payload:
            data.append(b)

        return data
