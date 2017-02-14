
class Device:
    def __init__(self, xknx, name):
        self.xknx = xknx
        self.after_update_callback = None
        self.name = name

    def after_update(self):
        if self.after_update_callback is not None:
            #pylint: disable=not-callable
            self.after_update_callback(self)

    def sync_state(self):
        pass

    def process(self, telegram):
        pass

    def get_name(self):
        return self.name

    # pylint: disable=invalid-name
    def do(self, action):
        pass
