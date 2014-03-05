"""
Models for data exchange between processes.
"""
from __future__ import division, print_function, with_statement

from collections import namedtuple

# data structure for errors generated by the workers
Error = namedtuple("Error", ["worker_id", "task_id",
                             "function", "args", "value",
                             "kwargs"])

# data structure for results generated by the workers
Result = namedtuple("Result", ["worker_id", "task_id",
                               "function", "args", "value",
                               "kwargs"])

# data structure for declaring the start of an execution by the workers
Start = namedtuple("Start", ["worker_id", "task_id",
                             "function", "args",
                             "kwargs"])

# data structure for tasks given to the workers
Task = namedtuple("Task", ["id",
                           "function", "args",
                           "param_spec", "return_spec",
                           "kwargs"])
