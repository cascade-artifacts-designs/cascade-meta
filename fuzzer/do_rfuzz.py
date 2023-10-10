# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script runs RFUZZ.

# sys.argv[1]: design name
# sys.argv[2]: num of cores allocated to fuzzing
# sys.argv[3]: offset for seed (to avoid running the fuzzing on the same instances over again)

from rfuzz.collectrfuzz import collect_coverage_rfuzz, _measure_coverage_rfuzz_worker
from rfuzz.collectactiverfuzz import collect_active_coverage_rfuzz
from rfuzz.plot import plot_rfuzz
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

import itertools
import multiprocessing as mp
import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    TIMEOUT_SECONDS = 120

    calibrate_spikespeed()

    num_cores_for_passive_rfuzz = int(os.getenv('CASCADE_JOBS', 160))

    design_names_for_rfuzz = [
        'vexriscv',
        'kronos',
        'picorv32',
        'rocket',
        'boom',
        # 'cva6', Ignored for now as indicated in the paper, until Y1 (CVE-2023-34884) is fixed.
    ]

    num_elfs_passive_rfuzz = {
        'vexriscv': 300,
        'kronos': 2500,
        'picorv32': 2500,
        'rocket': 300,
        'boom': 100,
        # 'cva6': 1800,
    }

    # Passive RFUZZ
    design_passive_rfuzz_results = dict()
    for design_name in design_names_for_rfuzz:
        profile_get_medeleg_mask(design_name)
        design_passive_rfuzz_results[design_name] = collect_coverage_rfuzz(design_name, num_cores_for_passive_rfuzz, num_elfs_passive_rfuzz[design_name])
        print(f"Passive RFUZZ for design {design_name}:", design_passive_rfuzz_results[design_name])

    # Active RFUZZ
    with mp.Pool(mp.cpu_count()) as p:
        ret = p.starmap(collect_active_coverage_rfuzz, zip(design_names_for_rfuzz, itertools.repeat(TIMEOUT_SECONDS)))
    design_active_rfuzz_results = dict()
    for val_id, val in enumerate(ret):
        design_active_rfuzz_results[design_names_for_rfuzz[val_id]] = val
        print(f"Active RFUZZ for design {design_names_for_rfuzz[val_id]}:", design_active_rfuzz_results[design_names_for_rfuzz[val_id]])

    plot_rfuzz(design_active_rfuzz_results, design_passive_rfuzz_results)
else:
    raise Exception("This module must be at the toplevel.")
