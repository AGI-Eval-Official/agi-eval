from agieval.common.logger import log_error


class EvalException(Exception):
    """
    Base exception class, mainly encapsulates the logic of printing logs
    """

    def __init__(self,  msg):
        super().__init__(self)
        log_error(f"Exception triggered: {self.__class__.__name__} message: {msg}")
        self.error_msg = msg

    def __str__(self):
        return self.error_msg

class PluginNotExistException(EvalException):
    pass
class NotStageImplementException(EvalException):
    pass

class ServerNotResponseException(EvalException):
    pass

class FlowConfigParseException(EvalException):
    pass