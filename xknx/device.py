
class Device:
    def __init__(self, xknx, name):
        self.xknx = xknx
        self.after_update_callback = lambda x: None
        self.name = name

    def sync_state(self):
        pass

    def process(self,telegram):
        pass

    def get_name(self):
        return self.name

    def do(self,action):
        pass
