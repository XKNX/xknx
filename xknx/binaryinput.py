
class CouldNotParseSwitchTelegram(Exception):
    pass

class BinaryInput:
    def __init__(self, telegram):
        if len( telegram.payload ) != 1:
            raise CouldNotParseSwitchTelegram()    

        self.telegram = telegram

    def is_on(self):
        return self.telegram.payload[0] == 0x81

    def is_off(self):
        return self.telegram.payload[0] == 0x80
