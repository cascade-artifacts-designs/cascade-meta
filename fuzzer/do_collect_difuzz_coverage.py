# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script collects coverage of DifuzzRTL.

from benchmarking.collectdifuzzcoverage import collectdifuzzcoverage, plot_difuzzrtl_coverage

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    collectdifuzzcoverage()
    plot_difuzzrtl_coverage()

else:
    raise Exception("This module must be at the toplevel.")
