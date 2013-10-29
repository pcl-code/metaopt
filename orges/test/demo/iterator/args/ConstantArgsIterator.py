"""Argument iterator that always returns the same arguments."""

from __future__ import division
from __future__ import print_function
from __future__ import with_statement


class ConstantArgumentBatchIterator(object):
    """Argument iterator that always returns the same arguments."""

    def __init__(self, arguments):
        """Sets the arguments this iterator shall always return."""
        self.arguments = arguments

    def __iter__(self):
        yield self

    def next(self):
        """Returns alwayst the arguments, that were given upon creation."""
        return self.arguments
