# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script measures the program construction relative performance.

from benchmarking.fuzzperf import benchmark_collect_construction_performance, plot_construction_performance

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_cores = max(int(os.environ['CASCADE_JOBS']) // 2, 1)

    benchmark_collect_construction_performance(num_cores)
    plot_construction_performance()

else:
    raise Exception("This module must be at the toplevel.")
