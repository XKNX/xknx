import threading
import time

class StateUpdater(threading.Thread):

    def __init__(self,
                 xknx,
                 timeout,
                 start_timeout=15,
                 sleep_during_devices=0.2):
        self.xknx = xknx
        self.timeout = timeout
        self.start_timeout = start_timeout
        self.sleep_during_devices = sleep_during_devices
        threading.Thread.__init__(self)


    def run(self):
        time.sleep(self.start_timeout)
        print("Starting Update Thread")
        while True:
            self.sync_states()
            time.sleep(self.timeout)

    def sync_states(self):
        for device in self.xknx.devices.devices:
            device.sync_state()
            time.sleep(self.sleep_during_devices)

    @staticmethod
    def start_thread(xknx, timeout=60):
        stateupdater = StateUpdater(xknx, timeout)
        stateupdater.setDaemon(True)
        stateupdater.start()
