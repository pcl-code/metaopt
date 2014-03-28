"""
Invoker that invokes objective functions sequentially.
"""
from __future__ import division, print_function, with_statement

from multiprocessing import Process, Queue
from uuid import uuid4

from metaopt.core.call import call
from metaopt.invoker.base import BaseInvoker
from metaopt.util.stoppable import stoppable_method


class SimpleMultiprocessInvoker(BaseInvoker):
    """Invoker that invokes objective functions sequentially."""

    def __init__(self):
        super(SimpleMultiprocessInvoker, self).__init__()

        self._f = None
        self._param_spec = None
        self._return_spec = None

        self.result_queue = Queue()

        self.workers = []
        self.workers_data = {}

        self.running_worker_count = 0
        self.maximum_worker_count = 5

    @property
    def f(self):
        return self._f

    @f.setter
    def f(self, value):
        self._f = value

    @property
    def param_spec(self):
        return self._param_spec

    @param_spec.setter
    def param_spec(self, value):
        self._param_spec = value

    @property
    def return_spec(self):
        return self._return_spec

    @return_spec.setter
    def return_spec(self, value):
        self._return_spec = value

    @stoppable_method
    def invoke(self, caller, fargs, *vargs, **kwargs):
        if self.running_worker_count == self.maximum_worker_count:
            result = self.result_queue.get()

            if result:
                self.running_worker_count -= 1
                self.call_on_result(result)
            else:
                for worker in self.workers:
                    worker.terminate()

                return

        self.start_worker(caller, fargs, kwargs)

    def start_worker(self, caller, fargs, kwargs):
        worker_name = uuid4()
        worker_data = (caller, fargs, kwargs)

        worker = Process(target=self.worker_target,
            args=(worker_name, self.result_queue, fargs))

        self.running_worker_count += 1

        self.workers.append(worker)
        self.workers_data[worker_name] = worker_data

        worker.start()

    def worker_target(self, worker_name, result_queue, fargs):
        actual_result = call(self.f, fargs, self.param_spec, self.return_spec)

        result = WorkerResult()
        result.worker_name = worker_name
        result.actual_result = actual_result

        result_queue.put(result)

    def wait(self):
        while self.running_worker_count > 0:
            result = self.result_queue.get()

            if result:
                self.running_worker_count -= 1
                self.call_on_result(result)
            else:
                self.result_queue.close()

                for worker in self.workers:
                    worker.terminate()

                break

    def call_on_result(self, result):
        caller, worker_fargs, worker_kwargs = \
            self.workers_data[result.worker_name]

        actual_result = result.actual_result
        caller.on_result(actual_result, worker_fargs, **worker_kwargs)

    def stop(self):
        self.result_queue.put(None)


class WorkerResult(object):
    def __init__(self):
        self._worker_name = None
        self._actual_result = None

    @property
    def worker_name(self):
        return self._worker_name

    @worker_name.setter
    def worker_name(self, value):
        self._worker_name = value

    @property
    def actual_result(self):
        return self._actual_result

    @actual_result.setter
    def actual_result(self, value):
        self._actual_result = value