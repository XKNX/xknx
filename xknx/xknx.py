import queue
from .devices import Devices
from .globals import Globals

class XKNX:

    def __init__(self):
        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = queue.Queue()


    def join(self):

        # Wait until all telegrams were processed
        self.telegrams.join()
