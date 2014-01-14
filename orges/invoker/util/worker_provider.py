"""
Various utilities for the multiprocess invoker.
"""
from __future__ import division, print_function, with_statement

import sys
import uuid
import threading
import traceback
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from multiprocessing.process import Process

from orges.core.args import call
from orges.util.singleton import Singleton
from orges.util.stoppable import Stoppable, stopping_method, stoppable_method
from orges.invoker.util.determine_worker_count import determine_worker_count


class WorkerProcessProvider(Singleton):
    """
    Keeps track of as many worker processes as there are CPUs.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._worker_count = determine_worker_count()  # use up to all CPUs
        self._workers = []

    def provision(self, queue_tasks, queue_results, queue_status,
                  number_of_workers=1):
        """
        Provisions a given number worker processes for future use.

        :rtype: A list of WorkerHandles if number_of_workers > 1,
                otherwise a single WorkerHandle.
        """
        with self._lock:
            if self._worker_count < (len(self._workers) + number_of_workers):
                raise IndexError("Cannot provision so many worker processes.")

            worker_processes = []
            for _ in range(number_of_workers):
                worker_id = uuid.uuid4()
                worker_process = WorkerProcess(worker_id=worker_id,
                                               queue_tasks=queue_tasks,
                                               queue_results=queue_results,
                                               queue_status=queue_status)
                worker_process.daemon = True  # workers don't spawn processes
                worker_process.start()
                worker_processes.append(worker_process)

            self._workers.extend(worker_processes)
        if number_of_workers > 1:
            return [WorkerProcessHandle(worker_process) for worker_process in
                    worker_processes]
        else:
            return WorkerProcessHandle(worker_processes[0])

    def release(self, worker_process):
        """Releases a worker process from the work force."""
        with self._lock:
            # send manually constructed empty result
            result = Result(worker_id=worker_process.worker_id, function=None,
                            args=None, vargs=None, kwargs=None,
                            task_id=worker_process.current_task_id,
                            value=None)
            worker_process.queue_results.put(result)

            # send kill signal and wait for the process to die
            worker_process.terminate()
            worker_process.join()

            self._workers.remove(worker_process)


# data structure for results generated by the workers
Task = namedtuple("Task", ["task_id", "function", "args", "vargs", "kwargs"])

# data structure for results generated by the workers
Status = namedtuple("Status", ["task_id", "function", "args", "vargs",
                               "kwargs", "worker_id"])

# data structure for results generated by the workers
Result = namedtuple("Result", ["task_id", "function", "args", "vargs",
                               "kwargs", "worker_id", "value"])

# data structure for results generated by the workers
Error = namedtuple("Error", ["task_id", "function", "args", "vargs",
                             "kwargs", "worker_id", "value"])


class BaseWorker(object):
    """Interface definition for worker implementations."""

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def worker_id(self):
        """Property for the _worker_id attribute."""
        pass


class Worker(BaseWorker):
    """Minimal worker implementation."""

    def __init__(self):
        self._worker_id = None
        super(Worker, self).__init__()

    @property
    def worker_id(self):
        return self._worker_id


class WorkerProcess(Process, Worker):
    """Calls functions with arguments, both given by a queue."""

    def __init__(self, worker_id, queue_results, queue_status,
                 queue_tasks):
        self._worker_id = worker_id
        self._queue_results = queue_results
        self._queue_status = queue_status
        self._queue_tasks = queue_tasks
        self._current_task_id = None
        super(WorkerProcess, self).__init__()

    @property
    def worker_id(self):
        """Property for the worker_id attribute of this class."""
        return self._worker_id

    @property
    def queue_tasks(self):
        """Property for the tasks attribute of this class."""
        return self._queue_tasks

    @property
    def queue_status(self):
        """Property for the results attribute of this class."""
        return self._queue_status

    @property
    def queue_results(self):
        """Property for the results attribute of this class."""
        return self._queue_results

    @property
    def busy(self):
        """Property for the results attribute of this class."""
        return self._current_task_id is not None

    @property
    def current_task_id(self):
        """Property for the results attribute of this class."""
        return self._current_task_id

    def run(self):
        """Makes this worker execute all tasks incoming from the task queue."""
        # Get tasks from the queue and trigger their execution
        while True:
            try:
                self._execute(self.queue_tasks.get())
            except EOFError:
                return

    def _execute(self, task):
        """Executes the given task."""
        # send sentinel to propagate the end of the task queue
        if task is None:
            self._queue_results.put(None)
            return

        # announce start of work
        self._current_task_id = task.task_id
        self._queue_status.put(Status(task_id=self._current_task_id,
                                      worker_id=self._worker_id,
                                      function=task.function,
                                      args=task.args, vargs=task.vargs,
                                      kwargs=task.kwargs))

        # import function given by qualified package name
        function = __import__(task.function, globals(), locals(), ['function'],
                              0).f
        # Note that the following is equivalent:
        #     from MyPackage.MyModule import f as function
        # Also note this always imports the function "f" as "function".

        # make the actual call
        try:
            value = call(function, task.args)
            self._queue_results.put(Result(task_id=self._current_task_id,
                                          worker_id=self._worker_id,
                                          function=task.function,
                                          args=task.args, value=value,
                                          vargs=task.vargs,
                                          kwargs=task.kwargs))
        except Exception:
            value = traceback.format_exc()
            # TODO maybe use a proper error log?
            print("WARNING: ", value, end='\n', file=sys.stderr)
            self._queue_results.put(Error(task_id=self._current_task_id,
                                          worker_id=self._worker_id,
                                          function=task.function,
                                          args=task.args, value=value,
                                          vargs=task.vargs,
                                          kwargs=task.kwargs))

        # announce finish of work
        self._current_task_id = None


class WorkerHandle(Stoppable):
    """Interface definition for worker handle implementations."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        super(WorkerHandle, self).__init__()

    @stoppable_method
    @stopping_method
    def stop(self):
        """Stops this worker."""
        pass


class WorkerProcessHandle(WorkerHandle):
    """A means to stop a worker."""

    def __init__(self, worker_process):
        super(WorkerProcessHandle, self).__init__()
        self._worker_process = worker_process

    @property
    def worker_id(self):
        """Property for the worker_id attribute of this handle's worker."""
        return self._worker_process.worker_id

    @property
    def current_task_id(self):
        """Property for the current_task_id of this handle's worker."""
        return self._worker_process.current_task_id

    @property
    def busy(self):
        """Property for the busy attribute of this handle's worker."""
        return self._worker_process.busy

    @stoppable_method
    @stopping_method
    def stop(self):
        """Stops this worker."""
        WorkerProcessProvider().release(self._worker_process)
