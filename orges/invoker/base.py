"""
Abstract invoker defining the API of invoker implementations.
"""

import abc  # Abstract Base Class


class Invoker(object):
    """Abstract invoker managing calls to ."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, resources, caller):
        pass

    @abc.abstractmethod
    def get_subinvoker(self, resources):
        """Returns a subinvoker using the given amout of resources of self."""
        pass

    @abc.abstractmethod
    def invoke(self, f, fargs, **kwargs):
        """Calls back to self.caller.on_result() for call(f, fargs)."""
        pass

    @abc.abstractmethod
    def wait(self):
        """Blocks till all invoke, on_error or on_result calls are done."""
        pass

class Caller(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def on_result(return_value, fargs, **kwargs):
        pass

    @abc.abstractmethod
    def on_error(fargs, **kwargs):
        pass