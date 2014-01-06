"""
Tests for the MutliProcess utilities.
"""

from multiprocessing.queues import Queue

import nose

from orges.invoker.multiprocess_util import WorkerProvider


def test_WorkerProvider_acts_as_singleton():
    wp0, wp1 = WorkerProvider(), WorkerProvider()

    assert wp0 is wp1


def test_WorkerProvider_circle():
    queue_tasks = Queue()
    queue_status = Queue()
    queue_results = Queue()

    worker_count = 2

    worker_provider = WorkerProvider()

    # once
    workers = worker_provider.provision(number_of_workers=worker_count,
                                        queue_tasks=queue_tasks,
                                        queue_results=queue_results,
                                        queue_status=queue_status)
    for worker in workers:
        worker.cancel()

    # and once more
    workers = worker_provider.provision(number_of_workers=worker_count,
                                        queue_tasks=queue_tasks,
                                        queue_results=queue_results,
                                        queue_status=queue_status)
    for worker in workers:
        worker.cancel()

if __name__ == '__main__':
    nose.runmodule()
