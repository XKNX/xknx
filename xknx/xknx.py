import queue
from .devices import Devices
from .globals import Globals

class XKNX:
    def __init__(self):

        self.globals = Globals()

        self.devices = Devices()

        self.out_queue = queue.Queue()

        
