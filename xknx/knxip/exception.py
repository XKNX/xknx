class CouldNotParseKNXIP(Exception):
    def __init__(self, description=""):
        super(CouldNotParseKNXIP, self).__init__("Could not parse KNXIP")
        self.description = description
    def __str__(self):
        return "<CouldNotParseKNXIP description='{0}'>" \
            .format(self.description)

class ConversionException(Exception):
    def __init__(self, description=""):
        super(ConversionException, self).__init__("Conversion Exception")
        self.description = description
    def __str__(self):
        return "<ConversionException description='{0}'>" \
            .format(self.description)
