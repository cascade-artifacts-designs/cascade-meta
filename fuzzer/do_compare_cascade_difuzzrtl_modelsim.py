# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script measures the simulator coverage of Cascade and DifuzzRTL.

from modelsim.comparedifuzzmodelsim import collect_coverage_modelsim_nomerge, merge_coverage_modelsim
from modelsim.plot import plot_coverage_global

import multiprocessing as mp
import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_workers = max(int(os.getenv('CASCADE_JOBS', 160)) // 4, 1)
    TARGET_NUMINSTRS = 1_100_000
    PLOT_NUMINSTRS = 1_000_000
    NUM_SERIES = 10

    # Cascade

    # Generate enough ELFs
    for series_id in range(NUM_SERIES):
        collect_coverage_modelsim_nomerge(False, series_id, 'rocket', num_workers, TARGET_NUMINSTRS, None)

    # DifuzzRTL

    # Generate the DifuzzRTL ELFs
    collect_coverage_modelsim_nomerge(True, 0, 'rocket', num_workers, TARGET_NUMINSTRS, None)

    # Run merging the coverage
    workloads = [(True, 0, TARGET_NUMINSTRS)]
    for series_id in range(NUM_SERIES):
        workloads.append((False, series_id, TARGET_NUMINSTRS))
    with mp.Pool(min(NUM_SERIES+1, num_workers)) as pool:
        pool.starmap(merge_coverage_modelsim, workloads)
    
    # Plot the coverage
    plot_coverage_global(NUM_SERIES, PLOT_NUMINSTRS, TARGET_NUMINSTRS)

else:
    raise Exception("This module must be at the toplevel.")
