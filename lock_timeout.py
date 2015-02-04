__author__ = 'http://stackoverflow.com/users/279089/robbles'

# yes, I nicked this from stackoverflow.com

import threading
from contextlib import contextmanager


class TimeoutLock(object):
    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self, blocking=True, timeout=-1):
        return self._lock.acquire(blocking, timeout)

    @contextmanager
    def acquire(self, timeout):
        # result = self._lock.acquire(timeout=timeout)
        # TODO: implement timeouts in python 2
        result = self._lock.acquire()
        yield result
        if result:
            self._lock.release()

    def release(self):
        self._lock.release()

# # Usage:
# lock = TimeoutLock()
#
# with lock.acquire_timeout(3) as result:
#     if result:
#         print('got the lock')
#         # do something ....
#     else:
#         print('timeout: lock not available')
#         # do something else ...
