from .binaryinput import BinaryInput,BinaryInputState
from .device import Device
import yaml
import time
from enum import Enum
from .address import Address
from .devices import Devices

class SwitchTime(Enum):
    SHORT = 1
    LONG = 2

class Action():
    def __init__(self, xknx, config):
        self.xknx = xknx
        self.hook = config["hook"]
        self.target = config["target"]
        self.method = config["method"]
        if( "switch_time" in config ):
            if(config["switch_time"]=="long"):
                self.switch_time = SwitchTime.LONG
            elif(config["switch_time"]=="short"):
                self.switch_time = SwitchTime.SHORT

    def test_switch_time(self,switch_time):
        if not hasattr(self,"switch_time"):
            # no specific switch_time -> always true
            return True

        return (switch_time==self.switch_time)


    def test(self,state,switch_time):
        if((state==BinaryInputState.ON) and (self.hook == "on") and self.test_switch_time(switch_time)):
            return True

        if((state==BinaryInputState.OFF) and (self.hook == "off") and self.test_switch_time(switch_time)):
            return True
        return False

    def execute(self):
        self.xknx.devices.device_by_name(self.target).do(self.method)

    def __str__(self):
        return "<Action hook={0} target={1} method={2}>".format(self.hook,self.target,self.method)

class Switch(BinaryInput):
    def __init__(self, xknx, name, config):
        group_address = Address(config["group_address"])
        BinaryInput.__init__(self, xknx, name, group_address)
        self.group_address = group_address
        self.last_set = time.time();

        self.actions = []
        if "actions" in config:
            for action in config["actions"]:
                action = Action(xknx, action)
                self.actions.append(action)

    def get_switch_time(self):
        new_set_time = time.time()
        time_diff = new_set_time - self.last_set
        self.last_set = new_set_time
        if time_diff<0.2:
            return SwitchTime.SHORT
        return SwitchTime.LONG

    def process(self,telegram):
        BinaryInput.process(self,telegram)
        switch_time = self.get_switch_time()

        for action in self.actions:
            if(action.test(self.state,switch_time)):
                action.execute()

    def __str__(self):
        return "<Switch group_address={0}, name={1}>".format(self.group_address,self.name)
