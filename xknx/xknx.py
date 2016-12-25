import queue
from .devices import Devices

class XKNX:
    def __init__(self):

        self.devices = Devices()

        self.out_queue = queue.Queue()


