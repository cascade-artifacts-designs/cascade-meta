# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from functools import wraps
from multiprocessing.context import TimeoutError
from multiprocessing.pool import ThreadPool

def timeout(seconds):
    def timeout_wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                pool = ThreadPool(processes=1)
                result = pool.apply_async(func, args, kwargs)
                return result.get(timeout=seconds)
            except TimeoutError:
                return None
        return wrapped
    return timeout_wrapper
