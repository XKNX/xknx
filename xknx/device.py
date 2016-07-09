
class Device:
    def __init__(self):
        pass        

    def request_state(self):
        pass

    def process(self,telegram):
        pass

    def get_name(self):
        return "undefined"

    def do(self,action):
        print("{0} {1}".format( self.get_name(), action))
        pass
