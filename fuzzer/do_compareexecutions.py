# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script compares the execution of two ELFs.
# This is typically useful in development/debug to ensure that AIPS does not break the program control flow.

from cascade.debug.compareexecutions import compare_executions
from common.spike import calibrate_spikespeed

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    design_name = 'vexriscv'
    numinstrs = 100

    elfpath1 = '/scratch/flsolt/data/python-tmp/spikedoublecheck399003_vexriscv_51_27.elf'
    elfpath2 = '/scratch/flsolt/data/python-tmp/spikereduce399003_vexriscv_51_27_12_57_1_0.elf'

    calibrate_spikespeed()

    compare_executions(design_name, elfpath1, elfpath2, numinstrs)

else:
    raise Exception("This module must be at the toplevel.")
