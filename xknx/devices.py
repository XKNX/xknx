import time
import threading

class CouldNotResolveAddress(Exception):
    def __init__(self, group_address):
        self.group_address = group_address

    def __str__(self):
        return "CouldNotResolveAddress <name={0}>".format(self.group_address)

class CouldNotResolveName(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "CouldNotResolveName <name={0}>".format(self.name)


class Devices:

    def __init__(self):
        print("Initialization of Devices")
        self.devices = []

    def device_by_group_address( self, group_address):
        for device in self.devices:
            if device.has_group_address(group_address):
                return device
        raise CouldNotResolveAddress(group_address)

    def device_by_name( self, name):
        for device in self.devices:
            if device.name == name:
                return device
        raise CouldNotResolveName(name)

#    def get_outlets( self ):
#        outlets = []
#        for device in self.devices:
#            if type(device) == Outlet:
#                outlets.append(device)
#        return outlets

    def get_devices( self ):
        return self.devices

    def update_thread_start(self,timeout):
        def worker(timeout):
            while True:
                devices = devices_.get_devices()
                for device in self.devices:
                    device.request_state()
                time.sleep(timeout)
        t = threading.Thread(target=worker, args=(timeout,))
        t.start();

devices_ = Devices()
