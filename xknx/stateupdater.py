import threading
import time

class StateUpdater(threading.Thread):

    def __init__(self, xknx, timeout):
        self.xknx = xknx
        self.timeout = timeout
        threading.Thread.__init__(self)


    def run(self):
        time.sleep(self.timeout)
        print("Starting Update Thread")
        while True:
            self.request_states()
            time.sleep(self.timeout)

    def request_states(self):
        for device in self.xknx.devices.devices:
            device.request_state()

    @staticmethod
    def start_thread(xknx, timeout = 60):
        t = StateUpdater(xknx, timeout)
        t.setDaemon(True)
        t.start()

