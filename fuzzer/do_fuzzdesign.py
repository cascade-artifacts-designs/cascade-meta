# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script executes the fuzzer on a given design to find faulting programs.

# sys.argv[1]: design name
# sys.argv[2]: num of cores allocated to fuzzing
# sys.argv[3]: offset for seed (to avoid running the fuzzing on the same instances over again)
# sys.argv[4]: authorize privileges (by default 1)
# sys.argv[5]: tolerate some bug (by default 0)

from top.fuzzdesign import fuzzdesign
from cascade.toleratebugs import tolerate_bug_for_eval_reduction
from common.designcfgs import get_design_cascade_path

import os
import sys

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    if len(sys.argv) < 4:
        raise Exception("Usage: python3 do_fuzzdesign.py <design_name> <num_cores> <seed_offset> <authorize_privileges> <tolerate_some_bug>")

    print(get_design_cascade_path(sys.argv[1]))

    if len(sys.argv) > 4:
        authorize_privileges = int(sys.argv[4])
    else:
        authorize_privileges = 1

    if len(sys.argv) > 5:
        tolerate_some_bug = int(sys.argv[5])
    else:
        tolerate_some_bug = 0

    if tolerate_some_bug:
        tolerate_bug_for_eval_reduction(sys.argv[1])

    fuzzdesign(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), authorize_privileges)

else:
    raise Exception("This module must be at the toplevel.")
