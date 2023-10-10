# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script reduces a single program.

# sys.argv[1]: design name
# sys.argv[2]: num of cores allocated to fuzzing
# sys.argv[3]: offset for seed (to avoid running the fuzzing on the same instances over again)

from cascade.reduce import reduce_program
from cascade.toleratebugs import tolerate_bug_for_eval_reduction
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    design_name = 'cva6'
    descriptor = (489442, design_name, 6, 48, False)

    # # Optional
    # tolerate_bug_for_eval_reduction(design_name)

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    reduce_program(*descriptor, True, check_pc_spike_again=True)

else:
    raise Exception("This module must be at the toplevel.")
