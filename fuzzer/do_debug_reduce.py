# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This is a debug script.

from cascade.debug.debugreduce import debug_top
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed
from cascade.toleratebugs import tolerate_bug_for_eval_reduction

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    design_name = 'cva6'
    descriptor = (42750, design_name, 58, 29, True)

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    debug_top(*descriptor, 1, 0, 0x63d8)

else:
    raise Exception("This module must be at the toplevel.")
