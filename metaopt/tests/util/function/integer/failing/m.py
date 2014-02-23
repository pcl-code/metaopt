"""
A failing function with integer parameters for testing purposes.
"""
from __future__ import division, print_function, with_statement

from metaopt.core import param


@param.int("a", interval=(1, 10))
@param.int("b", interval=(1, 10))
def f(a, b):
    """Function that fails, rising an exception."""
    del a, b
    raise Exception()